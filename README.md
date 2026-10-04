# AI 产业观察：免费个人看板

沿用现有 GitHub Actions、Releases 和 Pages。前端只读 JSON，采集器独立运行，历史快照不进入 Git 仓库。当前为本地待审核版本，未修改线上网站。

## 已确认的运行方式

- 上海时间每天 12:00 触发，包括周末；Actions 可能排队延迟，不保证 12:00 整发布。
- 每次打开或点击刷新读取最近成功快照；浏览器不直接抓外部 API。
- 全免费：公开仓库、标准 GitHub runner、免费公开数据，不启用付费兜底。
- 历史数据采用 Release 压缩附件，保留 90 天每日快照；既有 weekly seed Releases 不删除。
- 新闻展示标题、订阅源短导语和原文链接；国际新闻翻译成功后进入中文页面。
- 国际新闻采用 MyMemory 匿名免费接口，滚动24小时最多3000字符。缓存不扣量，失败请求计量，无自动重试和付费兜底。Actions 先将额度预留保存至专用 Release 账本，失败重跑不重复获得额度。两款未通过测试的离线模型已清理。
- iOS AI App 和产品指数不纳入；RAM 改为存储产业动态与原站链接。

## 栏目口径

| 栏目 | 来源和范围 |
|---|---|
| AI 新闻 | IT之家、Google AI、NVIDIA、TechCrunch AI 公开 RSS；七日内去重 |
| Token 用量 | OpenRouter Data API；真实零充值账户验证成功后才启用；不能代表全行业 |
| Token 价格 | OpenRouter 模型目录；USD/百万 Token，输入/输出分列；替代 Silicon Data 商业指数 |
| GPU 报价 | Azure Retail Prices API；H100 Linux 整机价格除以八，含 CPU/RAM 分摊；On-demand/Spot 分列 |
| 存储动态 | 新闻中的 HBM/DRAM/NAND/内存关键词，以及原站链接；不转载商业价格 |
| Hugging Face | 原多池采集，450 个完整历史模型与 50 个观察模型；约七日/十四日前快照比较，间隔不等标注七日等效值 |
| GitHub | 周 Trending 候选池 + 官方仓库 API；周新增 Stars 与总 Stars 的快照净变化分列 |

## 解耦结构

`config/sources.json` 控制来源与术语；`dashboard/prices.py`、`news.py`、`usage.py` 为独立适配器；HF/GitHub 原采集器继续复用。`run_daily.py` 编排并生成 `site/data/<module>/latest.json`；`storage.py` 管理校验与恢复；`site/` 只负责展示。

失败来源保留最近成功结果并标注 stale，成功来源继续更新。整个快照校验通过后才覆盖文件。将来可用数据库替代 Release，保持前端 JSON 契约。

## 本地验证

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m dashboard.run_daily
python -m http.server 8000 --directory site
```

浏览器访问 `http://localhost:8000`。采集需要网络，HF 全量采集不是只抓榜单前十项。

创建 OpenRouter API key，保存在本地 `.env` 的 `OPENROUTER_API_KEY=` 后，运行 `python scripts/verify_openrouter.py`。脚本只发 GET，不调用模型推理、不输出 key。验证成功后再启用用量模块，本地 key 不会自动同步到 Actions。

## 上线准备

完成翻译、账户验证和模块审核后另行确认发布。Actions key 放入仓库 Settings → Secrets and variables → Actions 的 `OPENROUTER_API_KEY`；不能写入 HTML、JSON、Git 或公开附件。`HF_TOKEN` 可选。

Workflow 的 `0 4 * * *` 为上海时间 12:00，Pages 使用 GitHub Actions 部署源。部署 artifact 保留一天，持久数据在 Releases。不使用 Git LFS、不提交模型权重、不增加付费 runner。定时流程可能因长期无仓库活动停用，页面用时间戳提示陈旧数据。

## 大小与额度

2026-10-03 实测：HF 21,925 模型的 gzip CSV 为1,446,583 bytes；接入国际新闻和翻译缓存后的日快照为1,606,108 bytes（约1.61 MB / 1.53 MiB），包括15条新闻中的8条国际新闻译文。尚不含OpenRouter用量，不是最终上限。保留90天约145 MB。每次采集在 `storage-report.json` 和 Actions 摘要报告实际体积。

GitHub Free Actions artifact 免费存储 500 MB，cache 默认每仓库 10 GB，Pages 站点上限 1 GB。Release 单附件小于 2 GiB、每 Release 最多 1000 附件；官方未列 Release 总大小或带宽限制。临时下载模型不进入快照，不启用 Actions 模型缓存。

来源：[Actions 计费](https://docs.github.com/en/billing/concepts/product-billing/github-actions)、[Release 限制](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)、[Pages 限制](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)。
