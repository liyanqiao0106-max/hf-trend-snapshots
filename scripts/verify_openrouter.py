"""Verify a zero-credit account using GET only; never print or persist the key."""
import argparse
import json
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dashboard.common import request_json, utc_now, write_json

def load_local_key():
    value=os.environ.get('OPENROUTER_API_KEY','').strip()
    env=Path(__file__).resolve().parents[1]/'.env'
    if not value and env.exists():
        for line in env.read_text(encoding='utf-8-sig').splitlines():
            if line.startswith('OPENROUTER_API_KEY='):
                value=line.split('=',1)[1].strip().strip('"').strip("'")
    return value

def verify(key):
    result={'checked_at_utc':utc_now(),'key_saved':False,'inference_called':False,'tests':{}}
    try:
        credits=request_json('https://openrouter.ai/api/v1/credits',key)['data']
        result['zero_credit_verified']=float(credits.get('total_credits',-1))==0 and float(credits.get('total_usage',-1))==0
    except Exception as exc:
        result['zero_credit_verified']=False
        result['credit_check_error']=str(exc)
    for name,url in {
        'token_usage':'https://openrouter.ai/api/v1/datasets/rankings-daily',
        'app_rankings':'https://openrouter.ai/api/v1/datasets/app-rankings?limit=5',
    }.items():
        try:
            payload=request_json(url,key)
            result['tests'][name]={'accessible':True,'rows':len(payload.get('data',[])),'meta':payload.get('meta',{})}
        except Exception as exc:
            result['tests'][name]={'accessible':False,'error':str(exc)}
    result['adopt_token_usage']=result['zero_credit_verified'] and result['tests']['token_usage']['accessible'] and result['tests']['token_usage']['rows']>0
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=Path('work/openrouter-verification.json'))
    args=parser.parse_args()
    key=load_local_key()
    if not key:
        print('API key 尚未配置；没有发送鉴权请求。')
        raise SystemExit(2)
    result=verify(key)
    write_json(args.output,result)
    print(json.dumps(result,ensure_ascii=True,indent=2))
