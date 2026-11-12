"""Weekly discovery of finance research repositories and verifiable skills."""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
import urllib.parse
from typing import Any

from github_collector import API, request_json
from .common import SCHEMA_VERSION, utc_now

QUERIES = (
    ('行情数据', 'topic:financial-data'), ('财报与估值', 'financial statements valuation'),
    ('量化研究', 'topic:quantitative-finance'), ('回测', 'topic:backtesting'),
    ('风险管理', 'financial risk management'), ('金融 Skill', 'finance agent skills'),
    ('投资研究', 'investment research'),
)


def collect_github_finance(day: str, previous: dict[str, Any] | None = None) -> dict[str, Any]:
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    old = {str(row.get('full_name', '')).lower(): row for row in (previous or {}).get('rows', [])}
    found: dict[str, dict[str, Any]] = {}
    sources = []
    for domain, query in QUERIES:
        url = f"{API}/search/repositories?q={urllib.parse.quote(query + ' archived:false')}&sort=stars&order=desc&per_page=50"
        try:
            result = request_json(url, token)
            if result.get('incomplete_results'):
                raise ValueError('GitHub 搜索结果不完整')
            for item in result['items']:
                name = item['full_name']
                if item.get('fork') or not isinstance(item.get('stargazers_count'), int):
                    continue
                key = name.lower()
                if key in found:
                    continue
                before = old.get(key, {})
                stars = item['stargazers_count']
                previous_stars = before.get('stars')
                found[key] = {'full_name': name, 'url': item['html_url'], 'domain': domain,
                    'source_type': 'GitHub 搜索', 'stars': stars,
                    'stars_net_change': stars - previous_stars if isinstance(previous_stars, int) else None,
                    'description_raw': item.get('description') or '', 'skill_status': 'unverified',
                    'default_branch': item.get('default_branch') or 'HEAD'}
            sources.append({'name': query, 'url': 'https://github.com/search?' + urllib.parse.urlencode({'q': query, 'type': 'repositories'}), 'status': 'ok'})
        except Exception as exc:
            sources.append({'name': query, 'status': 'error', 'error': type(exc).__name__})
    if not found:
        raise ValueError('金融项目搜索未返回有效仓库')
    rows = sorted(found.values(), key=lambda row: (-row['stars'], row['full_name'].lower()))[:100]
    def verify_skill(row: dict[str, Any]) -> None:
        try:
            branch = urllib.parse.quote(row.pop('default_branch'), safe='')
            tree = request_json(f"{API}/repos/{row['full_name']}/git/trees/{branch}?recursive=1", token)
            if any(part.get('type') == 'blob' and part.get('path', '').split('/')[-1].lower() == 'skill.md' for part in tree.get('tree', [])):
                row['skill_status'] = 'verified'
            elif not tree.get('truncated'):
                row['skill_status'] = 'not_found'
        except Exception:
            row.pop('default_branch', None)
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(verify_skill, rows))
    now = utc_now()
    return {'schema_version': SCHEMA_VERSION, 'dataset': 'github_finance', 'snapshot_date': day,
        'generated_at_utc': now, 'captured_at_utc': now, 'comparison_snapshot_date': (previous or {}).get('snapshot_date'),
        'status': 'partial' if any(s['status'] != 'ok' for s in sources) or any(row['skill_status'] == 'unverified' for row in rows) else 'ok', 'sources': sources, 'rows': rows,
        'methodology': 'GitHub 金融主题及关键词搜索结果去重后按总 Stars 排序，最多 100 个；净变化与上次成功快照比较，首次观察为缺失。Skill 依据仓库文件树中的 SKILL.md 核实；核实失败不视为不存在。'}
