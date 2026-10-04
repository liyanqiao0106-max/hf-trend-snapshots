from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import shutil
import sys
from pathlib import Path

from .common import ROOT, archive, utc_now, write_json
from .news import collect_news,memory_payload
from .prices import collect_models,collect_gpu
from .storage import restore,bundle,select_spaced
from .usage import collect_usage

def read_previous(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError,ValueError):
        return None

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo',default='liyanqiao0106-max/hf-trend-snapshots')
    parser.add_argument('--skip-restore',action='store_true')
    parser.add_argument('--reuse-hf',type=Path)
    args=parser.parse_args()
    # Fixed UTC+8 needs no platform timezone database on Windows.
    day=dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).date().isoformat()
    config=json.loads((ROOT/'config/sources.json').read_text(encoding='utf-8'))
    history=ROOT/'history'; dist=ROOT/'dist'
    history.mkdir(exist_ok=True); dist.mkdir(exist_ok=True)
    statuses=[]; archives=[]; raw_paths=[]
    if not args.skip_restore:
        try:
            restore(args.repo,ROOT,history,day,os.environ.get('GH_TOKEN'))
        except Exception as exc:
            statuses.append({'module':'restore','status':'error','error':str(exc)})
            # A failed restore must not publish a site missing old healthy modules.
            if not (ROOT/'site/data/inventory.json').exists():
                raise RuntimeError('无法恢复历史看板；暂停本次发布，线上仍保留旧版本') from exc
    def run(name,function):
        path=ROOT/'site/data'/name/'latest.json'
        previous=read_previous(path)
        try:
            payload=function(previous)
            if not isinstance(payload.get('rows'),list):
                raise ValueError('JSON rows 契约错误')
            if name in ('token-prices','gpu-prices'):
                key='input_usd_per_million' if name=='token-prices' else 'usd_per_gpu_hour'
                values=[float(r[key]) for r in payload['rows'] if float(r[key])>0 and (name!='gpu-prices' or r['billing']=='On-demand')]
                trend=list((previous or {}).get('history',[]))
                trend=[r for r in trend if r['date']!=day][-89:]
                if values:
                    trend.append({'date':day,'median':sorted(values)[len(values)//2],'sample_count':len(values)})
                payload['history']=trend
                payload['history_note']='每日可用样本中位数，仅描述样本；成员变化也会改变中位数，不是固定篮子指数。GPU 趋势仅 On-demand。'
            write_json(path,payload)
            metadata=archive(dist,day,payload['dataset'],payload)
            archives.append(metadata)
            status={'module':name,'status':payload.get('status','ok'),'rows':len(payload['rows']),
                'last_success_at_utc':payload['generated_at_utc'],'snapshot_date':payload.get('snapshot_date',day)}
            if name=='news':
                status['translation_pending']=payload.get('translation_pending',0)
                status['feed_checks']=payload.get('feed_checks',[])
            statuses.append(status)
            return payload
        except Exception as exc:
            statuses.append({'module':name,'status':'stale' if previous else 'unavailable','error':str(exc),
                'last_success_at_utc':(previous or {}).get('generated_at_utc'),'rows':len((previous or {}).get('rows',[]))})
            return previous

    translator=None
    if config.get('translation',{}).get('provider') not in (None,'pending'):
        try:
            from .translation import make_translator
            translator=make_translator(config['translation'],history/'translation-cache.json')
        except Exception as exc:
            statuses.append({'module':'translation','status':'error','error':str(exc)})
    news=run('news',lambda previous:collect_news(day,config,translator,previous))
    run('memory',lambda previous:memory_payload(news,day) if news and statuses[-1]['status']!='stale' else (_ for _ in ()).throw(ValueError('新闻未更新，保留上次存储产业动态')))
    run('token-prices',lambda previous:collect_models(day))
    run('gpu-prices',lambda previous:collect_gpu(day,config['gpu_skus']))

    def hf(previous):
        from collector import collect
        from weekly_dashboard import local_snapshot_refs,load_snapshot,build_payload,validate_payload
        if args.reuse_hf:
            candidates=list(args.reuse_hf.glob('models_*.csv.gz'))
            if len(candidates)!=1:
                raise ValueError('重用目录必须恰好有一个快照')
            data=candidates[0]; manifest=args.reuse_hf/('manifest_'+data.name[7:15]+'.json')
        else:
            data,manifest=collect(dist,snapshot_day=dt.date.fromisoformat(day))
        for path in (data,manifest):
            target=history/path.name
            shutil.copyfile(path,target)
            raw_paths.append(target)
        refs=local_snapshot_refs(history)
        selected=select_spaced(refs)
        if len(selected)<3:
            raise ValueError('周下载加速度需要当前、约7日前、约14日前三期有效快照')
        payload=build_payload([load_snapshot(refs[d]) for d in selected])
        validate_payload(payload)
        payload.update(snapshot_date=day,status='ok',methodology='累计下载量差分，比较约7日前与14日前快照。非七日间隔标注7日等效值，历史不足的模型单列观察。')
        return payload
    run('hugging-face',hf)

    def github(previous):
        from github_collector import collect
        from github_dashboard import build_payload,validate
        output=history/f'github_snapshot_{day.replace("-", "")}.json'
        collect(output,date_value=day,token=os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN'),no_readme=True)
        raw_paths.append(output)
        snapshot=json.loads(output.read_text(encoding='utf-8'))
        payload=build_payload(snapshot)
        payload['rows']=[r for r in payload['rows'] if not r['domain'].startswith('非AI')]
        payload['count']=len(payload['rows'])
        if not payload['rows']:
            raise ValueError('本期未识别 AI 相关项目')
        for rank,row in enumerate(payload['rows'],1):
            row['weekly_rank']=rank
        old={(r.get('full_name')):r for r in (previous or {}).get('rows',[])}
        for row in payload['rows']:
            before=old.get(row['full_name'])
            row['stars_net_change']=row['stars']-before['stars'] if before and isinstance(before.get('stars'),int) and isinstance(row.get('stars'),int) else None
            if translator and row.get('description_raw'):
                try:
                    from .news import excerpt
                    row['use_case_zh']='主要用于'+row['domain']+'；简介：'+translator(excerpt(row['description_raw'],'en'))
                    row['use_case_translation_status']='machine'
                except Exception:
                    row['use_case_zh']='主要用于'+row['domain']+'；中文简介待翻译，请查看原仓库。'
                    row['use_case_translation_status']='pending'
        payload['comparison_snapshot_date']=(previous or {}).get('snapshot_date')
        payload['methodology']='周 Trending 页面新增 Stars；总 Stars 来自官方 API。净变化与上次成功快照比较，可能包含取消收藏，首次观察无净变化。'
        payload['status']='ok' if all(r.get('stars') is not None and r.get('use_case_translation_status')!='pending' for r in payload['rows']) else 'partial'
        validate(payload)
        return payload
    run('github',github)
    # User explicitly excludes iOS and product leaderboards. Only Token usage can be enabled after verification.
    usage_config=config.get('openrouter_usage',{})
    if usage_config.get('zero_credit_verified'):
        key=os.environ.get('OPENROUTER_API_KEY')
        if not key:
            from scripts.verify_openrouter import load_local_key
            key=load_local_key()
        run('token-usage',lambda previous:collect_usage(day,key) if key else (_ for _ in ()).throw(ValueError('API key 未配置')))
    else:
        statuses.append({'module':'token-usage','status':'pending_verification','rows':0,'error':'等待零充值账户 API key 验证，未采用也未调用推理'})
    if translator is not None:
        translator.save()
        if hasattr(translator,'finish'):
            try:translator.finish()
            except Exception as exc:statuses.append({'module':'translation-budget','status':'error','error':str(exc)})
        raw_paths.append(history/'translation-cache.json')
    inventory={'schema_version':1,'generated_at_utc':utc_now(),'snapshot_date':day,'schedule':config['schedule'],
        'sources':statuses,'terms':config['terms'],'archives':archives,'history_days':config['history_days'],
        'translation_provider':config.get('translation',{}).get('provider','pending')}
    if translator is not None:
        import time
        inventory['translation_budget']={'limit_characters_24h':3000,
            'used_characters_24h':sum(r['characters'] for r in translator.requests if r['time']>time.time()-86400)}
    write_json(ROOT/'site/data/inventory.json',inventory)
    archive_path=bundle(ROOT,dist,day,raw_paths+[dist/m['file'] for m in archives])
    print(json.dumps({'bundle_bytes':archive_path.stat().st_size,'sources':statuses},ensure_ascii=True),flush=True)
    if not any(s['status'] in ('ok','partial') for s in statuses):
        raise RuntimeError('没有成功更新的来源，禁止发布空看板')

if __name__=='__main__':
    main()
