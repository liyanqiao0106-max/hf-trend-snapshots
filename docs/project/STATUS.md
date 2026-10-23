# 项目状态

最后更新：2026-10-23（Asia/Shanghai）

## 2026-10-23 — WorkBuddy 日报 GitHub Pages 自动发布修复

- 根因确认：WorkBuddy 已生成 2026-10-20、2026-10-21 两份日报，但任务记录显示调用的是不存在的旧脚本 `/Users/liyanqiao/Documents/ChatGPT/AI/scripts/publishworkbuddynews.sh`，随后只发布到 WorkBuddy 自有站点，未同步 GitHub 仓库，因此公开 Pages 停在 2026-10-19。
- 已将 2026-10-20、2026-10-21 两份积压日报及刚生成的 2026-10-23 日报同步到 `site/ai-news-daily/`，报告数从 7 增至 10。同步器新增幂等 manifest、索引说明卡片移除、总览/日报返回导航注入，避免后续每次复制覆盖公开站定制。
- 发布脚本增加固定 PATH 和并发锁；新增 Codex 本地自动化“WorkBuddy 新闻 Pages 补推”，每天 09:30、10:30、11:30、12:30 补偿检查，有新日报才提交推送，无变化保持安静且不产生空提交。
- WorkBuddy 任务提示词已恢复正确的第六步，路径为 `/Users/liyanqiao/Documents/ChatGPT/AI自动化/scripts/publish_workbuddy_news.sh`，并要求命令失败时明确报错，不得误报 Pages 已更新。
- 验证：Python 37/37、Playwright 桌面/手机 18/18、shell 语法与 `git diff --check` 均通过。尝试的 LaunchAgent 因 macOS TCC 禁止后台 bash 访问“文稿”目录而退出 126，已卸载并改用具备项目权限的 Codex 本地自动化。提交 `166f81f`、`b24c9a3`、`4918c50` 已快进至 GitHub `main`；Actions run `39881984760` 的 `collect` 与 `deploy-dashboard` 均成功。公开索引已显示 2026-10-23，10 月 23 日报告返回 HTTP 200。

## 2026-10-20 — 04 新闻模块收敛为 WorkBuddy 日报

- 用户已授权直接提交并推送。主看板移除“产业新闻”和“AI 新闻预览（独立预览）”；新闻区域仅保留 WorkBuddy 的“AI 新闻日报 / 每日自动更新”入口，侧栏后续编号顺延为 Token 01 至 AI 研究前沿与模型能力 09。
- 删除旧 RSS 产业新闻采集器、独立预览转换器、预览页面/数据/测试及相应配置、契约、浏览器断言；日报同步与发布脚本仍独立保留。日报索引说明卡片已删除，先前的总览/日报返回链接保持。
- 不删除 `history/`、`site/data/` 或翻译缓存；`run_daily` 显式忽略旧 `news` manifest 条目，避免下次采集将它重新带回总览。
- 已通过 Python 37/37、Playwright 桌面/手机 18/18、静态契约、JS 语法与 Git 差异检查；提交 `0aaedd7` 已推送 `origin/main`。GitHub Actions `39361306807` 的 `collect` 与 `deploy-dashboard` 均成功，01 可据此验收公开页面。

## 2026-10-20 — 04 日报入口与返回导航本地调整

- 主看板侧栏 09 的导航文案改为“上市公司Capex”；WorkBuddy 日报卡片改为上方“AI 新闻日报”、下方“每日自动更新”，去除其下方分隔线，字号保持原有层级。
- `site/ai-news-daily/index.html` 左上新增“返回总览”；7 份历史日报均新增“返回 AI 新闻日报”。入口、归档与总览均使用相对路径，兼容 GitHub Pages 子路径。
- 已验证 Playwright 桌面/手机 24/24、`node --check site/app.js` 与 `git diff --check`；本地总览、日报索引与 2026-10-19 归档报告均已人工打开并核对返回链接。未改正式数据、WorkBuddy 自动化、`history/` 或翻译缓存，未提交、推送或发布，等待用户确认本地效果。

## 2026-10-16 — 01 财务看板 P0 已发布并完成线上验收

- 用户提供的评审文档按产品/数据需求建议处理，由 01 分派 02 数据、03 自动化发布预检、04 前端；P0 已完成，P1 仍受数据质量验收约束。仅选择性提交 6 个财务代码/测试文件为 `06b753f` 并推送公开 `main`；新闻预览、RSS、README、`site/index.html` 与本机 `history/`、`site/data/`、翻译缓存均未纳入提交或覆盖。
- 发布前复验：Python 44/44、Playwright 桌面/手机 22/22、静态契约、JS 语法及 Git 差异检查通过。GitHub Actions/Pages run `38918609312` 的 collect、deploy-dashboard 均成功，公开财务 JSON 与新版 `app.js` 已读取验证。
- 公开快照日期 2026-10-16：11 家公司、11 个统一指标、FY/TTM/Quarter/YTD 四种期间、11 条来源记录；8 家 FY 全指标 `ok`，NVDA、AMZN、TSM 为 `partial`，没有来源请求 `error`。全部 FY 已报告数值均可链接至 SEC 原件，已计算指标的同期输入一致。TTM 保持 N/A，不伪造滚动值。
- 后续：02 核对 NVDA、AMZN、TSM 原始申报（尤其 TSM 20-F/币种和自定义标签）并提出可审计映射方案；P1 公司 BABA、0700.HK、ANET、VRT 及 D&A、R&D、Net Debt、Guidance 先留在 BACKLOG，不直接纳入每日采集。GitHub Actions 目前提示 Node.js 20 弃用与 ubuntu-latest 即将迁移，03 后续评估工作流依赖版本。

## 2026-10-16 — 04 财务模块前端本地完成，待 01 联合验收

- 主表保留公司、CapEx/期间、Revenue/期间、OCF/期间、申报日与 SEC 原件；只增加 CapEx/Revenue 与 FCF 两个派生结果。公司详情按固定顺序展示 11 项统一指标（原有 3 项 + P0 8 项），每项含 Reported/Derived、独立期间、状态或缺失原因、公式、基础输入及可用的 SEC 原件链接。
- FY/TTM/Quarter/YTD 期间切换、产业链分组、CapEx YoY/强度/FCF 排序已接入 02 的 periods/metrics 契约。旧版 6 公司快照可降级展示原始事实并提示期间未统一；派生结果保持 N/A，不以旧值推算。手机端用详情弹层，桌面端用展开行。
- 已验证 `node --check site/app.js`、`git diff --check`、Playwright 桌面/手机全套 22/22（含新旧财务快照契约）。前端尚未提交或发布；真实 11 公司 SEC 快照需要 01 在 Actions 采集和 Pages 发布后验收。

## 2026-10-16 — 02 财务数据扩展本地完成，待 01 上线验收

- 配置已扩至 11 家（原 6 家 + ORCL、CRWV、TSM、AVGO、MU），每家保留产业链分组与准则说明。数据契约固定 FY/TTM/Quarter/YTD、11 个统一指标；FY 默认。每项保留独立期间、标准 taxonomy、SEC 申报链接、状态和缺失原因，派生项保留公式及基础事实审计。仅同期、同币种、可靠的 USD 全实体事实参与计算。
- edgartools 5.62.0 解析器已核对：FinancialFact 的 taxonomy 与未加前缀 concept 可能分开传递；后端兼容两种形式，支持标准 us-gaap/ifrs-full 和 10-K/10-Q/20-F/40-F。SEC 官方文档确认 Company Facts 仅聚合非自定义、全实体 XBRL；NVDA/AMZN 的旧标准 CapEx 标签不能代替当前数，自定义标签缺失也不等于未披露。TSM 配置的准则为 unknown，运行时由实际选中 FY 标准事实的 taxonomy 推断 US GAAP 或 IFRS；无可靠事实或混用则 unknown。只接受可证实的 USD 标准事实，不以 TWD 未注明汇率地换算。TTM 暂不推算，显示原因；负 OCF 的 CapEx/OCF 标为 N/M。
- 每家公司 SEC 请求失败仍保留公司行和 11 个统一空指标，异常消息不输出，避免泄露抓取身份；快照以 as_of 日期排除未来申报事实。此机未配置 SEC_USER_AGENT，故未做真实 SEC 自动抓取；仓库 Action Secret 已由 03 确认存在，发布后的真实采集须由 01 检查 11 行、来源/期间/公式。Python 全套 44/44、静态契约与差异检查通过。未修改本机历史快照/翻译缓存，未提交或推送。

## 2026-10-16 — 03 财务扩展发布链路预检

- 当前 `main`/`origin/main` 与实时远端 HEAD 均为 `9b7be302`；本机 `gh` 已登录仓库账户，具有 `repo`、`workflow` 权限。GitHub Secret 名称清单确认 `SEC_USER_AGENT` 存在，未读取值。
- 日报工作流 `collect.yml` 已向 `dashboard.run_daily --scope daily` 传入 `SEC_USER_AGENT`。采集器按 `config/ai_observatory.json` 的 `sec_companies` 遍历，写入 `site/data/ai-financials/latest.json` 和 manifest，工作流上传 `site/` 并由 `deploy-dashboard` 发布 Pages；扩到 11 家不需要改工作流。最近定时 run `38902658832` 的 collect、deploy-dashboard 均成功；公开 2026-10-16 财务 JSON 仍是 6 行/6 来源、`partial`。
- `.venv/bin/python scripts/check_contract.py` 通过。当前财务提取仅识别 10-K/10-Q；新增的 TSM 涉及 20-F 时须由 02 核对来源与口径。逐公司异常当前只记录来源 `error` 而不生成占位行，因此 11 家上线验收要检查完整公司行和逐指标缺失状态，不能只看 Actions 成功。
- 01 选择性提交含 `dashboard/**`、`config/**` 或 `site/**` 后，推送 `main` 会触发一次真实日报采集和 Pages 部署；需核验新 run 的 collect/deploy 成功、公开 JSON 11 家、同一字段契约与原件链接、manifest 状态及页面展示。03 未运行全量采集、未改工作流/脚本、未提交或推送。

## 本轮 AI 财务/研究前沿已发布并核验

- 用户已在 GitHub Actions 仓库 Secrets 配置 `SEC_USER_AGENT`（仅确认名称存在，未读取密钥）。仅选择性发布了两次提交：`51d5ab8`（模块接入）与 `9b7be30`（防止将过期标准 CapEx 标签展示为当前值）；RSS、新闻预览、README、`site/index.html`、`history/`、`site/data/` 和翻译缓存均未进入提交。
- 发布前验证：Python 37/37、静态数据契约、`node --check site/app.js` 与 Playwright 桌面/移动端 20/20。线上日报/Pages run `38663918177` 与纠正 run `38664718029` 的 collect、deploy-dashboard 均 success。
- 线上核验：导航已显示 09/10；`ai-frontier` 为 `ok`，50 条（30 条基准、20 篇论文）。`ai-financials` 为 `partial`，6 家公司；MSFT、GOOGL、META、AMD 显示同期标准 CapEx，NVDA、AMZN 因唯一标准标签分别停留在 2020、2017，被明确隐藏并将原始事实/SEC 原件链接保存于 `omitted_metrics`，不伪造最新 CapEx。

## 本轮 edgartools / Hugging Face 榜单接入（待 SEC 身份授权后发布）

- 本地安装：`edgartools==5.62.0` 已进入项目 `.venv`，源码发行包位于根目录 `edgartools/`；`huggingface/leaderboards` 的固定版本文档仓库位于根目录 `leaderboards/`。完整 GitHub edgartools 归档下载持续中断，故本地根目录保存官方 PyPI 源码发行包而非完整 Git 历史；两个上游目录均被忽略，不进入 Pages 或项目源码提交。
- 新增日报模块 `ai-financials`、`ai-frontier`，沿用现有 GitHub Actions → `site/data` JSON → 主看板按需加载；新增侧边栏 09/10、财务指标与 SEC 原件链接、官方榜单原始分/verified/排名变化、HF Daily Papers 原文与实际发布时间，并提供逐源状态。资本开支明确为公司整体 PPE 现金支出，不假称 AI 专项；榜单不混算不同基准，论文不伪造中文翻译或当日新鲜度。
- 真实 HF API 试跑成功：SWE-bench Verified、Humanity’s Last Exam 和 Daily Papers 均返回 `ok`，小样本共 33 条。SEC 自动请求需要带可联系的抓取身份；安全审查拒绝未经授权将现有个人 Git 邮箱发送给 SEC，已删除该默认值。工作流只读取待配置的 `secrets.SEC_USER_AGENT`；缺失时财务模块标记 `unavailable`，不得宣称已实盘验证或已上线。
- 验证：Python 36/36、Playwright 桌面/手机 20/20、静态契约、JS 语法、`git diff --check` 与本地 `pip check` 通过。未运行会覆盖正式快照的完整日报；未更改 `history/`、`site/data/` 或翻译缓存。现阶段未提交、推送或发布，现有 RSS/新闻预览工作区改动保持原样。
- 下一步：用户明确指定/批准用于 SEC 的联系身份（名称 + 邮箱），由仓库管理员设为 `SEC_USER_AGENT` Secret；真实采集成功后仅暂存本轮模块文件与需发布的前端/工作流改动，复跑测试并发布 Pages。不要把既有新闻预览与 RSS 改动带入本次提交。

## 本轮存储价格单位显示修复

- 存储硬件价格的“类别价格基准”表对可比单位以 `USD` 开头的最低、平均、中位和最高值，统一显示 `$` 前缀，与 GPU 云报价页一致；例如 SSD 的 `USD/TB` 显示为 `$133`，HBM 租赁代理显示为 `$0.0102`。
- `可比单位` 列继续保留完整口径（如 `USD/TB`、`USD per HBM-GB·hour`）。未来出现非 USD 数据时不强加 `$`，仍由该列明确其币种或其他单位，避免货币误标。
- 变更范围为 `site/app.js` 与 `tests/browser/dashboard.spec.js`；完整 Playwright 桌面/手机 18/18、`node --check site/app.js` 和 `git diff --check` 均通过。已单独提交并推送为 `8f39820`；Actions/Pages run `38519457452` 成功，公开 `app.js` 与存储页均已核验 HTTP 200。不触碰 `history/`、`site/data/`、翻译缓存或现有 RSS/预览工作区改动。

## 本轮筛选修复与价格页优化

- Hugging Face 分类筛选已修复：通用筛选不再猜测行内第一个分类字段，各页面显式指定自身字段；同时复核并固定产业新闻、模型 API、GPU、存储和 GitHub 的分类映射，避免同类错配。
- 模型 API、GPU 云报价、存储硬件价格默认改为“基准概览”，分别展示价格分位代表、按 GPU/计费方式聚合的最低/平均/中位/最高价、按存储类别与可比单位聚合的基准；保留“全部明细”切换。
- 三个价格页的统计卡改为当前筛选结果的平均值、中位数或关键基准。SSD 按 USD/TB 比较，HBM 明确为含计算成本的租赁代理，不混算不同单位。
- 模型 API 散点统一缩为 3.2px，悬停、点击或键盘聚焦时突出当前点并显示模型名、输入价和输出价；搜索框和所有分类下拉框统一为 38px 高。
- 验证：Python 31/31、Playwright 桌面/手机 18/18、静态数据契约、`node --check site/app.js`、`bash -n scripts/run-local.sh` 与 `git diff --check` 全部通过。仅 `site/app.js`、`site/styles.css`、`tests/browser/dashboard.spec.js` 已提交为 `9a052de` 并推送至 `main`；日报/Pages run `38424369852` 成功，公开页面及 `app.js` 均返回 HTTP 200。未触碰 `history/`、`site/data/` 或翻译缓存，RSS 与新闻预览等工作区改动未进入提交。

## 本轮 X 看板更新

- 桌面分类菜单已修复：一级菜单必要时向左对齐，二级账号菜单按视口剩余空间自动向左/向右展开，并限制宽度；页面不因菜单产生横向滚动。修复已单独提交本地 `41b911f`。
- 用户已通过 GitHub Desktop 成功推送 3 个提交；GitHub Actions run 28 的 `collect` 与 `deploy-dashboard` 均成功，公开 Pages 返回 HTTP 200。
- 近七天采集与前端交互已经完成；最新快照为 2026-10-10 12:33，135 条帖子，38/50 个账号有动态、12 个账号明确本期无动态，50/50 查询成功。Tibo `@thsottiaux` 近七天有 5 条。
- 分类菜单按悬停显示二级账号菜单；切换一级分类时替换右侧账号列表。具体账号视图展示该账号的所有本期帖子，卡片不显示一级分类。
- 动态 JSON 发布副本位于 `site/x-watch/latest.json`；本机采集结果与历史快照仍分别保留于 `site/data/` 和 `history/`。采集严格限近七天，无 30 天回溯。
- 已公开部署至 `https://liyanqiao0106-max.github.io/hf-trend-snapshots/#x-watch`；公开 JSON 已核对为 50 个账号、135 条帖子、38 个有动态账号、12 个本期无动态账号。

## 当前基线

- 权威代码与工作流：GitHub `liyanqiao0106-max/hf-trend-snapshots` 的 `main`。
- GitHub `main` 已包含排期提交 `7d5d821`、X 看板提交 `49d8992`、菜单修复 `41b911f` 和看板筛选/价格基准优化 `9a052de`；本机与 `origin/main` 已同步。
- 本机保留状态：`history/`、`history/translation-cache.json`、`site/data/`；恢复后 SHA-256 校验通过。
- GitHub Actions 排期已更新为每日 15:48（上海时间）、每周一 07:11。
- 看板发布：GitHub Pages 静态站点；前端仅读取已发布 JSON，不在浏览器暴露密钥。
- 本机主看板已增加“X 账号动态 08”；X 快照依赖本机 Chrome/X 登录态，只能通过 `collect-x` 本地刷新。当前快照已公开发布。

## 当前风险与阻塞

## 2026-10-20 — WorkBuddy 每日 AI 新闻接入 Pages

- 状态：本地接入完成，待提交并推送后线上验收。
- 结论：保留 WorkBuddy 每日独立 HTML 作为历史归档；新增桥接同步脚本，将 `ai-news-board/index.html` 与 `reports/*.html` 发布到 `site/ai-news-daily/`。不改 WorkBuddy 生成器为单一不断增长的 HTML，避免历史回溯和故障恢复变差。
- 已验证：从 `/Users/liyanqiao/Documents/WorkBuddy/AI每日新闻/ai-news-board` 同步 7 份报告；桥接单元测试、`git diff --check`、shell 语法检查通过。
- 自动化：WorkBuddy 每日 08:50 生成后调用 `scripts/publish_workbuddy_news.sh`，脚本只暂存新闻接入目录，提交并推送 `main`；Pages 沿用现有 push 部署链路。
- 风险：GitHub Pages 无法读取本机 WorkBuddy 目录，必须由本机任务负责同步和推送；不能把 WorkBuddy 状态目录、Cookie、密钥或 `.env` 带入仓库。

1. 本地与远端 `main` 已同步至 `9a052de`，公开 Pages 已更新。`config/sources.json` 的 RSS 修改及新闻预览等仍是未提交工作区改动，未包含在本次发布中。
2. Mac `scripts/run-local.sh` 已恢复并通过 31 项 Python 测试；Windows 启动脚本仍未恢复到权威源码。
3. 现有看板与独立新闻预览共 18 项 Playwright 浏览器测试（桌面与移动端）、前端语法与静态数据契约已通过。
4. GitHub Actions、Pages 和三条工作流的公开状态已于 2026-10-09 核验；仓库 Secrets 名称列表需要具有仓库管理权限的账户在 Settings 中复核（当前只读匿名接口返回 401，未读取任何密钥）。
5. 最近一次定时日报虽成功，但在北京时间约 19:16 才启动，明显晚于配置的 12:00；需持续观察 GitHub 定时调度延迟。
6. 用户已确认两个新官方来源暂时保持当前翻译优先级。英文新闻按 `config/sources.json` 顺序消耗 MyMemory 滚动 24 小时 3000 字符额度；当前定向样本合计约 505 字符，未触发额度问题，上线后观察 `translation_pending` 和各来源实际入选情况。
7. `ai-news-daily` 的 `package.json`/README 声明 MIT，但提交 `bb88b501` 没有 LICENSE/COPYING/NOTICE，GitHub License API 也返回 404；正式站点不得复用其源码或 UI。锁定依赖审计为 2 critical、6 high、2 moderate，主要涉及旧版 axios、protobufjs、sharp 与 onnxruntime 链路；页面模板还直接插入 RSS 标题/摘要而未统一 HTML 转义。长期接入前必须升级或替换依赖，并由 02/04 独立实现安全的数据与渲染边界。
8. X 动态无法由无登录的 GitHub Actions 可靠采集；当前仅在本机刷新。公开 Pages 静态快照由用户明确授权发布；不得上传 Chrome/X Cookie 或凭据。

## 进行中

- 01：排期、X 看板及本轮筛选/价格优化均已推送；继续保持 RSS 配置和新闻预览不进入发布提交。
- 03：本轮日报/Pages run `38424369852` 已成功；周报未被前端路径变更触发，最近一次定时 run `38195220275` 成功。RSS 改动仍需独立发布决策，仓库 Secrets 名称清单仍待有管理权限的账户复核。
- 04：独立 HTML 预览页、看板入口和浏览器验证已完成；01 本地验收通过。预览仍为一次静态样本，未接入正式日报或部署。

## 最近完成

- 01：2026-10-10 将用户上传的 `AI_Industry_X_Watchlist_50_Accounts.txt` 精确转换为正式 `config/x_watchlist.json`：50 个唯一账号顺序与上传文件一致，含 21 个官方账号、10 位领导者、15 位研究员/工程师、4 个产业研究账号及 15 个优先账号；Tibo 为 `@thsottiaux`。新增 `dashboard.x_watch` 本机采集器与 `scripts/run-local.sh collect-x`，侧边栏新增“X 账号动态”而非独立页面，支持关键词、四类账号和优先子集筛选。真实查询 50/50 成功；发现高频回复会挤占分组额度后，正式查询排除回复及原生转帖，最终得到 128 条去重近七天主动发布动态、29 个账号有返回、65 条来自优先账号、Tibo 4 条；112 条 oEmbed 复核，16 条保留 Chrome 页面正文。Python 31/31、Playwright 桌面/手机 12/12、静态契约、JS/shell 语法和差异检查通过；真实数据额外在桌面与手机验证 128 条、Tibo 4 条、优先动态 65 条，无控制台错误。截图位于 `work/tmp/x-watch-dashboard-{desktop,mobile}.png`，本机主看板运行在 `http://127.0.0.1:8000/#x-watch`。未提交、推送或部署；X 刷新仍要求本机 Chrome/X 登录，不进入 GitHub Actions。
- 01：2026-10-09 用户明确授权全局 OpenCLI 与主 Chrome/X 登录态，并完成官方 Browser Bridge 安装、X 登录及全局命令软链接。OpenCLI 1.8.8 与扩展 1.0.24 已连接；采集器避开超时的 `twitter search` 主动内部 API 适配器，改为普通 X 搜索页面 DOM 只读提取及公开 oEmbed 复核。64 个账号按 8 组查询近 7 天，每组最多 40 条，得到 37 个账号的 290 条去重动态（251 条 oEmbed 复核成功、39 条保留浏览器正文），不是完整时间线。独立 HTML 位于 `work/tmp/ai-influence-digest-preview/public/index.html`，本机 `http://127.0.0.1:8877/` 已打开，默认 8 条按 skill 标准整理的中文精选，另有全部动态及 15 条规则候选。搜索、账号筛选、排序、精选稿、重读与选择持久化验证通过，页面无控制台错误，桌面/窄屏截图核验、10 项数据断言、JS 与 shell 语法通过。缓存/状态/产物均在 `work/`，仅全局命令入口在 `/usr/local/bin/opencli`；未接入正式看板、Actions 或全局 Codex skills，未提交或发布。
- 01：2026-10-09 在 `work/tmp/ai-influence-digest-upstream` 与 `work/python-runtime/ai-influence-digest` 隔离安装 `koffuxu/ai-influence-digest`（源码归档提交 `dd9c31a`），未接入现有项目。按 64 个账号、7 天窗口运行上游公开 `syndication` 路径；X 返回 429/SSL 中断，真实本周候选为 0。随后仅用 4 条公开历史 URL 走上游 `oEmbed` 种子模式，成功读取 2 条并生成历史演示 Markdown、HTML 与 PNG 海报；演示明确标注不代表本周结果。正式体验需配置 OpenCLI Browser Bridge 与专用 Chrome/X 副号 Profile，当前未安装全局 `opencli`、未访问主 Chrome Profile。
- 01：2026-10-09 验收 04 独立预览页。复核原创页面、相对数据路径、正式新闻栏目隔离、外部文本/URL 安全、新鲜度重算、分类重读状态及桌面/手机截图；本地 HTML 和 JSON 均返回 HTTP 200，页面显示 61 条。筛选重读问题已由 04 修复并通过桌面/手机 6 项预览回归。结论：本地预览验收通过，尚不代表正式数据质量或上线授权。
- 04：2026-10-09 原创完成 `site/news-preview/` 独立页面与 `site/index.html` 入口，读取 02 的独立 JSON，实际展示 61 条、4 类；页面标明规则降级、未翻译、逐源状态未知和发布时间未经核实，按打开时间重算 36 小时时效。桌面/手机浏览器测试 10/10、Python 29/29、静态契约与 JS 语法通过；两张截图保存于 `work/tmp/ai-news-preview-{desktop,mobile}.png`。本机只读预览 `http://127.0.0.1:8000/news-preview/index.html` 可访问；未提交、推送或部署。
- 02：2026-10-09 完成 `dashboard/preview_ai_news_daily.py`、4 项预览契约测试及独立静态预览 JSON `site/preview-data/ai-news-daily/latest.json`。基于 03 的隔离产物转换 61 条，状态为 `partial`（上游规则分类）；29 项 Python 测试、静态契约和差异检查通过。未改正式日报、`history/`、`site/data/`、翻译缓存，未提交或发布。
- 03：2026-10-09 在 `work/tmp/ai-news-daily-upstream` 隔离安装并运行上游 RSS→处理→静态页面流水线。采集 70 个源得到 211 篇候选；模型下载失败后降级为规则处理，新增处理 61 篇、隔离数据共 1742 篇；生成 17 个日期的静态数据，当天页面展示 61 篇、4 个分类。页面已在 `http://127.0.0.1:8765/` 实际打开。通过本地安全开关禁用 15 天滚动清理，未运行 workflow、Git 提交/强推或部署，`history/`、`site/data/` 和翻译缓存无改动。
- 01：2026-10-09 将日报和周报排期改为上海时间每日 15:48、每周一 07:11，核对 UTC 换算；25 项 Python 测试、静态契约和 JS 语法检查通过。仅排期相关六个文件进入本地提交 `7d5d821`，未包含 02 的 RSS 改动。
- 01：2026-10-09 记录用户决策：Google DeepMind 与 Together AI Blog 暂时保持当前顺序和翻译优先级，以真实日报数据判断是否需要公平额度分配。
- 01：2026-10-09 验收 Google DeepMind 与 Together AI Blog RSS 接入。官方域名、RSS XML、七日筛选、翻译额度、失败降级、日报工作流、JSON 契约与 HTML 渲染链路均通过审查；25 项 Python 测试、静态契约与 `git diff --check` 通过。结论为“本地验收通过，满足提交前条件；尚未授权提交或发布”。
- 02：2026-10-09 评估 `ai-news-daily`、TrendRadar、`ai-influence-digest`，按现有架构适配度排序；从 `ai-news-daily` 来源清单独立验证并接入 Google DeepMind、Together AI Blog 两个官方 RSS。现有日报、JSON 快照与新闻页面无需改动；25 项 Python 测试和静态契约检查通过。尚未运行会改写本地快照的真实全量采集，也尚未提交或部署。
- 03：2026-10-09 只读核验线上自动化：三条 workflow 均 active 且都配置 `workflow_dispatch`；最近日报、周报和 Pages 部署均成功，公开 Pages 站点返回 HTTP 200。已确认新增 RSS 会复用既有日报、Release 归档及 Pages 发布路径；其配置文件合入 `main` 将自动触发一次真实日报发布。
- 01：2026-10-09 安全恢复线上 Git 历史、远程关联和工作流。
- 01：2026-10-09 验证所有本地历史与最新快照未被覆盖。
- 03：2026-10-09 从安全迁移备份恢复兼容的 Mac 本地启动脚本 `scripts/run-local.sh`；临时目录与工具缓存均指向 `work/`，已完成 Shell 静态语法验证。
- 01：2026-10-09 在项目内 `.venv` 安装 Python 依赖，运行 24 项 Python 测试、前端 JS 语法检查和静态数据契约检查，全部通过。
- 01：2026-10-09 在项目内安装锁定的 Node 依赖与 Playwright Chromium，4 项桌面和移动端浏览器测试全部通过。
