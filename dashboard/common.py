from __future__ import annotations
import datetime as dt
import gzip
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = 'AI-Industry-Personal-Dashboard/1.0'

def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def request_bytes(url, token=None, accept='application/json', retries=3):
    headers={'User-Agent':UA,'Accept':accept}
    if token:
        headers['Authorization']='Bearer '+token
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=60) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code not in (429,500,502,503,504) or attempt==retries-1:
                raise RuntimeError(f'HTTP {exc.code}: {url.split("?")[0]}') from None
        except (urllib.error.URLError, TimeoutError):
            if attempt==retries-1:
                raise RuntimeError('无法连接来源: '+url.split('?')[0]) from None
        time.sleep(2**attempt)

def request_json(url, token=None):
    return json.loads(request_bytes(url,token))

def write_json(path, payload):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    temp.replace(path)

def envelope(dataset,source,url,rows,methodology,**extra):
    if not isinstance(rows,list):
        raise ValueError('rows 必须是列表')
    if not rows:
        raise ValueError('来源返回空数据，保留上次成功结果')
    return {'schema_version':1,'dataset':dataset,'source':source,'source_url':url,
            'generated_at_utc':utc_now(),'collected_at_utc':utc_now(),'status':'ok',
            'methodology':methodology,'rows':rows,**extra}

def archive(directory, day, dataset, payload):
    raw=json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode('utf-8')
    blob=gzip.compress(raw,mtime=0)
    path=Path(directory)/f'{dataset}_{day.replace("-", "")}.json.gz'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(blob)
    return {'file':path.name,'bytes':len(blob),'raw_bytes':len(raw),'sha256':hashlib.sha256(blob).hexdigest()}

def compact_price_history(directory, current, dataset, value_key):
    values=[]
    for path in sorted(Path(directory).glob(f'{dataset}_*.json.gz'))[-89:]:
        try:
            payload=json.loads(gzip.decompress(path.read_bytes()))
            vals=[float(r[value_key]) for r in payload['rows'] if r.get(value_key) is not None and float(r[value_key])>0]
            if vals:
                values.append({'date':payload.get('snapshot_date'),'median':sorted(vals)[len(vals)//2],'sample_count':len(vals)})
        except (ValueError, KeyError, OSError):
            continue
    vals=[float(r[value_key]) for r in current['rows'] if r.get(value_key) is not None and float(r[value_key])>0]
    if vals:
        values=[v for v in values if v['date']!=current['snapshot_date']]
        values.append({'date':current['snapshot_date'],'median':sorted(vals)[len(vals)//2],'sample_count':len(vals)})
    return values
