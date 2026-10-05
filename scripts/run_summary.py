import json
import os
from pathlib import Path

root=Path(__file__).resolve().parents[1]
manifest_path=root/'site/data/manifest.json'
manifest=json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else json.loads((root/'site/data/inventory.json').read_text(encoding='utf-8'))
storage=json.loads((root/'dist/storage-report.json').read_text(encoding='utf-8'))
modules=manifest.get('modules') or {item['module']:item for item in manifest.get('sources',[])}
lines=['## AI 行业看板采集结果','',f"压缩快照：{storage['bundle_bytes']:,} bytes。范围：{manifest.get('scope','all')}。",'', '| 模块 | 状态 | 记录数 |','|---|---|---|']
lines.extend(f"| {name} | {item.get('status')} | {item.get('rows',0)} |" for name,item in modules.items())
text='\n'.join(lines)+'\n'
if os.environ.get('GITHUB_STEP_SUMMARY'):
    with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as handle:
        handle.write(text)
else:
    print(text)
