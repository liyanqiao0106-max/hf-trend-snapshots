from __future__ import annotations
import datetime as dt
import email.utils
import hashlib
import html
import re
import xml.etree.ElementTree as ET
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from .common import envelope, request_bytes, utc_now

AI=re.compile(r'\b(?:AI|LLM|GPU|HBM|DRAM|NAND|SSD|HDD|Claude|Anthropic|OpenAI|DeepSeek|Qwen|Gemini|ChatGPT|Agent|inference|multimodal)\b|人工智能|大模型|智能体|算力|英伟达|豆包|千问|智谱|机器学习|光互联|光刻',re.I)
MEMORY=re.compile(r'\b(?:RAM|HBM|DRAM|NAND|GDDR|DDR[456]|memory|Micron|SK Hynix)\b|内存|显存|存储芯片|美光|海力士',re.I)
MEMORY_INDUSTRY=re.compile(r'\b(?:supply|demand|production|fab|capacity|Micron|SK Hynix|Samsung|price)\b|产能|供应|供需|需求|涨价|降价|制造商|晶圆|工厂|美光|海力士|三星|闪存',re.I)
EVENT=re.compile(r'\b(?:launch|release|announce|acquire|invest|funding|raise|order|contract|deploy|partnership|revenue|earnings|capacity|production|price|availability|benchmark|open.source)\b|发布|推出|上线|投资|融资|收购|订单|合同|采购|部署|合作|营收|财报|扩产|量产|涨价|降价|开源|基准',re.I)
REJECT=re.compile(r'\b(?:rumou?r|opinion|sponsored|roundup|tutorial|how to|guide)\b|传闻|据传|观点|评论|软文|赞助|教程|盘点|汇总|如何',re.I)
CHAIN_RULES=[
    ('上游/芯片与算力',re.compile(r'\b(?:GPU|HBM|DRAM|NAND|semiconductor|chip|lithography|datacenter|data center|optical interconnect)\b|芯片|半导体|算力|光互联|光刻|数据中心',re.I)),
    ('中游/模型与工具',re.compile(r'\b(?:LLM|model|inference|fine.?tun|Agent|skill|MCP|Hugging Face|GitHub)\b|模型|推理|微调|智能体|开源',re.I)),
    ('下游/应用与商业化',re.compile(r'\b(?:application|customer|contract|order|procurement|enterprise|commercial)\b|应用|客户|采购|订单|商业化|企业服务',re.I)),
]

def memory_related(text):
    return bool(MEMORY.search(text) and MEMORY_INDUSTRY.search(text))

def canonical_url(value):
    parts=urlsplit(value)
    query=[(k,v) for k,v in parse_qsl(parts.query,keep_blank_values=True) if not k.lower().startswith('utm_') and k.lower() not in ('ref','source','fbclid','gclid')]
    return urlunsplit((parts.scheme.lower(),parts.netloc.lower(),parts.path.rstrip('/') or '/',urlencode(query),''))

def chain_category(text):
    for name,pattern in CHAIN_RULES:
        if pattern.search(text):
            return name
    return '产业综合'

def eligible_news(row,feed):
    text=' '.join((row.get('title_raw',''),row.get('summary_raw','')))
    if REJECT.search(text):
        return False
    if feed.get('tier',2)==1:
        return bool(AI.search(text) and (EVENT.search(text) or feed.get('official')))
    # Secondary media must place both AI subject and verifiable event in the title.
    return bool(AI.search(row.get('title_raw','')) and EVENT.search(row.get('title_raw','')))

def clean(value):
    value=re.sub(r'<(script|style)\b.*?</\1>',' ',value,flags=re.I|re.S)
    return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',value))).strip()

def timestamp(value):
    try:
        parsed=email.utils.parsedate_to_datetime(value)
    except (ValueError,TypeError):
        try:
            parsed=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
        except (ValueError,TypeError):
            return None
    if not parsed.tzinfo:
        parsed=parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)

def excerpt(value, language):
    value=clean(value)
    if language=='en':
        value=re.split(r'\s+(?:The post|Read more|Continue reading)\b',value)[0]
        return ' '.join(value.split()[:32])
    value=re.split(r'\s*(?:责任编辑|广告声明|相关阅读|查看更多)',value)[0]
    return value[:150]

def parse_feed(raw, feed, now=None, days=7):
    now=now or dt.datetime.now(dt.timezone.utc)
    root=ET.fromstring(raw)
    items=root.findall('.//item')
    atom='{http://www.w3.org/2005/Atom}'
    if not items:
        items=root.findall('.//'+atom+'entry')
    if not items:
        raise ValueError('返回内容不是含新闻条目的 RSS/Atom')
    rows=[]
    for item in items:
        title=clean(item.findtext('title') or item.findtext(atom+'title') or '')
        link=item.findtext('link')
        if not link:
            node=item.find(atom+'link')
            link=node.get('href') if node is not None else ''
        date=timestamp(item.findtext('pubDate') or item.findtext(atom+'published') or item.findtext(atom+'updated') or '')
        description=item.findtext('description') or item.findtext(atom+'summary') or ''
        if not title or not link or not link.startswith(('https://','http://')) or not date:
            continue
        if date>now+dt.timedelta(hours=2) or date<now-dt.timedelta(days=days):
            continue
        summary=excerpt(description,feed['language'])
        if not AI.search(title+' '+summary) and not memory_related(title+' '+summary):
            continue
        link=canonical_url(link)
        text=title+' '+summary
        rows.append({'id':hashlib.sha256(link.encode()).hexdigest()[:20],
            'title_raw':title,'summary_raw':summary,'title':title,'summary':summary,
            'url':link,'source':feed['name'],'region':feed['region'],'language':feed['language'],
            'published_at_utc':date.isoformat(),'translation_status':'original' if feed['language']=='zh' else 'pending',
            'source_tier':feed.get('tier',2),'official':bool(feed.get('official')),
            'chain_category':chain_category(text),'memory_related':memory_related(text)})
    return rows

def collect_news(day, config, translator=None, previous=None):
    rows=[]; checks=[]; untranslated=0; translation_errors=[]
    for feed in config['feeds']:
        try:
            found=parse_feed(request_bytes(feed['url'],accept='application/xml,text/xml,*/*',cache_key='feed:'+feed['url']),feed,days=config['news_days'])
            found=[row for row in found if eligible_news(row,feed)]
            checks.append({'source':feed['name'],'url':feed['url'],'status':'ok','eligible':len(found),'checked_at_utc':utc_now()})
            maximum=4 if feed['language']=='en' else config['news_limit_per_region']
            for row in sorted(found,key=lambda r:r['published_at_utc'],reverse=True)[:maximum]:
                if row['language']=='en':
                    if translator is None:
                        untranslated+=1
                        continue
                    try:
                        row['title']=translator(row['title_raw'])
                        row['summary']=translator(row['summary_raw']) if row['summary_raw'] else ''
                        row['translation_status']='machine'
                    except Exception as exc:
                        untranslated+=1
                        translation_errors.append({'id':row['id'],'source':row['source'],'error':str(exc)})
                        continue
                rows.append(row)
        except Exception as exc:
            checks.append({'source':feed['name'],'url':feed['url'],'status':'error','error':str(exc),'checked_at_utc':utc_now()})
    if not any(c['status']=='ok' for c in checks):
        raise ValueError('全部新闻源采集失败，保留上次成功结果')
    if previous:
        cutoff=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(days=config['news_days'])).isoformat()
        ids={r['id'] for r in rows}
        for row in previous.get('rows',[]):
            text=row.get('title_raw',row['title'])+' '+row.get('summary_raw',row['summary'])
            if row.get('published_at_utc','')>=cutoff and row['id'] not in ids and (AI.search(text) or memory_related(text)):
                rows.append(row)
                ids.add(row['id'])
    rows.sort(key=lambda r:r['published_at_utc'],reverse=True)
    rows.sort(key=lambda r:r.get('source_tier',2))
    selected=[]; seen=set(); clusters=set(); regions={}; sources={}
    for row in rows:
        source_maximum=4 if row['language']=='en' else config['news_limit_per_region']
        words=re.sub(r'[^a-z0-9\u4e00-\u9fff]+',' ',row.get('title_raw','').lower()).split()
        cluster=' '.join(words[:8])
        if row['id'] in seen or cluster in clusters or regions.get(row['region'],0)>=config['news_limit_per_region'] or sources.get(row['source'],0)>=source_maximum:
            continue
        seen.add(row['id']);clusters.add(cluster);regions[row['region']]=regions.get(row['region'],0)+1;sources[row['source']]=sources.get(row['source'],0)+1
        selected.append(row)
        if len(selected)>=config.get('news_maximum',50):
            break
    selected.sort(key=lambda r:r['published_at_utc'],reverse=True)
    result=envelope('news','公开 RSS', 'https://www.ithome.com/rss/',selected,
        '最近七日 AI 产业事件；必须命中产业链、事件类型和可核查主体。按规范 URL 与标题聚类去重，一级官方来源优先；国际新闻翻译失败时不伪装为中文。',snapshot_date=day,feed_checks=checks,translation_pending=untranslated,translation_errors=translation_errors)
    if untranslated or any(c['status']!='ok' for c in checks):
        result['status']='partial'
    return result

def memory_payload(news, day):
    rows=[r for r in news['rows'] if memory_related(r.get('title_raw',r['title'])+' '+r.get('summary_raw',r['summary']))]
    if not rows:
        return {'schema_version':1,'dataset':'memory','source':'公开新闻','source_url':'https://www.dramexchange.com/',
            'generated_at_utc':utc_now(),'snapshot_date':day,'status':'no_recent_news',
            'methodology':'仅存储产业新闻与原站链接，不抓取或转载商业 RAM 指数。最近七日未发现匹配新闻。','rows':[]}
    return envelope('memory','公开新闻','https://www.dramexchange.com/',rows,
        'HBM / DRAM / NAND / 内存相关新闻，来自 AI 新闻中的规则筛选。原站仅提供访问链接，不展示未经授权的商业价格。',snapshot_date=day)
