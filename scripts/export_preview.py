"""Export a self-contained review snapshot; normal Pages remains API JSON-based."""
import argparse
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def export(output):
    html=(ROOT/'site/index.html').read_text(encoding='utf-8')
    css=(ROOT/'site/styles.css').read_text(encoding='utf-8')
    js=(ROOT/'site/app.js').read_text(encoding='utf-8')
    data={p.relative_to(ROOT/'site').as_posix():json.loads(p.read_text(encoding='utf-8')) for p in (ROOT/'site/data').rglob('*.json')}
    data['data/inventory.json']['terms']=json.loads((ROOT/'config/sources.json').read_text(encoding='utf-8'))['terms']
    text=json.dumps(data,ensure_ascii=False).replace('</','<\\/')
    loader='const reviewData='+text+';window.fetch=async(url)=>{const p=String(url).split("?")[0];return new Response(reviewData[p]?JSON.stringify(reviewData[p]):"missing",{status:reviewData[p]?200:404,headers:{"Content-Type":"application/json"}});};'
    html=html.replace('<link rel="stylesheet" href="styles.css">','<style>'+css+'</style>')
    html=html.replace('<script src="app.js" defer></script>','<script>'+loader+'</script><script>'+js+'</script>')
    html=html.replace('<header>','<p style="padding:12px;background:#fff1ce;color:#754500">本地验收预览 · 固定采集快照 · 点击刷新仅重新读取此文件内的数据 · 线上尚未更新</p><header>')
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(html,encoding='utf-8')
    print('Review HTML saved: '+str(output))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path)
    export(parser.parse_args().output)
