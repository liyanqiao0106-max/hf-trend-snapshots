# WorkBuddy AI 新闻接入

## 设计结论

WorkBuddy 继续保留“每日一份报告 HTML + 看板 `index.html`”作为本地源文件，不改成只维护一个集合 HTML。每日文件天然形成历史归档，出错时可以回滚到前一天，也不会让一个不断变大的文件成为单点故障。

Pages 站点通过 `scripts/sync_workbuddy_news.py` 将以下内容复制到 `site/ai-news-daily/`：

- WorkBuddy 看板 `index.html`；
- `reports/*.html` 全部历史报告；
- `manifest.json`，记录同步时间、报告数量、文件大小和 SHA-256。

同步后的公开入口是：

`https://liyanqiao0106-max.github.io/hf-trend-snapshots/ai-news-daily/`

## 每日发布命令

WorkBuddy 每日 08:50 生成报告后，调用本仓库中的脚本：

```bash
bash /Users/liyanqiao/Documents/ChatGPT/AI自动化/scripts/publish_workbuddy_news.sh
```

该命令会同步本地 HTML、只暂存 `site/ai-news-daily/`、创建一个带日期的提交并推送 `main`。GitHub Pages 随后按现有 `collect.yml` 的 push 链路部署。脚本不会读取或提交 `.env`、WorkBuddy 私有状态、Cookie 或密钥。

为避免 WorkBuddy 已生成报告但没有真正执行 shell 命令，Mac 另外安装独立的 LaunchAgent 作为发布保障。它在每天 09:30、10:30、11:30、12:30 检查一次；有新内容才提交和推送，没有变化时直接退出。安装或刷新配置：

```bash
bash /Users/liyanqiao/Documents/ChatGPT/AI自动化/scripts/install_workbuddy_news_launch_agent.sh
```

运行日志保存在项目内 `work/logs/workbuddy-news-publish*.log`，不会进入 Git。

首次接入完成后，建议把主看板中的“WorkBuddy 每日 AI 新闻”入口作为固定入口；今后只要 WorkBuddy 生成新报告并调用发布命令，新报告就会自动出现在公开 Pages 的历史列表中。

## 失败边界

- WorkBuddy 找不到 `index.html` 或没有报告 HTML 时，脚本失败且不会提交空站点。
- 报告内容仍由 WorkBuddy 负责；桥接脚本只复制静态 HTML，不改写 HTML 内部结构。
- GitHub Pages 或网络推送失败时，本地同步结果仍保留在工作区，可在网络恢复后重试。
