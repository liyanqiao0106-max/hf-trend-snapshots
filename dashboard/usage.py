from .common import envelope, request_json

URL='https://openrouter.ai/api/v1/datasets/rankings-daily'

def collect_usage(day,key):
    import datetime as dt
    from urllib.parse import urlencode
    end=dt.date.fromisoformat(day)-dt.timedelta(days=1)
    start=end-dt.timedelta(days=6)
    payload=request_json(URL+'?'+urlencode({'start_date':start.isoformat(),'end_date':end.isoformat(),'period':'day'}),key)
    grouped={}; totals={}; seen=set()
    for row in payload.get('data',[]):
        value=int(row['total_tokens']); model=row['model_permaslug']
        if not start.isoformat()<=row['date']<=end.isoformat():
            raise ValueError('Token 数据日期超出请求区间')
        identity=(row['date'],model)
        if identity in seen:
            raise ValueError('Token 数据含重复日期/模型')
        seen.add(identity)
        if value<0:
            raise ValueError('负 Token 总量')
        grouped[model]=grouped.get(model,0)+value
        totals[row['date']]=totals.get(row['date'],0)+value
    rows=[{'id':model,'tokens':str(value),'url':'https://openrouter.ai/rankings','coverage':'daily_top50_partial' if model!='other' else 'long_tail'} for model,value in sorted(grouped.items(),key=lambda x:x[1],reverse=True)]
    result=envelope('token_usage','OpenRouter', 'https://openrouter.ai/rankings',rows,
        'UTC 最近七个已结束日期的每日 Top 50 + other。平台总量为全部行相加；逐模型值仅包含进入日榜的日期，可能低估该模型七日用量。Token 含输入与输出，不代表全行业或用户数。',
        snapshot_date=day,period={'start':start.isoformat(),'end':end.isoformat(),'timezone':'UTC'},
        daily_totals=[{'date':date,'tokens':str(value)} for date,value in sorted(totals.items())],
        total_tokens=str(sum(totals.values())),source_as_of=payload.get('meta',{}).get('as_of'),license='CC BY 4.0')
    result['observed_days']=len(totals)
    if len(totals)!=7:
        result['status']='partial'
        result['methodology']+=' 当前只返回 '+str(len(totals))+' 个日期，不应当作完整七日总量。'
    return result
