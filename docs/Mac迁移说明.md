# Mac 迁移说明

迁移包用于在 Mac 上查看、修改和本地运行本项目。线上定时采集仍由 GitHub Actions 完成，不需要 Mac 或 Windows 保持开机。

## 压缩包包含

- 完整源代码、工作流、配置、测试与项目说明。
- 打包时的 `site/data` 最新快照，可在断网时启动静态服务器查看。
- 不包含 `.git`、`.env`、API key、Windows Python/Node 运行时、`node_modules`、测试报告和临时缓存。

## 在 Mac 上解压和运行

1. 将压缩包复制到 Mac 并解压。
2. 打开 Terminal，进入解压后的项目目录。
3. 建立独立 Python 环境并安装依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

4. 如需本地采集，复制环境变量模板并用文本编辑器填写 OpenRouter key：

```bash
cp .env.example .env
```

`.env` 只保存在本机，不要提交到 GitHub，也不要通过聊天发送。

5. 验证并启动：

```bash
python -m unittest discover -s tests -v
python -m dashboard.run_daily --scope all
python -m http.server 8000 --directory site
```

浏览器打开 <http://localhost:8000>。只想查看打包时快照时，可以跳过采集命令，直接启动静态服务器。

## 前端测试（可选）

安装 Node.js 24 后执行：

```bash
npm ci
npx playwright install chromium
npm test
```

## 与 GitHub 同步

项目的正式线上版本在 `liyanqiao0106-max/hf-trend-snapshots`。日常查看不需要 Git。若以后要在 Mac 修改代码，建议从 GitHub 重新 clone，再把本地 `.env` 单独复制到新目录；压缩包内不包含 Git 历史。

## 常见问题

- 双击 `index.html` 无法读取 JSON：浏览器会限制本地 `file://` 请求，请使用上面的 `http.server`。
- 页面数据没有当天更新：GitHub schedule 可能延迟，查看页面日期和仓库 Actions 状态。
- Token 用量为空：检查本机 `.env` 或 GitHub Secret 是否存在 `OPENROUTER_API_KEY`，不要把 key 写入代码。
- 某个来源显示 `partial`：其他来源仍会更新；看板保留上次成功值，并在状态面板显示原因。
