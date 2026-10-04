"""Only delete this project's daily archive releases older than configured retention."""
import argparse, datetime as dt, json, os, subprocess
from pathlib import Path

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo',required=True)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    days=json.loads((root/'config/sources.json').read_text(encoding='utf-8'))['history_days']
    cutoff=dt.datetime.now(dt.timezone.utc).date()-dt.timedelta(days=days)
    process=subprocess.run(['gh','api','--paginate',f'repos/{args.repo}/releases','--jq','.[].tag_name'],capture_output=True,text=True,check=True)
    for tag in process.stdout.splitlines():
        if not tag.startswith('daily-snapshot-'):
            continue
        try:
            date=dt.datetime.strptime(tag.removeprefix('daily-snapshot-'),'%Y%m%d').date()
        except ValueError:
            continue
        if date>=cutoff:
            continue
        print(('Delete ' if args.apply else 'Would delete ')+tag)
        if args.apply:
            subprocess.run(['gh','release','delete',tag,'--repo',args.repo,'--yes','--cleanup-tag'],check=True)
