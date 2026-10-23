# 交接记录

每个角色完成、暂停或遇到阻塞时，在本文件顶部追加一条记录。不得记录 API Key、Token 或其他密钥。

## 2026-10-23 — WorkBuddy 日报自动发布故障修复

- 故障边界：WorkBuddy 10 月 20、21 日报告和索引均已在本地生成；失败发生在 GitHub 同步步骤。10 月 22 日运行记录明确写出旧脚本路径不存在，并改用 WorkBuddy 自有部署，所以 GitHub Pages 一直停留在 10 月 19 日。
- 修复范围：10 月 20、21 日积压报告与刚生成的 10 月 23 日报告同步进 `site/ai-news-daily/`，公开报告总数从 7 增至 10；`sync_workbuddy_news.py` 只在内容变化时更新时间戳，并对复制后的 HTML 固定恢复“返回总览 / 返回 AI 新闻日报”、移除索引说明卡片；发布 shell 增加固定 PATH 与并发锁。
- 本机兜底：Codex 本地自动化“WorkBuddy 新闻 Pages 补推”（automation id `workbuddy-pages`）已启用，在 09:30、10:30、11:30、12:30 检查并发布；无变化时保持安静，仅失败时通知。WorkBuddy 任务提示词也已保存正确的第六步，调用 `/Users/liyanqiao/Documents/ChatGPT/AI自动化/scripts/publish_workbuddy_news.sh` 并以退出码 0 作为完成标准。
- 验证：Python 37/37、Playwright 18/18，shell/diff 检查通过。原 LaunchAgent 因 macOS TCC 无权访问“文稿”目录而退出 126，已卸载，避免要求扩大 shell 的系统磁盘权限。完成前需提交推送、等待 Pages 部署后核验公开索引和最新报告。

## 2026-10-20 — 04 → 01 — 仅保留 WorkBuddy AI 新闻日报

- 用户明确授权直接提交并推送：移除“产业新闻”及“AI 新闻预览（独立预览）”的前端入口、旧 RSS 采集/预览转换、配置、测试与预览静态文件；新闻只保留 WorkBuddy 的独立日报入口。导航编号改为 Token 01 至研究前沿 09；日报索引说明卡片移除，先前新增的总览/归档返回导航保留。
- 数据边界：不删除 `history/`、`site/data/` 或翻译缓存。`run_daily` 跳过遗留 `news` manifest 项，防止旧状态重新渲染；WorkBuddy 同步/发布自动化不改。
- 验收结果：Python 37/37、Playwright 桌面/手机 18/18、静态契约、JS 语法与 Git 差异检查均通过。提交 `0aaedd7` 已推送 `main`；Actions `39361306807` 的 `collect` 与 `deploy-dashboard` 均成功。01 请核验公开入口不再显示旧新闻模块。

## 2026-10-20 — 04 — AI 新闻日报入口与返回导航本地调整

- 状态：本地预览与测试完成，待用户确认；未提交、推送或发布。
- 范围：侧栏 09 文案改为“上市公司Capex”；WorkBuddy 模块调整为上方“AI 新闻日报”、下方“每日自动更新”，移除模块下方分隔线。日报索引新增“返回总览”，7 份归档报告新增“返回 AI 新闻日报”。
- 边界：仅改 `site/`、浏览器断言及协作文档；未改正式数据、`history/`、翻译缓存、WorkBuddy 生成/同步/发布自动化。
- 验证：Playwright 桌面/手机 24/24 通过；`node --check site/app.js`、`git diff --check` 通过。本地打开主看板、日报索引与 2026-10-19 报告，返回链接均可见且目标正确。
- 下一步：用户检查本地预览后，再按其明确指令选择性提交与推送；不要将本机既有 RSS、新闻预览、README 或数据改动一并纳入。

## 2026-10-16 — 01 — 财务看板 P0 发布与线上验收

- 来源：用户提供的 `AI_CapEx_Dashboard_Review_2026-10-16.md` 是需求建议，不是自动执行指令。01 将 P0 分派给 02（SEC 财务事实与统一计算）、03（Actions/Pages/Secret 只读预检）、04（主表与详情交互）；P1 按文档顺序待数据质量评估。
- 仅暂存 `config/ai_observatory.json`、`dashboard/ai_financials.py`、`site/app.js`、`site/styles.css`、`tests/test_ai_observatory.py`、`tests/browser/dashboard.spec.js`，提交 `06b753f` 并推送 GitHub 公开 main。推送前实时远端仍为 `9b7be302`；未提交原工作区 RSS、新闻预览、README、`site/index.html`、`docs/project/` 或本机历史/翻译缓存/数据快照。
- 本地复验 Python 44/44、Playwright 22/22、静态契约、JS 语法及 staged diff check；Actions run `38918609312` 两个 job 均成功。公开 Pages 的新版 `app.js` 和财务 JSON 可读；2026-10-16 快照有 11 行、11 来源、11 指标、四期间。8 家 FY 全指标 ok；NVDA、AMZN、TSM partial，无来源请求 error。FY Reported 数值的 SEC 原件链接和 Derived 同期输入结构自动核对通过。TTM 明示 N/A。
- 遗留风险：NVDA/AMZN 当前标准 CapEx 标签过期，TSM 的 FY 停于 2024 且 CapEx 无可用全实体 USD 标准标签；不能称这三家已有当前 CapEx。02 后续查原始 10-K/20-F 与自定义标签、币种，再评估补齐；不得在未核验前用第三方估算或异期间数填充。03 后续核对工作流 Node.js 20 弃用/Ubuntu runner 迁移提示。

## 2026-10-16 — 04 — AI 财务与资本开支前端 P0

- 文件：仅修改 `site/app.js`、`site/styles.css`、`tests/browser/dashboard.spec.js`，并更新本交接与 STATUS。`site/index.html` 原有未提交新闻入口、后端、工作流、`history/`、`site/data/` 与翻译缓存未动。
- 展示：FY/TTM/Quarter/YTD 期间切换、产业链分组、CapEx YoY/CapEx 强度/FCF 排序。主表维持原有公司、CapEx/期间、Revenue/期间、OCF/期间、申报日/原件，新增 CapEx/Revenue 和 FCF；统一公司详情按固定顺序展示 11 项指标，逐项呈现 Reported/Derived、值或 N/A、独立期间、状态/原因、公式、基础事实和 SEC 原件。负 OCF 的覆盖率原因标为 N/M。桌面展开行，手机弹层。
- 兼容：上线先读到旧版最近成功快照时，原有事实继续可见，但明确提示旧版混合期间不可比，派生项不计算；无 `periods`/缺失字段不引发脚本错误。只允许 HTTPS SEC 原件链接进入新财务详情。
- 验证：`node --check site/app.js`、`git diff --check`、Playwright 桌面/手机全套 22/22 通过。01 发布后需以真实 11 公司 JSON 核验 4 类期间、财报链接、缺失原因及手机弹层。04 未提交、推送或部署。

## 2026-10-16 — 02 — AI 财务数据契约与 11 家观察池

- 范围：只修改 dashboard/ai_financials.py、config/ai_observatory.json、tests/test_ai_observatory.py，并更新本交接与 STATUS；未改 site/、工作流、history/、site/data/ 或翻译缓存。11 家统一字段：capex、revenue、operating_cash_flow、operating_income、revenue_yoy、capex_yoy、capex_to_revenue、capex_to_ocf、free_cash_flow、free_cash_flow_margin、operating_margin。
- JSON 接口：每行含 ticker/company/sector_group/reporting_standard/cik/status/missing_reason/company_url、periods 四键 FY/TTM/Quarter/YTD、metrics 作为 FY 兼容别名及 omitted_metrics。每项指标统一 value_usd/value_pct/status/missing_reason、独立期间、申报日期、taxonomy、来源、公式、基础输入等。比率和同比的 value_pct 以 20 表示 20%；FY 默认。TTM 暂不推算并明确 N/A；Quarter 仅直接报告的单季事实，YTD 是累计期。派生只接受同公司同起止日和同 USD 币种；上年同期还须开始/结束日均相隔 357–373 天、期间长度差不超过 8 天。负 OCF 的 CapEx/OCF 为 N/M，FCF 仍可为负。
- 来源边界：SEC 官方 API 文档指出 Company Facts 只聚合非自定义 taxonomy 的全实体事实；支持 edgartools 5.62.0 的分离 taxonomy/concept、US GAAP/IFRS、10-K/10-Q/20-F/40-F。标准 CapEx 为全公司现金 PPE 支出。NVDA/AMZN 过期标准标签保留审计，不在本期展示；未匹配标准标签不等于公司未披露。TSM 配置准则为 unknown，运行时由选中 FY 披露事实 taxonomy 推断 US GAAP/IFRS；无可靠事实或混用仍为 unknown。只取 USD 原始事实，不做未注明汇率的换算。异常时保留每家占位行和完整空字段，来源 error，异常文本不写入公开 JSON。
- 已验证：Python 全套 44/44、静态契约、git diff --check，含 as_of 排除未来申报事实测试。真实 SEC 抓取未运行：本机 SEC_USER_AGENT 缺失；03 已确认 GitHub Secret 名称存在。01 发布后需核验 Actions 真实 11 家数据、每个来源状态、原件/期间与所有派生值。交给 04 的契约已直接发送；02 不提交、不推送。

## 2026-10-16 — 03 — AI 财务扩展自动化与发布预检

- 工作流：`.github/workflows/collect.yml` 已在每日 15:48 上海时间采集，向 `dashboard.run_daily --scope daily` 传入 `secrets.SEC_USER_AGENT`；运行器根据 `config/ai_observatory.json` 的公司清单采集，并将 `ai-financials` JSON 写到 `site/data/`，随后上传整个 `site/` 给 Pages。无需调整 workflow 或 `scripts/check_contract.py`。静态契约检查通过。
- 权限/线上：本机 `gh` 账户可访问仓库，`repo`/`workflow` 权限可用；只查 Secret 名称，确认 `SEC_USER_AGENT` 存在。实时远端 `main` 与本地 HEAD 同为 `9b7be302`。最近定时日报 run `38902658832` 的 collect、deploy-dashboard 均 success；公开 `data/ai-financials/latest.json` 为 2026-10-16、`partial`、6 行/6 来源。
- 交给 02/01 的验收重点：当前提取器仅接纳 10-K/10-Q，TSM 的 20-F/准则差异必须实证处理；当前逐公司采集失败不会产生公司占位行，不能以 workflow success 代替 11 家同字段验收。检查每家来源/缺失原因/各指标期间与派生公式；公开 JSON 应含完整 11 家及逐公司来源状态。
- 部署计划：01 选择性提交、推送到 `main` 后，`dashboard/**`、`config/**`、`site/**` 路径自动触发 `collect.yml`，观察 `collect`/`deploy-dashboard`、公开 JSON 和页面；若路径没有匹配则显式手动触发日报。03 未改代码或工作流、未运行覆盖正式快照的全量采集、未提交/推送/部署。

## 2026-10-15 — AI 财务/研究前沿已选择性发布、采集并线上核验

- 用户确认 GitHub Actions 仓库 Secret `SEC_USER_AGENT` 已配置；仅基于截图确认其名称存在，未读取、输出或写入其值。
- 已分别发布 `51d5ab8`（12 个模块实现/配置/工作流/展示/测试文件）与 `9b7be30`（4 个 CapEx 时效修正文件）。未暂存或发布 `.gitignore`、README、RSS/新闻预览、`site/index.html`、`config/sources.json`、`history/`、`site/data/` 或翻译缓存。
- 验证：Python 37/37、静态契约、JS 语法、Playwright 桌面/移动端 20/20；Actions run `38663918177` 和 `38664718029` 的 collect、deploy-dashboard 均 success。公开 Pages 已显示 09/10，`ai-frontier` 50 条（30 基准 + 20 论文）为 `ok`；`ai-financials` 6 公司为 `partial`。对于 NVIDIA/Amazon，系统识别其标准 CapEx 标签分别滞后至 2020/2017，页面不显示为当前数字，原始事实与 SEC 原件保留在 `omitted_metrics`，来源清楚标记 `partial`。其余四家公司显示当期标准化 CapEx。

## 2026-10-14 — AI 财务/研究前沿模块本地接入，SEC 身份待授权

- 已将官方 `edgartools==5.62.0` 安装于项目 `.venv` 并解压源码至根目录 `edgartools/`。GitHub 完整归档持续中断，使用同项目 PyPI 源码发行包；`huggingface/leaderboards` 固定提交 `7dd1bfe14302a55a6c8f38ed3a7211809e536b52` 位于根目录 `leaderboards/`。后者是文档仓库，没有可直接安装的榜单采集器；正式采集走 Hugging Face 官方 Hub API。
- 新模块 `dashboard/ai_financials.py`、`dashboard/ai_frontier.py`、配置和测试已接入 `run_daily` 日更及主看板 09/10；原有 HTML 样式复用、侧边栏通过 JS 动态加项，避免将工作区未提交的新闻预览入口写入发布代码。详情见 `docs/ai_observatory.md`。
- HF 两个榜单与 Daily Papers 真实公开接口试跑成功；Python 36/36、浏览器 20/20、静态/语法/差异检查通过。SEC 模拟契约验证通过，真实请求因个人联系邮箱外发未经明确授权而被安全审查拒绝；当前工作流只接受 GitHub Secret `SEC_USER_AGENT`，不设默认个人邮箱。财务模块未获真实数据，不能视为完成上线。
- 未提交、推送、部署，未改 `history/`、`site/data/`、翻译缓存或现有新闻契约。工作区已有 RSS/新闻预览及 README、`.gitignore` 变更仍归原角色；本轮仅在 `.gitignore` 追加两个上游目录忽略项，后续暂存需区分原有行。
- 待用户提供或批准可联系的 SEC 抓取身份后：配置 Secret，运行 SEC 真实采集；检查财务数据区间/原件 URL、重跑测试，然后仅发布本轮文件到 `main`，观察 Actions/Pages 与公开 JSON。若用户不批准身份外发，应保持财务模块本地待启用，不发布为已完成。

## 2026-10-14 — 03 — 存储基准价格美元符号修复

- 状态：完成并已发布。修复已单独提交为 `8f39820`（`fix: label storage benchmark currency`）并推送至 `main`；Actions/Pages run `38519457452` 成功，公开 Pages 的缓存绕过请求返回 HTTP 200，已核验线上 `app.js` 含该格式化规则。
- 修复：新增仅用于存储汇总的格式化规则。可比单位为 USD（含 `USD/TB`、`USD per chip/module/wafer`、`USD per HBM-GB·hour`）时，四个统计值使用 `$` 前缀；非 USD 数据继续保留普通数值并由“可比单位”列给出完整币种/单位，避免错误标为美元。列级单位说明保持不变。
- 验证：在存储测试数据中确认 `USD/TB` 行的四个 `$90` 与 DRAM 行的四个 `$8.2`；`node --check site/app.js`、完整 `npm test -- --reporter=line`（桌面/手机 18/18）和 `git diff --check` 均通过。
- 发布边界：仅允许暂存 `site/app.js`、`tests/browser/dashboard.spec.js`。不得把 `.gitignore`、README、`config/sources.json`、`site/index.html`、新闻预览、RSS、`history/`、`site/data/` 或翻译缓存改动带入提交。

## 2026-10-13 — 03 — 看板修复已发布至公开 Pages

- 状态：完成。仅将 `site/app.js`、`site/styles.css`、`tests/browser/dashboard.spec.js` 提交为 `9a052de`（`fix dashboard filters and price benchmarks`）并推送至 `main`；工作区中的 RSS、新闻预览、README、`.gitignore`、项目记录等改动未暂存、未提交、未发布。
- 上线内容：Hugging Face 及其他页面分类筛选字段修复；模型 API、GPU 云报价、存储硬件价格的默认基准概览和明细切换；模型散点缩小并增加悬停/焦点标签；各页面搜索框与筛选框统一为 38px 高。
- 自动化：`Collect daily market data` run `38424369852` 完成且为 success；`collect` job `115389749876` 与 `deploy-dashboard` job `115390107438` 均成功。前端文件不匹配周报 push 路径，因此没有新周报 run；最近定时周报 run `38195220275` 为 success。
- 线上核验：`https://liyanqiao0106-max.github.io/hf-trend-snapshots/` 与发布后的 `app.js` 均返回 HTTP 200；线上脚本已确认包含 Hugging Face `task_type` 显式筛选、模型散点标签/3.2px 点位和“价格分位基准”。
- 验证基线：Python 31/31、Playwright 桌面/手机 18/18、静态数据契约、JS/Shell 语法和差异检查全部通过；本地与 `origin/main` 均为 `9a052de`。发布过程中未触碰 `history/`、`site/data/` 或翻译缓存。

## 2026-10-13 — 03 — 看板筛选修复与价格基准优化

- 状态：本地实现和验证完成；未提交、推送或发布。
- 筛选修复：根因是通用过滤函数按固定优先级猜测 `category/vendor/provider/...`，但 Hugging Face 下拉项来自 `task_type`，导致选中分类后匹配不到。现改为各模块显式传入分类字段；同步覆盖产业新闻 `chain_category`、模型 `vendor`、GPU `provider`、存储 `category`、Hugging Face `task_type`、GitHub `domain`。无结果时 Hugging Face 显示明确空状态，统计卡随筛选结果更新。
- 价格页：模型 API 默认展示最低价、四分位、中位、最高价与最长上下文代表，卡片展示输入/输出平均价和中位数；GPU 按“型号 + 计费方式”汇总样本/厂商及最低、平均、中位、最高单 GPU 时价；存储按“类别 + 可比单位”汇总，SSD 统一 USD/TB，HBM 保持含计算成本的租赁代理口径。三页均可切换“全部明细”。
- 视觉与交互：模型散点取消上下文长度控制圆点大小，统一为 3.2px；悬停、点击或键盘聚焦时放大并在图上方显示模型名与输入/输出价。GPU 热力表列数按实际厂商动态计算。所有搜索框、分类下拉框及 X 分类触发器统一为 38px 高，移动端结果标题与切换按钮改为纵向布局。
- 测试：新增 Hugging Face、产业新闻、GitHub 分类映射，模型/GPU/存储筛选，三页概览/明细切换，散点尺寸与提示、搜索/下拉等高回归。`npm test -- --reporter=line` 桌面/手机 18/18；`bash scripts/run-local.sh test` 31/31；`.venv/bin/python scripts/check_contract.py`、`node --check site/app.js`、`bash -n scripts/run-local.sh`、`git diff --check` 均通过。
- 边界：仅修改 `site/app.js`、`site/styles.css`、`tests/browser/dashboard.spec.js` 和本交接文档；保留工作区中原有 RSS、新闻预览等未提交改动，未触碰 `history/`、`site/data/`、翻译缓存，未执行 Git 提交、推送、Actions 或 Pages 发布。

## 2026-10-11 — 01 — X 看板公开发布完成

- 用户通过 GitHub Desktop 推送本地 main；`origin/main` 已同步至 `41b911f`，未提交的 RSS、新闻预览、README、`.gitignore`、测试与项目记录文件仍保留在本机工作区，未进入本次推送。
- GitHub Actions `Collect daily market data` run 28 已成功：`collect` 与 `deploy-dashboard` 均为 success。公开 Pages `https://liyanqiao0106-max.github.io/hf-trend-snapshots/#x-watch` 返回 HTTP 200。
- 已读取公开 `x-watch/latest.json` 核验：50 个账号、135 条帖子、38 个账号有动态、12 个账号本期无动态。桌面端菜单视口修复随提交 `41b911f` 发布。

## 2026-10-11 — 01 — X 菜单视口修复与 Pages 推送

- 状态：菜单修复已本地提交 `41b911f`，但未能推送或部署。HTTPS 推送因没有可用 GitHub 用户名凭据而失败；临时 SSH 推送 URL 返回 `Permission denied (publickey)`。不在本机保存或输出凭据。
- 修复：桌面端一级分类面板靠近右边界时向左对齐；账号二级菜单根据剩余视口宽度在右侧/左侧展开，必要时收窄到可用空间，避免推动页面横向滚动。移动布局保持现有屏幕内菜单样式。
- 验证：`node --check site/app.js` 与 `git diff --check` 通过；未运行完整测试套件。页面源修改只提交了 `site/app.js`、`site/styles.css`。
- 发布阻塞与恢复：本地 main 含 `7d5d821`、`49d8992`、`41b911f`，远端跟踪基线仍为 `ed989b7`。用户在本机完成 GitHub CLI 或 Git Credential Manager 授权后，可于项目目录运行 `git push origin main`；随后确认 Pages workflow 与公开页面更新。
- 边界：未暂存或提交 RSS、新闻预览、README、`.gitignore`、测试及 `AGENTS.md` 等已有工作区文件；未更改 `origin` 配置。

## 2026-10-10 — 01 — X 账号菜单与近七天结果

- 状态：本机采集与前端实现完成，已提交本地 `49d8992`；推送尚未成功，等待网络连接恢复后将本地 `main` 推送至 Pages。
- 菜单：一级分类悬停时在右侧显示该类全部账号，切换一级分类时切换子菜单；可选具体账号查看其近七天帖子。帖子卡片不标注一级分类。账号子菜单区分“本期无动态”和“查询失败”。
- 时间与采集：全程只查询近七天，不做 30 天回溯；排除回复和原生转帖。对 11 个首次搜索异常的账号逐一重试后，50/50 账号均成功判定。
- 本轮快照：2026-10-10 12:33 上海时间；135 条去重帖子，38/50 个账号有动态，12 个账号本期无动态，0 个查询失败；Tibo `@thsottiaux` 重试后返回 5 条。公开静态副本为 `site/x-watch/latest.json`，本机快照为 `site/data/x-watch/latest.json`，历史快照保留在 `history/x-watch/`。
- 验证：`node --check site/app.js`、`bash -n scripts/run-local.sh`、Python 编译检查与 `git diff --check` 通过；未重跑测试套件。主看板在本地 `http://localhost:8000/#x-watch` 打开供目视查看，已确认分类子菜单、具体账号筛选及 4 条 SemiAnalysis 帖子。
- 发布边界：采集仍只依赖本机登录 Chrome，不进入 Actions；仅将用户指定看板代码、50 账号清单和公开动态快照发布至 Pages，不上传登录态、Cookie、RSS 配置或其他本地新闻预览资产。
- 推送阻塞：本机 HTTPS push 返回 GitHub 连接 `Empty reply from server`；GitHub 连接器虽可读取仓库，但创建 Git blob/ref 与内容 API 均返回 403 `Resource not accessible by integration`。公开 `main` 仍是 `ed989b7`。待网络可用后执行 `git push origin main`，再检查 Actions 与 Pages。

## 2026-10-10 — 01 — X 动态正式接入主看板

- 状态：完成；本机主看板可用，未提交、推送或部署。
- 清单：用户上传文件解析出的前 50 个唯一 Handle 与 `config/x_watchlist.json` 逐项顺序一致，missing/extra 均为空。配置保留名称、四类分组、关注重点和 15 个优先账号；以后增删统一改此文件，不再读取旧 64 账号临时清单。Tibo 已配置为 `@thsottiaux`。
- 采集：新增 `dashboard/x_watch.py`，通过 OpenCLI 1.8.8 + Browser Bridge 1.0.24 使用主 Chrome/X 登录态，只读普通搜索页 DOM，未调用 X API；排除回复与原生转帖，校验作者、status URL、精确七天时间窗口并去重，以公开 oEmbed 复核。正式命令为 `bash scripts/run-local.sh collect-x`，完成后自动释放自有浏览器会话、写 `site/data/x-watch/latest.json`、更新 manifest/inventory 的 `x-watch` 状态；下次运行前将上一轮非空快照保存在 `history/x-watch/`。
- 本轮结果：2026-10-10 查询 50/50 成功，128 条去重主动发布动态，29 个账号有返回；65 条属于 15 个优先账号；Tibo 4 条。112 条 oEmbed 成功，16 条保留 Chrome DOM 正文。初次含回复采集的 245 条快照已按规则存入 `history/x-watch/`，正式页面不再展示其回复噪音。每组最多 40 条，因此是抽样结果，不宣称完整时间线，账号无返回也不解释为没有发布。
- 前端：主侧边栏新增 `X 账号动态 08`，读取 `data/x-watch/latest.json`。显示动态数、返回账号、优先账号；支持全文/名称/Handle/关注点搜索、四类分组筛选、优先账号筛选和安全的 X 原文链接。所有外部文本经过 HTML 转义，非标准 `https://x.com/<handle>/status/<id>` 链接不渲染。
- 验证：上传清单一致性断言通过；Python 31/31、Playwright 桌面/手机 12/12、`scripts/check_contract.py`、`node --check site/app.js`、`bash -n scripts/run-local.sh`、`git diff --check` 通过。真实本机页面在桌面和手机均验证 128 条、Tibo 搜索 4 条、优先账号动态 65 条且无控制台错误；截图为 `work/tmp/x-watch-dashboard-{desktop,mobile}.png`。
- 本地入口：服务正在 `http://127.0.0.1:8000/` 运行，直接打开 `http://127.0.0.1:8000/#x-watch`。用户刷新网页只重新读取最近快照；需要抓取新 X 动态时保持 Chrome/X 登录并另行运行 `collect-x`。
- 边界：该模块已进入正式项目，但采集是本机能力，不能由 GitHub Actions 自动刷新。Cookie、密码和 Browser Bridge 状态未写入项目。若以后需要公开 Pages 同步，应新增显式的“本机采集后发布静态快照”流程，并再次确认发布范围；本次没有获得提交、推送或公开发布授权。

## 2026-10-09 — 01 — X 真实动态采集与独立 HTML 交付

- 状态：完成；用户所需安装、登录步骤均已完成，当前无人工操作阻塞。此记录取代下方首次无登录试跑的阻塞状态。
- 授权：用户明确要求安装全局 `opencli` 并复用主 Chrome Profile/X 登录态。用户自行安装官方 Browser Bridge、登录 X 并创建 `/usr/local/bin/opencli` → 项目 `work/node-runtime/opencli-command/opencli` 软链接。命令版本 1.8.8，扩展 1.0.24，doctor 连接成功。依赖、配置、运行状态、缓存、临时文件均限定在项目 `work/`；未导出 cookie 或凭据，未执行发帖/关注等账户写入。
- 修复：默认全局 npm 前缀无写权限，改项目内全局前缀加系统命令入口；禁用安装后全局副作用，修正已安装运行时 3 处目录定位以遵从 `OPENCLI_CONFIG_DIR`。当前 `twitter search` 适配器超时且主动请求 X 内部 API，因此独立采集器只读取普通 X 搜索页面 DOM，再用官方公开 oEmbed 复核。修正上游 `here is` 会匹配 `there is` 的关键词误判；保留全量原始快照，不因规则初筛丢失帖子。
- 数据：2026-10-09 16:47 上海时间完成。64 个清单账号全部查询，8 组、每组最多 40 条、精确最近 7 天日期校验，37 个账号返回 290 条去重有效帖子。oEmbed 成功 251 条，其余 39 条保留浏览器实际读取文本；长帖可能截断。15 条规则初筛候选；另按原 skill 创作者规则编辑 8 条中文导读，建议步骤标为 AI 整理，未宣称实测。分组搜索有截断，非穷尽时间线，未返回不能解释为无发布。
- 交付：`work/tmp/ai-influence-digest-preview/public/index.html` 为内嵌数据的独立离线 HTML，`public/latest.json` 为页面重读数据，`public/preview.png` 为最终桌面截图；原始快照与候选在 `data/`，中文编辑层为 `data/editorial.json`。本地只读服务当前运行于 `http://127.0.0.1:8877/`（仅暴露 public/）。Codex 预览已保留；采集与截图用的两个人工新建 Chrome 会话已释放，不关闭用户原有页面。
- 验证：真实浏览器完成中文搜索、全量 290 条切换、Midjourney 账号筛选、15 条规则候选、勾选、生成 Markdown 草稿、重载持久化、取消勾选、点赞排序和重读验证，控制台无错误。桌面双列及窄屏单列均人工检查；10 项快照/时间/URL/作者/编辑/嵌入数据/误判断言通过，JS `node --check`、启动脚本 `bash -n` 通过。
- 复现教程：见试跑目录 `README.md`。保持 Chrome 登录，在终端执行 `bash '/Users/liyanqiao/Documents/ChatGPT/AI自动化/work/tmp/ai-influence-digest-preview/scripts/run-local.sh' scan`；`serve` 启动本地阅读服务，`doctor` 检查连接，`build` 重建 HTML。后续采集前自动将上一轮非空快照保存在独立 `data/history/`；中文导读只按本轮 URL 匹配，未来新帖不会自动生成中文编辑。
- 边界：未修改正式采集、正式看板、Actions、`history/`、`site/data/`、翻译缓存或现有 `.venv`；未安装进全局 Codex skill 目录，未提交、推送、部署或安排自动采集。用户现在可直接阅读，不需要先人工筛选；需要自行决定正式发布稿时，可在页面勾选并整理可编辑精选稿。

## 2026-10-09 — 01 — ai-influence-digest 隔离安装与试跑

- 状态：隔离安装、真实无登录扫描和历史种子海报演示均完成；未接入、提交、推送或部署。
- 范围：上游源码解压到 `work/tmp/ai-influence-digest-upstream`，独立 Python 环境位于 `work/python-runtime/ai-influence-digest`，依赖与 Playwright 浏览器缓存均限定在项目 `work/`。未修改正式采集、Actions、`history/`、`site/data/`、翻译缓存或现有 `.venv`，未安装全局 `opencli`，未读取或复用主 Chrome Profile。
- 已验证：`pip check` 无依赖冲突；完整 64 账号、7 天、`syndication + oEmbed` 只读扫描退出码为 0，但 X 公开时间线对全部账号返回 429 或 SSL 中断，产出 `work/tmp/ai-influence-digest-output/candidates.json`，候选数 0。另用 4 条公开历史 URL 运行上游原生 `--seed-urls` 模式，官方 oEmbed 成功读取 2 条；产出位于 `work/tmp/ai-influence-digest-seed-output/`，包括候选 JSON/Markdown、人工整理的演示周报、HTML 和 PNG 海报。PNG 已人工检查，中文排版与链接显示正常。
- 结论：项目的安装、候选结构化与海报渲染链路可以在本机运行；仅靠无登录公开回退无法稳定得到本周内容。当前 PNG 是历史种子视觉演示，不能当作真实周报。
- 风险/阻塞：要看到作者主推的完整效果，需要安装全局 `opencli`、Browser Bridge，并由用户准备独立 Chrome Profile 与已登录的 X 副号；该路径会复用浏览器登录会话，需用户另行明确授权。即便启用，流程仍包含人工筛选和中文编辑，不是完全无人值守产出。
- 下一步：用户先查看 `work/tmp/ai-influence-digest-seed-output/weekly_report.png`；若认可形态，再决定是否配置专用 X 副号环境做真实周报，或仅借鉴其候选筛选与海报样式。

## 2026-10-09 — 01 — 独立新闻预览页本地验收

- 状态：本地验收通过；未提交、推送或部署。
- 范围：复核 04 原创页面、看板入口、02 独立 JSON 接口与正式新闻隔离。页面明确标注静态独立预览、规则降级、未翻译、逐源健康未知、发布时间未经核实，并按当前时间重算 36 小时新鲜度。
- 已验证：本地 `http://127.0.0.1:8000/news-preview/index.html` 和预览 JSON 均返回 HTTP 200；61 条预览数据可显示。04 运行桌面/手机完整浏览器测试 10/10、Python 29/29、静态契约与 JS 语法检查，随后修正“重新读取”分类状态并通过 6/6 预览回归；01 复核代码、截图、`node --check` 与 `git diff --check` 均无问题。
- 结论：符合“先给用户看独立 HTML 效果、不替换正式产业新闻”的本地验收标准。样本是一次采集，部分来源/分类质量未核实，不代表正式日报；上游许可与依赖风险仍阻止直接复制或上线原项目。
- 下一步：请用户先打开本地预览体验。用户明确决定长期更新与展示范围前，不接入每日自动化或正式 Pages。

## 2026-10-09 — 04 — 预览页重新读取分类状态修正

- 状态：完成，交 01 复验；未提交、推送或部署。
- 范围：仅修改 `site/news-preview/app.js`、`tests/browser/news-preview.spec.js`。重新读取后若原分类仍存在，保留选中项并使下拉框与过滤状态一致；若新数据已无该分类，自动切回“全部分类”。读取失败时也同步重置为“全部分类”，避免下次重试隐藏数据。
- 验证：新增同一浏览器测试中的“分类保留/分类消失回退”断言；桌面、手机预览测试 6/6 通过，`node --check site/news-preview/app.js` 与 `git diff --check` 通过。本地只读服务继续监听 `127.0.0.1:8000`，页面仍为 `http://127.0.0.1:8000/news-preview/index.html`。
- 下一步：01 验收筛选与重新读取的一致性，再向用户交付预览效果。

## 2026-10-09 — 04 — ai-news-daily 独立 HTML 预览页

- 状态：本地页面与入口完成，交 01 验收；未提交、推送或部署。当前预览为一次性静态样本，不随日报刷新。
- 范围：新增原创 `site/news-preview/{index.html,styles.css,app.js}`、`tests/browser/news-preview.spec.js`；在 `site/index.html` 加独立入口，`site/styles.css` 只加入口样式。正式“产业新闻”模块、Actions、`history/`、`site/data/` 和翻译缓存均未改。未复制上游源码、HTML、CSS、JS、Logo 或素材。
- 数据消费：页面相对读取 `../preview-data/ai-news-daily/latest.json`，因此本地与 GitHub Pages 子路径兼容。实际样本显示 61 条、4 类，状态 `partial`。来源采集时间与 JSON 生成时间不混淆；打开时依据 `source_crawled_at_utc` 重算 36 小时，展示逐源健康未知、规则降级分类、未翻译和上游发布时间未经核实。带关键词搜索、分类筛选、有效空/失败/陈旧/无匹配状态。外部文本用 `textContent`，原文 URL 限 HTTP(S) 且新标签加 `noopener noreferrer`；测试覆盖脚本注入与 `javascript:` 链接拒绝。
- 本地打开：在项目根目录设置 TMPDIR/TMP/TEMP、PIP/npm/XDG 缓存至 `work/` 后，以 `.venv/bin/python -m http.server 8000 --bind 127.0.0.1 --directory site` 启动只读服务；当前该服务在本机 127.0.0.1:8000 运行，页面 URL 为 `http://127.0.0.1:8000/news-preview/index.html`。`curl` 对 HTML 和独立 JSON 均为 HTTP 200；实际浏览器显示 61/61 条。
- 验证：`npm test -- --reporter=line` 桌面/手机 10/10，通过原有 4 项及新增 6 项；`bash scripts/run-local.sh test` 29/29；`.venv/bin/python scripts/check_contract.py`、`node --check site/news-preview/app.js`、`git diff --check` 均通过。实际浏览器桌面、手机视口人工检查完成；截图保存 `work/tmp/ai-news-preview-desktop.png` 与 `work/tmp/ai-news-preview-mobile.png`。
- 风险/下一步：上游许可文本仍缺失、依赖有安全告警，因此当前只使用 02 的原创静态 JSON 适配器与 04 的原创页面。01 验收页面和数据口径后，请用户决定是否长期自动刷新；在此之前不要将预览接进正式日报或替换正式新闻。

## 2026-10-09 — 02 — ai-news-daily 独立预览数据接口

- 状态：数据适配与本地预览 JSON 完成；待 04 实现页面并确认消费接口。当前未发现已创建的 04 号任务，跨角色接口以本记录为准。
- 范围：新增原创 `dashboard/preview_ai_news_daily.py`、`tests/test_preview_ai_news_daily.py`，从 03 隔离的 `work/tmp/ai-news-daily-upstream/data/2026-10-09-processed.json` 生成 `site/preview-data/ai-news-daily/latest.json`。未引入上游程序、依赖、UI 或清理逻辑，也未改正式新闻采集、Actions、`history/`、`site/data/` 或翻译缓存。
- 复现：在项目根目录运行 `.venv/bin/python -m dashboard.preview_ai_news_daily --input work/tmp/ai-news-daily-upstream/data/2026-10-09-processed.json`。转换器只写独立预览路径；输入缺失/损坏会写 `status=error`、`rows=[]` 并以非零码退出；有效空输入写 `status=empty`。
- 给 04 的静态接口：在 `site/` 页面中以相对 URL `preview-data/ai-news-daily/latest.json` 读取。根字段为 `schema_version=1`、`dataset=ai_news_daily_preview`、`preview_only=true`、`status`（`ok|partial|stale|empty|error`）、`freshness_status`（`recent_crawl|stale_crawl|unknown`）、`freshness_checked_at_utc`、`freshness_threshold_hours=36`、`source_crawled_at_utc`、`source_processed_at_utc`、`generated_at_utc`、`source_filter_date`、`processing_method`、`source_health`、`counts`、`warnings[]`、`rows[]`。行字段为 `id`、原文 `url`、`title`、可空 `summary`、`source`、`source_category`、`category`、`category_basis`、`language`、`translation_status=not_translated`、`published_at_original`、`published_at_utc`、`publication_time_status`、可空 `collected_at_utc`。`summary` 仅是上游抓取的 RSS 短摘录，缺失时为 `null`。
- 04 展示约定：明确标注“独立预览”；用 `source_crawled_at_utc` 显示上游采集时间，用 `published_at_utc` 显示上游提供的发布时间；`generated_at_utc` 仅是本地转换时间。静态 JSON 的 `freshness_status` 只代表 `freshness_checked_at_utc` 当时的检查，页面打开时应按当前时间和 `source_crawled_at_utc` 重新判断是否超过 36 小时。逐源失败没有上游明细，显示 `source_health=unreported`，不要把 70 个配置源写成 70 个成功源。所有外部文本与 URL 要安全渲染；缺失摘要不补写、英文不称中文翻译、`publication_time_status` 可疑时提示未经核实。
- 口径差异：正式“产业新闻”仅选近七日可核查的产业事件，按 AI/事件词与排除词过滤，分上中下游，规范 URL 与标题前八词聚类去重，按来源/地区限额最多 50 条，并使用 MyMemory 中文翻译；预览取上游隔离输出的更广来源（含研究、教程、社区等），本次模型不可用，实际为规则筛选/分类，不再套正式事件过滤，保留上游 `category`，只按规范化 URL 或完整规范化标题去重、不做近似事件聚类、不调用翻译。上游各类源采用约 3–15 日不同窗口，转换器不改写日期，也不额外宣称“今日新闻”。上游可能以抓取时间代替缺失或未来发布时间，原始 RSS 时间已不可回溯；行内始终标为 `upstream_normalized_unverified`，接近采集时间的可疑值另标记。
- 实测：输入 61 条，输出 61 条、4 类，`status=partial`、`freshness_status=recent_crawl`、`processing_method=rule-based`、`ai_filter_used=false`、`source_health=unreported`；预览 JSON 50,054 字节。`bash scripts/run-local.sh test` 29/29 通过，`.venv/bin/python scripts/check_contract.py`、`git diff --check` 通过。
- 限制/下一步：当前是 03 一次隔离运行的静态预览，不会由正式日报自动更新。04 确认接口后制作独立页面与入口；01 验收后再由用户决定长期自动化。不得将上游缺失的逐源状态、真正原始发布时间或机器翻译凭空补齐。

## 2026-10-09 — 03 — ai-news-daily 隔离流水线与排期推送复查

- 状态：隔离预览完成；排期推送因 GitHub 身份验证阻塞。
- 范围：在 `work/tmp/ai-news-daily-upstream`（提交 `bb88b501`）隔离安装锁定依赖，运行 RSS 采集、规则降级处理、静态 HTML 构建并启动本地只读服务；未复制到正式 `site/`，未运行上游 workflow、Git 自动提交/拉取/强推、Pages 部署或 15 天文件删除。根项目 `history/`、`site/data/`、`history/translation-cache.json` 无改动。
- 许可证：`package.json` 与 README 声明 MIT，但当前 Git tree 无 LICENSE/COPYING/NOTICE，GitHub License API 返回 404，无法确认完整授权文本及署名要求。因此隔离结果只能用于本地评估，02/04 不得复制上游源码、HTML、CSS、JS、Logo 或其他 UI 素材到正式站点。
- 依赖：Node `v24.21.0`、npm `11.19.0`；`npm ci --ignore-scripts` 后仅为当前 ARM64 Mac 重建锁定的 `sharp@0.32.6`。`npm audit --omit=dev` 报告 10 项漏洞：2 critical、6 high、2 moderate；主要涉及 axios、form-data、protobufjs/onnxruntime、sharp、tar-fs。长期接入前必须升级或替换，不应直接沿用该锁文件上线。
- 上游缺陷与隔离修补：① `npm run crawl`、`npm run build` 的入口判断在含中文的绝对路径/相对参数下静默不执行，改为直接调用其导出函数；② `process-with-llm.js` 自带 15 天过滤，新增仅限隔离目录的 `DISABLE_ROLLING_CLEANUP=1` 开关；③ Transformers 缓存改由 `AI_NEWS_MODEL_CACHE` 指向项目 `work/cache/`；④规则处理生成 `{text,label}` 实体，而构建器只接受 `{word,entity}`，在隔离构建器中增加兼容归一化；⑤模板直接把 RSS 标题、摘要、来源与 URL 插入 HTML，缺少统一转义，不能原样用于正式页面。以上均未进入根项目源码或任何提交。
- 运行结果：70 个来源采集出 211 篇唯一候选；本地分类模型远程下载失败，按上游逻辑降级为关键词过滤。处理阶段读取 1681 篇既有隔离数据，新处理 61 篇，总计 1742 篇，`cleanupApplied=false`、`cleanedUpCount=0`。构建生成 17 个日期，当天页面展示 61 篇、4 个分类；部分 RSS 返回超时、403、404、410。输出为 `work/tmp/ai-news-daily-upstream/site/index.html`，当前本地 URL 为 `http://127.0.0.1:8765/`，已实际验证 HTTP 200、HTML 97034 字节，`data.json` 为 1742 篇，并在浏览器中打开。
- 复现命令：在上游目录执行 `npm_config_cache="$PROJECT_ROOT/work/cache/npm-ai-news-daily" npm ci --ignore-scripts --no-audit --no-fund`，再执行 `npm_config_cache="$PROJECT_ROOT/work/cache/npm-ai-news-daily" npm rebuild sharp --foreground-scripts`；设置 `AI_NEWS_MODEL_CACHE="$PROJECT_ROOT/work/cache/ai-news-daily-models"`、`TMPDIR="$PROJECT_ROOT/work/tmp/ai-news-daily-runtime"`、`XDG_CACHE_HOME="$PROJECT_ROOT/work/cache"` 后，以 `node --input-type=module -e` 分别 import 并调用 `crawlAllSources()`、默认的 `processArticlesWithAI()`（同时设 `DISABLE_ROLLING_CLEANUP=1`）和默认的 `buildSite()`；最后从项目根目录运行 `.venv/bin/python -m http.server 8765 --bind 127.0.0.1 --directory work/tmp/ai-news-daily-upstream/site`。
- 排期提交：推送前 `git ls-remote` 确认远端 `main=ed989b7`，随后显式推送 `7d5d82131f900167217c1457d3bcab62663a1749:refs/heads/main`，但 HTTPS 无法取得 Keychain 凭据；现有 SSH 身份也未获 GitHub 授权。公开 API 再次确认远端仍为 `ed989b7`；最新日报仍为 scheduled run `37768937652`，最新周报仍为 `37455547886`，最新 Pages deployment 仍为 `6934048702`，正式 Pages 返回 HTTP 200。故本次没有触发新 Actions/Pages，02 的 RSS 工作区改动没有被提交或推送。
- 下一步：01/用户恢复 GitHub HTTPS 凭据或为现有 SSH 公钥授权后，由 03 重新确认远端仍为 `ed989b7`，仅推送 `7d5d821` 并观察两条 Actions 与 Pages。02 可基于隔离生成的 JSON 设计独立、原创的数据契约；04 应独立实现预览 UI，不复用上游素材。

## 2026-10-09 — 01 — 排期修改与 ai-news-daily 预览决策

- 状态：本地排期已提交，远端推送阻塞；预览方案已定，接入尚未执行。
- 范围：日报改为上海时间每天 15:48（UTC 07:48），周报改为每周一 07:11（周日 UTC 23:11）；用户选择新增独立 HTML 预览页，不替换现有“产业新闻”。上游浅克隆位于 `work/tmp/ai-news-daily-upstream`，提交 `bb88b501`。
- 已验证：排期相关六个文件单独提交为本地 `7d5d821`；`git diff --cached --check`、25 项 Python 测试、静态契约、`node --check site/app.js` 均通过。02 的 RSS 配置与测试仍在工作区，未包含在此提交。公开 GitHub API 返回远端 `main=ed989b7`；`github.com:443` 连接超时，推送未成功。
- 上游边界：上游为独立 Node RSS→分类→静态站流水线，包含 15 天滚动清理、自动提交/推送与部署；不可直接搬入本项目。`package.json` 标 MIT，README 引用 LICENSE，但检出的仓库未见 LICENSE 文件；复制代码前须核实许可。尚未安装依赖或运行上游采集，未生成预览页。
- 风险/阻塞：排期尚未在线生效。推送此提交会匹配现有日报和周报的 `push` 路径，可能立即触发真实采集与 Pages。下游预览必须保留 `history/`、`site/data/`、翻译缓存与现有新闻栏目。
- 下一步：03 检查网络恢复后推送排期提交并核验 Actions；02/03/04 按职责依次完成隔离运行、数据桥接和独立预览页，01 最终验收。

## 2026-10-09 — 01 — 新资讯源优先级决策

- 状态：完成。
- 决策：按 01 建议，Google DeepMind 与 Together AI Blog 暂时保持当前来源顺序和翻译优先级。
- 观察项：配置合入后由 03 观察真实日报的 `translation_pending`、`translation_errors` 与来源入选情况；只有持续发生额度竞争时，才交给 02 设计公平分配方案。
- 发布状态：仍为本地未提交变更，尚未推送或触发发布。

## 2026-10-09 — 01 — 两个官方 RSS 接入验收

- 状态：本地验收通过；待用户授权提交与发布。
- 范围：审查 `config/sources.json`、新增契约测试、新闻采集与翻译代码、日报 workflow、JSON 契约、HTML 新闻渲染，并结合 03 的线上只读核验结果；未运行全量采集，未改写 `history/`、`site/data/` 或翻译缓存。
- 来源结论：Google DeepMind 与 Together AI Blog 均使用各自官方域名的公开 RSS；2026-10-09 定向下载可被现有解析器完整解析，七日窗口内分别有 1 条、2 条符合现有规则。只引用标题、短摘要、发布时间和原文链接，不复制第三方项目代码。
- 兼容性结论：配置字段与现有 `collect_news` 契约一致；单源失败记入 `feed_checks` 并令快照为 `partial`，其他来源继续；全部来源失败时 `run_daily` 保留最近成功快照。新增配置匹配日报 workflow 的 `config/**` push 触发范围，沿用月度 Release、Pages 和现有 `renderNews`，无需改工作流或前端。
- 翻译结论：当前两个来源七日合格样本合计约 505 个待翻译字符，低于滚动 24 小时 3000 字符上限。翻译失败或额度耗尽时对应新英文条目不进入中文行，`translation_pending` 增加、快照标记 `partial`，旧的七日内成功条目仍可合并保留。来源按配置顺序消耗额度，新来源当前位于最前，未来高频发布时可能挤占后续来源额度，列为上线观察项。
- 已验证：`bash scripts/run-local.sh test` 为 25/25 通过；`.venv/bin/python scripts/check_contract.py`、`git diff --check` 通过。03 已确认三个 workflow active 且支持手动触发，最近日报、周报、Pages deployment 成功，公开站点 HTTP 200。
- 上线验收标准：① 用户明确授权提交/推送；② 推送后日报 workflow 成功；③ `news/latest.json` 中两个 `feed_checks` 可解析且无结构错误，允许无新文章时 `eligible=0`；④ `translation_pending`、`translation_errors` 与快照 `status` 相互一致且无旧数据冒充当天数据；⑤ 月度 Release 上传成功；⑥ Pages deployment 成功、manifest 日期更新、新闻栏可打开原文；⑦ 记录定时延迟与 Secrets 名称复核结果，不记录密钥值。
- 下一步：获得用户授权后再提交和推送；由 03 观察首次真实日报及 Pages，01 根据上述标准作最终线上验收。

## 2026-10-09 — 03 — Actions、Pages 与 RSS 发布链路只读核验

- 状态：完成（Secrets 名称清单待有仓库管理权限的账户复核）。
- 范围：只读检查 `.github/workflows/{collect,weekly,quality}.yml`、日报 RSS 调用路径、公开 GitHub Actions/Deployments API、公开 Pages 站点与当前线上 JSON；未运行采集、未触发 workflow、未改写数据。
- 已验证：三个 workflow 均为 `active` 且均含 `workflow_dispatch`；最近一次日报 `37768937652`（北京时间 2026-10-08 19:16 至 19:17）、周报 `37455547886`（2026-10-06 19:18 至 19:19）均成功。对应最新 Pages deployment `6934048702` 状态为 `success`，站点 `https://liyanqiao0106-max.github.io/hf-trend-snapshots/` HTTP 200；线上 inventory 最新快照为 2026-10-08。公开 Secrets API 返回 401，未读取或输出密钥。
- 结论：Google DeepMind 与 Together AI Blog 仅新增 `config/sources.json` 的一级官方 RSS。`dashboard.run_daily --scope daily` 已按该配置调用 `collect_news`，并沿用 `feed_checks`、`translation_pending`、本地快照打包、月度 Release 上传与 Pages 部署；无需工作流改造。该文件匹配 `collect.yml` 的 `config/**` push 路径，故其合入 `main` 会自动运行一次真实日报、归档并发布。质量 workflow 不监听 push，仅可通过 PR 或手动触发执行。
- 风险/阻塞：声明的日报 cron 为北京时间 12:00，但最新 scheduled run 于约 19:16 才启动，存在 GitHub 调度延迟；当前线上新闻、GPU 和存储模块均为 `partial`，这是快照状态而非本次 RSS 变更导致。`OPENROUTER_API_KEY` 为周度 token 模块所需，最近周报 token 模块为 `ok`；`RUNPOD_API_KEY`、`VAST_API_KEY` 与 `HF_TOKEN` 的存在不可由匿名接口确认，前两者在代码中可选且缺失时使 GPU 模块降级为 `partial`，HF 可匿名访问。请 01 使用有管理权限的 GitHub 账户在仓库 Settings 的 Secrets and variables > Actions 中仅核对名称/存在状态；不需要向本 Agent 提供任何值。
- 下一步：01 先决定何时将 02 的 RSS 配置合入 `main`（会产生真实采集和发布）；合入后由 03 观察一次日报 run 的 `feed_checks`、`translation_pending`、Release 上传和 Pages 部署结果。

## 2026-10-09 — 02 — 外部资讯项目适配与 RSS 接入

- 状态：本地接入完成；待 01 验收与后续发布。
- 范围：评估三个用户指定仓库；修改 `config/sources.json`、`tests/test_daily_sources.py`，复用现有 `dashboard.news` → `site/data/news/latest.json` → HTML 新闻栏目的路径。
- 适配排序：① `ai-news-daily`：RSS、定时采集、静态站结构最贴近本项目；② TrendRadar：RSS/热榜筛选可借鉴，但热榜依赖 newsnow API、整套程序含独立数据库/通知/页面且代码为 GPL-3.0；③ `ai-influence-digest`：X 扫描依赖本机已登录 Chrome/OpenCLI 与人工选稿，无法可靠运行于无人值守的每日 Actions。
- 来源依据：`https://github.com/ai-news-daily/ai-news-daily.github.io/blob/main/sources.json` 提供候选 URL；直接核验 `https://deepmind.google/blog/rss.xml` 和 `https://www.together.ai/blog/rss.xml` 均返回可解析 RSS，近七日各有 1、2 条经现有筛选器通过的条目。2026-10-09 核验时 Microsoft AI RSS 为 HTTP 410、LangChain RSS 为 HTTP 404、The Verge AI Atom 当前无条目，故未纳入。
- 数据口径：仅采集官方订阅公开标题、短摘要、发布时间和原文链接；按现有七日窗口、事件筛选、翻译额度与去重规则进入新闻模块。原始发布日期保留，采集失败沿用现有来源状态与最近成功快照处理。每日各请求一次；无需新密钥或服务。未复制三个仓库代码。第三方订阅内容版权仍归原站，页面只展示短摘要与链接。
- 已验证：`bash scripts/run-local.sh test` 为 25/25 通过，`.venv/bin/python scripts/check_contract.py` 与 `git diff --check` 通过；两条订阅用项目现有解析器做过只读在线抽查。
- 风险/阻塞：新闻仍受 MyMemory 每 24 小时 3000 字符上限约束，新条目在额度耗尽时不会进入中文展示；尚未执行完整真实采集，避免覆盖本机 `history/` 与 `site/data/`。`ai-news-daily` README 声称 MIT，但 GitHub 仓库元数据没有识别到许可证；本次仅将其清单当作发现线索，独立核实订阅 URL。
- 下一步：01 审核本地变更；获授权提交/发布后，由 03 观察一次日报 Actions 的 `feed_checks`、`translation_pending` 和 Pages 新闻栏目。

## 2026-10-09 — 01 — 浏览器验证

- 状态：完成
- 范围：项目内安装锁定的 Node 依赖与 Playwright Chromium，运行浏览器测试。
- 已验证：`npm test` 在桌面与手机两个视口共 4 项测试全部通过。
- 结论：恢复后的静态看板可在 Mac 的 Chromium 环境读取本地快照并正常呈现已覆盖的页面。
- 风险/阻塞：线上 Actions/Pages 状态仍待单独核验。
- 下一步：03 核验线上自动刷新与部署状态。

## 2026-10-09 — 01 — Mac Python 环境验证

- 状态：完成
- 范围：项目内 `.venv` 安装 `requirements.txt`；更新 README 与项目状态。
- 已验证：`bash scripts/run-local.sh test` 运行 24 项测试全部通过；`node --check site/app.js`、`python3 scripts/check_contract.py` 通过。
- 结论：权威源码可在 Mac 上运行 Python 契约测试；浏览器测试和线上 Actions 健康仍待检查。
- 风险/阻塞：尚未执行 Playwright 浏览器测试和真实采集；真实采集会更新本地快照，需安排独立验证。
- 下一步：03 核验线上 Actions/Pages，04 完成浏览器测试。

## 2026-10-09 — 03 — 恢复 Mac 本地启动脚本

- 状态：完成
- 范围：新增 `scripts/run-local.sh`；更新 `docs/project/STATUS.md`。
- 已验证：迁移备份与当前 `main` 的入口逐项核对，`requirements.txt`、`tests/`、`dashboard/run_daily.py`、`scripts/build_mac_package.py`、`site/` 均存在；`bash -n scripts/run-local.sh` 通过。
- 结论：脚本提供 `serve`、`test`、`collect`、`package` 四个模式，优先使用 `.venv/bin/python`；`TMPDIR`、PIP、npm、Hugging Face、XDG 与 Playwright 缓存全部限定在项目的 `work/` 内。
- 风险/阻塞：未安装或验证项目 Python/Node/Playwright 依赖，故未运行会访问网络或执行采集的模式；完整环境验证仍属 P0。
- 下一步：02/04 安装或确认现有依赖后，分别执行 Python 契约测试和 Playwright 浏览器测试；03 可随后核验线上 Actions 与 Pages。

## 2026-10-20 — WorkBuddy AI 新闻桥接发布

- 状态：本地完成，待 01 提交推送并做 Pages 线上验收。
- 方案：WorkBuddy 保留每日 HTML 与历史 `reports/`；`scripts/sync_workbuddy_news.py` 复制看板、报告和带 SHA-256 的 `manifest.json` 到 `site/ai-news-daily/`。公开入口为 `/ai-news-daily/`。
- 每日命令：`bash /Users/liyanqiao/Documents/ChatGPT/AI自动化/scripts/publish_workbuddy_news.sh`。该脚本同步、只暂存 `site/ai-news-daily/`、按上海日期提交并推送 `main`。
- 验证：当前同步 7 份报告；`tests.test_sync_workbuddy_news`、`git diff --check`、`bash -n scripts/publish_workbuddy_news.sh` 通过。
- 线上验收：推送后检查 GitHub Actions `collect` / `deploy-dashboard`，确认 `https://liyanqiao0106-max.github.io/hf-trend-snapshots/ai-news-daily/` 与 2026-10-19 报告返回 200；次日检查 WorkBuddy 生成的新日期是否自动进入清单。
- 注意：不要将现有未提交的 `site/news-preview`、RSS 配置或其他工作区改动一并提交；WorkBuddy 私有状态、Cookie、密钥和 `.env` 不进入 Pages。

## 模板

```markdown
## YYYY-MM-DD — 角色编号 — 简短主题

- 状态：完成 / 进行中 / 阻塞
- 范围：涉及的功能与文件
- 已验证：执行的命令、测试结果或人工核验结果
- 结论：数据、实现或设计结论
- 风险/阻塞：需要谁决定，以及所需信息
- 下一步：可直接执行的一步
```

## 2026-10-09 — 01 — 恢复 GitHub 权威基线

- 状态：完成
- 范围：Git 元数据、`.github/workflows/`、权威源码恢复；本地数据保留。
- 已验证：`history/` 与 `site/data/` 恢复前后 SHA-256 全部一致；`git diff --exit-code` 无源码差异；`origin/main` 指向 `ed989b7`。
- 结论：本机现已连接至权威 GitHub 历史，但 Mac 本地启动脚本不在权威版本中。
- 风险/阻塞：需 P0 验证本机运行环境以及线上 Actions/Pages 健康。
- 下一步：03 恢复并验证受控的 Mac 启动脚本。
