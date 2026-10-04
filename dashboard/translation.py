"""Free anonymous translation with a persistent, strict character allowance."""
import datetime as dt
import hashlib
import json
import re
import time
import os
from urllib.parse import urlencode
from pathlib import Path
from .common import write_json,request_bytes

# Restore only terms actually found in the source. Original text remains inspectable.
ALIASES={
    'Anthropic':['炭疽病','人类学','安思罗匹克'],
    'Claude Code':['Claude代码','Claude 代码','克劳德代码','克劳德·代码'],
    'OpenAI':['开放人工智能'],
    'NVIDIA':['英伟达','英维达'],
    'Google':['谷歌'],
    'Multimodal':['多模式','多模态'],
    'Agent':['代理','智能体'],
    'Token':['令牌','代币','标记'],
    'GPU':['图形处理器'],
    'HBM':['高带宽内存'],
}

def restore_terms(source,translated):
    for term,aliases in ALIASES.items():
        if re.search(r'(?<![A-Za-z])'+re.escape(term)+r's?(?![A-Za-z])',source,re.I):
            for alias in aliases:
                translated=translated.replace(alias,term)
            if not re.search(re.escape(term),translated,re.I):
                raise ValueError('译文未保留专业名称: '+term)
    return translated

def make_translator(config,cache_path):
    if config['provider']=='mymemory':return MyMemoryTranslator(config,cache_path)
    raise ValueError('未采用的翻译方式，不启用')

class MyMemoryTranslator:
    def __init__(self,config,cache_path):
        self.cache_path=Path(cache_path)
        self.limit=min(3000,int(config.get('max_characters_per_24h',3000)))
        self.max_bytes=min(450,int(config.get('max_bytes_per_request',450)))
        self.disabled=False
        try:data=json.loads(self.cache_path.read_text(encoding='utf-8'))
        except (OSError,ValueError):data={}
        self.cache=data.get('translations',{})
        self.requests=data.get('requests',[])
        self.requests=[r for r in self.requests if r['time']>time.time()-86400]
        self.ledger=None;self.new_requests=[]
        if os.environ.get('GITHUB_ACTIONS')=='true':
            from .translation_budget import ReleaseBudget
            self.ledger=ReleaseBudget(self.requests,self.limit)
            self.requests=list(self.ledger.requests)
            self.limit=min(self.limit,sum(r['characters'] for r in self.requests)+self.ledger.allowance)

    def __call__(self,text):
        if not text.strip():return ''
        # The anonymous service handles short requests; long excerpts are split by words.
        words=text.split();chunks=[];current=''
        for word in words:
            candidate=(current+' '+word).strip()
            if len(candidate.encode('utf-8'))>self.max_bytes:
                if not current:raise ValueError('新闻包含过长的单个词，不提交翻译')
                chunks.append(current);current=word
                if len(current.encode('utf-8'))>self.max_bytes:raise ValueError('新闻包含过长的单个词')
            else:current=candidate
        if current:chunks.append(current)
        return ''.join(self._one(chunk) for chunk in chunks)

    def _one(self,text):
        identity=hashlib.sha256(('mymemory|terms-v1|'+text).encode()).hexdigest()
        date=dt.datetime.now(dt.timezone.utc).date().isoformat()
        if identity in self.cache:
            self.cache[identity]['last_used']=date
            return self.cache[identity]['translated']
        if self.disabled:raise RuntimeError('本次免费翻译接口不可用，保留旧译文')
        now=time.time()
        self.requests=[r for r in self.requests if r['time']>now-86400]
        if sum(r['characters'] for r in self.requests)+len(text)>self.limit:
            raise RuntimeError('翻译已达滚动24小时3000字符上限，不发送新请求')
        # Persist before sending. Failed requests also consume the local budget; no automatic retry.
        record={'time':now,'characters':len(text)}
        self.requests.append(record);self.new_requests.append(record)
        self.save()
        url='https://api.mymemory.translated.net/get?'+urlencode({'q':text,'langpair':'en|zh-CN'})
        try:
            result=json.loads(request_bytes(url,retries=1))
            translated=result.get('responseData',{}).get('translatedText','').strip()
            if int(result.get('responseStatus',0))!=200 or result.get('quotaFinished'):
                raise RuntimeError('免费翻译服务额度不足或返回错误')
            if not re.search(r'[\u4e00-\u9fff]',translated):raise ValueError('缺少有效中文译文')
        except Exception:
            self.disabled=True
            raise
        translated=restore_terms(text,translated)
        self.cache[identity]={'translated':translated,'last_used':date}
        self.save()
        return translated

    def finish(self):
        self.save()
        if self.ledger:self.ledger.finish(self.new_requests)

    def save(self):
        cutoff=(dt.datetime.now(dt.timezone.utc).date()-dt.timedelta(days=90)).isoformat()
        self.cache={k:v for k,v in self.cache.items() if v.get('last_used','')>=cutoff}
        write_json(self.cache_path,{'provider':'mymemory','translations':self.cache,'requests':self.requests})
