import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
index=(root/'site/index.html').read_text(encoding='utf-8')
app=(root/'site/app.js').read_text(encoding='utf-8')
required=['overview','token','models','gpu','storage','hugging-face','github']
for name in required:
    if f'data-module="{name}"' not in index:
        raise SystemExit(f'missing navigation module: {name}')
for name in ('ai-financials', 'ai-frontier'):
    if f"'{name}':{{title:" not in app or f"['{name}'," not in app:
        raise SystemExit(f'missing dynamic navigation module: {name}')
for token in ('data/manifest.json','loadModule','state.pending'):
    if token not in app:
        raise SystemExit(f'missing frontend contract token: {token}')
config=json.loads((root/'config/sources.json').read_text(encoding='utf-8'))
if config.get('history_days')!=90:
    raise SystemExit('retention period is invalid')
print('Static dashboard contract OK')
