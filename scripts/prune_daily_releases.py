"""Delete only this dashboard's dated assets beyond the configured retention."""
import argparse
import datetime as dt
import json
import re
import subprocess
from pathlib import Path


def run(*args):
    return subprocess.run(args,capture_output=True,text=True,check=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo',required=True)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    days=json.loads((root/'config/sources.json').read_text(encoding='utf-8'))['history_days']
    cutoff=dt.datetime.now(dt.timezone.utc).date()-dt.timedelta(days=days)
    releases=json.loads(run('gh','api','--paginate',f'repos/{args.repo}/releases').stdout)
    for release in releases:
        tag=release.get('tag_name','')
        if tag.startswith('daily-snapshot-'):
            try: date=dt.datetime.strptime(tag.removeprefix('daily-snapshot-'),'%Y%m%d').date()
            except ValueError: continue
            if date<cutoff:
                print(('Delete ' if args.apply else 'Would delete ')+tag)
                if args.apply: subprocess.run(['gh','release','delete',tag,'--repo',args.repo,'--yes','--cleanup-tag'],check=True)
            continue
        if not tag.startswith('market-'):
            continue
        for asset in release.get('assets',[]):
            match=re.search(r'(\d{8})',asset.get('name',''))
            if not match: continue
            try: date=dt.datetime.strptime(match.group(1),'%Y%m%d').date()
            except ValueError: continue
            if date>=cutoff: continue
            print(('Delete asset ' if args.apply else 'Would delete asset ')+asset['name'])
            if args.apply: subprocess.run(['gh','api','-X','DELETE',f"repos/{args.repo}/releases/assets/{asset['id']}"],check=True)
