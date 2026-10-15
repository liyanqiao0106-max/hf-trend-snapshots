# AI 财务与研究前沿模块

两个模块沿用 `dashboard.run_daily --scope daily` → `site/data/<module>/latest.json` → `site/app.js` 的既有路径；每日 GitHub Actions 采集，单源失败保留最近成功快照并在清单中标记异常。

## 本地上游与运行依赖

- 项目根目录 `edgartools/`：`dgunning/edgartools` 官方 PyPI 源码发行包 `5.62.0` 的本地副本（含 `edgar/`、`pyproject.toml` 和许可证）。GitHub 完整归档下载持续中断，改用同项目的已发布源码包；不包含上游 Git 历史、测试与完整文档。运行时由 `requirements.txt` 安装 `edgartools==5.62.0`，不依赖把上游源码提交到本项目 Git。
- 项目根目录 `leaderboards/`：`huggingface/leaderboards` 固定提交 `7dd1bfe14302a55a6c8f38ed3a7211809e536b52` 的本地文档副本。上游没有可安装采集器；运行时使用 Hugging Face 官方 Hub API，而不是复制上游页面或代码。
- 本机依赖安装：`PIP_CACHE_DIR="$PWD/work/cache/pip" .venv/bin/python -m pip install -r requirements.txt`。缓存限制在项目内 `work/`。

## 财务口径

观察清单在 `config/ai_observatory.json`。SEC 标准 XBRL 指标包括购建物业、厂房与设备现金支出、营收与经营现金流；每个指标保留独立报告期间、申报日期、表单、accession 和 SEC 原件链接。10-Q 现金流通常为财年累计，不和 10-K 全年值直接相加。这里是**全公司资本开支**，不是 AI 专项资本开支，也不推算 AI 投入比例。若公司已停止使用标准资本开支标签，且该标签比同公司最新财务期早一年以上，页面不把旧事实冒充为当前资本开支；原始事实、期间和 SEC 原件链接保留在 JSON 的 `omitted_metrics`，来源标记 `partial`。

SEC 要求抓取身份。需由仓库管理员将可联系的 `名称 邮箱` 设为 GitHub Actions secret `SEC_USER_AGENT`；没有配置时该模块明确报告 `unavailable`，不会伪造数据或发送项目作者的个人邮箱。敏感身份不写入源码、快照或文档。

## 研究口径

使用 Hugging Face 官方 `get_dataset_leaderboard` 和 `list_daily_papers`。榜单按基准分别显示原始分、排名和 `verified`；排名变化只与上次成功快照的同一基准、同一模型比较，首次观察为空值。不合并不同基准分数，也不把未验证结果称作已复核；榜单 API 无结果发布时间，只显示采集时间。论文保留英文原题、原始摘要、发布时间、HF 提交时间及原文链接，不伪造中文翻译或新鲜度。空榜单/失败来源写入 `sources` 状态，至少一个来源成功时整体为 `partial`。

## 发布验证

运行 `.venv/bin/python -m unittest discover -s tests -v`、`npm test -- --reporter=line`、`.venv/bin/python scripts/check_contract.py` 和 `node --check site/app.js`。提交和发布时仅暂存本模块新文件与实际改动；不要把当前工作区的 RSS、新闻预览、历史快照或翻译缓存带入发布。
