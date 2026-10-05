"""Small daily bundles in Releases, isolated from Actions artifact storage."""
from __future__ import annotations
import datetime as dt
import hashlib
import io
import json
import tarfile
from pathlib import Path
from .common import request_json,request_bytes,write_json

def release_list(repo,token=None):
    rows=[]
    for page in range(1,5):
        batch=request_json(f'https://api.github.com/repos/{repo}/releases?per_page=100&page={page}',token)
        if not isinstance(batch,list):
            raise ValueError('Release 列表格式错误')
        rows.extend(batch)
        if len(batch)<100:
            break
    return rows

def select_spaced(days):
    days=sorted(set(days),reverse=True)
    if not days:
        return []
    selected=[days[0]]
    for offset in (7,14):
        target=days[0]-dt.timedelta(days=offset)
        candidates=[d for d in days if d<selected[-1] and abs((d-target).days)<=7]
        if candidates:
            selected.append(min(candidates,key=lambda d:(abs((d-target).days),d)))
    return selected

def unpack_bundle(blob,destination,restore_site=False):
    root=Path(destination).resolve()
    manifest=None
    with tarfile.open(fileobj=io.BytesIO(blob),mode='r:gz') as tar:
        members=tar.getmembers()
        entries={m.name:m for m in members}
        if 'bundle_manifest.json' not in entries:
            raise ValueError('快照缺少校验清单')
        manifest=json.load(tar.extractfile(entries['bundle_manifest.json']))
        validated=[]
        for name,meta in manifest['files'].items():
            member=entries.get(name)
            target=(root/name).resolve()
            if not target.is_relative_to(root) or not member or not member.isfile():
                raise ValueError('快照路径不合法')
            raw=tar.extractfile(member).read()
            if len(raw)!=meta['bytes'] or hashlib.sha256(raw).hexdigest()!=meta['sha256']:
                raise ValueError('快照校验失败: '+name)
            if (name.startswith('site/') or name=='history/translation-cache.json') and not restore_site:
                continue
            validated.append((target,raw))
        # Verify the entire bundle before overwriting any healthy local module.
        for target,raw in validated:
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(raw)
    return manifest

def restore(repo,root,history,day,token=None):
    releases=release_list(repo,token)
    daily=[]
    for release in releases:
        tag=release.get('tag_name','')
        if tag.startswith('daily-snapshot-'):
            stamp=release['tag_name'].removeprefix('daily-snapshot-')
            try:
                date=dt.datetime.strptime(stamp,'%Y%m%d').date()
            except ValueError:
                continue
            assets={a['name']:a for a in release['assets']}
            asset=assets.get(f'daily_snapshot_{stamp}.tar.gz')
            if asset:
                daily.append((date,asset))
        elif tag.startswith('market-'):
            for asset in release.get('assets',[]):
                if not asset.get('name','').startswith('daily_snapshot_') or not asset['name'].endswith('.tar.gz'):
                    continue
                try:
                    stamp=asset['name'][15:23]
                    date=dt.datetime.strptime(stamp,'%Y%m%d').date()
                except ValueError:
                    continue
                daily.append((date,asset))
    chosen=select_spaced([date for date,asset in daily]+[dt.date.fromisoformat(day)])
    newest=max((d for d,a in daily),default=None)
    local_manifest=None
    for candidate in (Path(root)/'site/data/manifest.json',Path(root)/'site/data/inventory.json'):
        try:
            local_manifest=json.loads(candidate.read_text(encoding='utf-8'))
            break
        except (OSError,ValueError):
            pass
    try:
        local_date=dt.date.fromisoformat((local_manifest or {}).get('snapshot_date',''))
    except ValueError:
        local_date=None
    wanted=set(chosen)|({newest} if newest else set())
    for date,asset in sorted(daily,reverse=True):
        if date not in wanted:
            continue
        blob=request_bytes(asset['browser_download_url'],accept='application/octet-stream')
        # Never let a same-day or older remote archive overwrite locally generated schema/data.
        unpack_bundle(blob,root,restore_site=date==newest and (local_date is None or date>local_date))
    # Preserve existing weekly seed releases during transition to daily snapshots.
    legacy=[]
    for release in releases:
        for asset in release.get('assets',[]):
            if asset['name'].startswith('models_') and asset['name'].endswith('.csv.gz'):
                date=dt.datetime.strptime(asset['name'][7:15],'%Y%m%d').date()
                legacy.append((date,release,asset))
    existing=list(Path(history).glob('models_*.csv.gz'))
    available=[dt.datetime.strptime(p.name[7:15],'%Y%m%d').date() for p in existing]
    want=set(select_spaced(available+[d for d,r,a in legacy]+[dt.date.fromisoformat(day)]))
    for date,release,asset in legacy:
        if date not in want:
            continue
        stamp=date.strftime('%Y%m%d')
        for entry in release.get('assets',[]):
            if entry['name'] in (asset['name'],f'manifest_{stamp}.json'):
                path=Path(history)/entry['name']
                if not path.exists():
                    path.parent.mkdir(parents=True,exist_ok=True)
                    path.write_bytes(request_bytes(entry['browser_download_url'],accept='application/octet-stream'))
    # Weekly GitHub assets existed under both a stable and a dated filename.
    for release in releases:
        for asset in release.get('assets',[]):
            name=asset.get('name','')
            if name!='github_snapshot.json' and not (name.startswith('github_snapshot_') and name.endswith('.json')):
                continue
            raw=request_bytes(asset['browser_download_url'],accept='application/octet-stream')
            try:
                payload=json.loads(raw)
                stamp=str(payload.get('snapshot_date','')).replace('-','')
                if len(stamp)!=8 or not stamp.isdigit():
                    continue
            except (ValueError,TypeError):
                continue
            target=Path(history)/f'github_snapshot_{stamp}.json'
            if not target.exists():
                target.write_bytes(raw)
    return releases

def bundle(root,dist,day,extra_paths):
    root=Path(root); dist=Path(dist); dist.mkdir(parents=True,exist_ok=True)
    paths=list((root/'site/data').rglob('*.json'))+list(extra_paths)
    entries={}
    for path in paths:
        if path.exists():
            name=path.relative_to(root).as_posix()
            raw=path.read_bytes()
            entries[name]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    manifest={'schema_version':2,'date':day,'files':entries}
    output=dist/f'daily_snapshot_{day.replace("-", "")}.tar.gz'
    with tarfile.open(output,'w:gz') as tar:
        for name in entries:
            tar.add(root/name,arcname=name)
        raw=json.dumps(manifest,ensure_ascii=False).encode()
        info=tarfile.TarInfo('bundle_manifest.json'); info.size=len(raw)
        tar.addfile(info,io.BytesIO(raw))
    write_json(dist/'storage-report.json',{'bundle':output.name,'bundle_bytes':output.stat().st_size,
        'uncompressed_bytes':sum(m['bytes'] for m in entries.values()),'files':entries})
    return output
