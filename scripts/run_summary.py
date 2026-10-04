import json, os
from pathlib import Path
root=Path(__file__).resolve().parents[1]
inventory=json.loads((root/'site/data/inventory.json').read_text(encoding='utf-8'))
storage=json.loads((root/'dist/storage-report.json').read_text(encoding='utf-8'))
lines=['## 每日 AI 采集结果','',f"压缩日快照：{storage['bundle_bytes']:,} bytes。每天 12:00 上海时间，周末照常。",'', '| 模块 | 状态 | 记录数 |','|---|---|---|']
lines.extend(f"| {s['module']} | {s['status']} | {s.get('rows',0)} |" for s in inventory['sources'])
text='\n'.join(lines)+'\n'
if os.environ.get('GITHUB_STEP_SUMMARY'):
    with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as f:
        f.write(text)
else:
    print(text)
