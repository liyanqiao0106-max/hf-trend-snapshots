const state = { source: "hugging-face", data: {} };
const format = new Intl.NumberFormat("zh-CN");
const shanghai = new Intl.DateTimeFormat("zh-CN", { dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Shanghai", hour12: false });
const text = (value) => String(value ?? "");
const escapeHtml = (value) => text(value).replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
const number = (value) => value === undefined || value === null ? "—" : format.format(value);
const config = {
  "hugging-face": { file: "data/hugging-face/latest.json", link: "https://huggingface.co/models", linkText: "Hugging Face Models ↗" },
  github: { file: "data/github/latest.json", link: "https://github.com/trending", linkText: "GitHub Trending ↗" },
};

function setCards(payload) {
  const github = state.source === "github";
  document.querySelector("#card-one-label").textContent = github ? "本期热门项目" : "完整历史模型";
  document.querySelector("#card-one").textContent = number(github ? payload.count : payload.exact_count);
  document.querySelector("#card-one-note").textContent = github ? "GitHub Trending 周榜" : "可计算周度增量";
  document.querySelector("#card-two-label").textContent = github ? "AI 相关项目" : "新上榜观察";
  document.querySelector("#card-two").textContent = github ? number(payload.rows.filter((row) => row.domain && !row.domain.includes("非AI")).length) : number(payload.watch_count);
  document.querySelector("#card-two-note").textContent = github ? "按简介、topics、README 初步识别" : "历史快照不足三期";
  document.querySelector("#card-three-label").textContent = github ? "有项目说明" : "异常累计值";
  document.querySelector("#card-three").textContent = github ? number(payload.rows.filter((row) => row.use_case_zh).length) : number(payload.invalid_count);
  document.querySelector("#card-three-note").textContent = github ? "description / README" : "已从排名中排除";
}

function renderRows() {
  const payload = state.data[state.source];
  if (!payload) return;
  const query = document.querySelector("#search").value.trim().toLowerCase();
  const status = document.querySelector("#status-filter").value;
  const category = document.querySelector("#category-filter").value;
  const github = state.source === "github";
  const rows = payload.rows.filter((row) => (!github || !query || `${row.full_name} ${row.description_raw} ${row.use_case_zh}`.toLowerCase().includes(query)) && (github || (status === "all" || row.status === status)) && (category === "all" || (github ? row.domain : row.task_type) === category));
  document.querySelector("#row-count").textContent = `显示 ${format.format(rows.length)} / ${format.format(payload.rows.length)} 条`;
  document.querySelector("#rows").innerHTML = rows.length ? rows.map((row) => github
    ? `<tr><td class="number">${row.weekly_rank ?? row.rank ?? "—"}</td><td><a href="${escapeHtml(row.url)}" target="_blank" rel="noreferrer">${escapeHtml(row.full_name)} ↗</a></td><td>${escapeHtml(row.domain)}</td><td class="number">${number(row.stars_this_week)}</td><td class="number">${number(row.stars)}</td><td>${escapeHtml(row.language || "—")}</td><td class="note">${escapeHtml(row.use_case_zh)}</td></tr>`
    : `<tr><td class="number">${row.rank ?? "—"}</td><td><a href="${escapeHtml(row.model_url)}" target="_blank" rel="noreferrer">${escapeHtml(row.id)} ↗</a></td><td>${escapeHtml(row.task_type)}</td><td class="number">${number(row.downloads_this_period)}</td><td class="number">${number(row.downloads_last_period)}</td><td class="number">${number(row.download_acceleration)}</td><td class="number">${number(row.likes)}</td><td class="note">${escapeHtml(row.use_case_zh || row.download_note)}</td></tr>`).join("") : '<tr><td colspan="8">没有符合条件的数据。</td></tr>';
}

function populate(payload) {
  state.data[state.source] = payload;
  const github = state.source === "github";
  setCards(payload);
  document.querySelector("#panel-title").textContent = github ? "GitHub 周度热门项目" : "周度下载加速度排行";
  document.querySelector("#search-label").textContent = github ? "搜索项目" : "搜索模型";
  document.querySelector("#search").placeholder = github ? "项目名、简介或用途" : "模型名或机构";
  document.querySelector("#period").textContent = github ? `快照日期：${payload.snapshot_date || "—"}` : `比较快照：${payload.snapshot_dates.join(" → ")}`;
  document.querySelector("#status").textContent = `最新成功生成：${shanghai.format(new Date(payload.generated_at_utc))}（上海时间）`;
  document.querySelector("#footnote").textContent = github ? "数据源：GitHub Trending 页面与官方 REST API。项目用途说明优先取仓库 description，其次取 README 开头；仅作快速研究索引，详情请打开原项目。" : "数据源：Hugging Face Hub 官方 API。周度值由累计下载量快照差分计算；非 7 日间隔会换算为 7 日等效值。";
  document.querySelector("#table-head").innerHTML = github ? "<tr><th>排名</th><th>项目</th><th>领域</th><th>本周新增 Stars</th><th>总 Stars</th><th>语言</th><th>用途说明</th></tr>" : "<tr><th>排名</th><th>模型</th><th>类型</th><th>本期下载</th><th>上期下载</th><th>下载加速度</th><th>点赞</th><th>说明</th></tr>";
  const categories = [...new Set(payload.rows.map((row) => github ? row.domain : row.task_type))].filter(Boolean).sort();
  document.querySelector("#category-filter").innerHTML = `<option value="all">全部${github ? "领域" : "类型"}</option>` + categories.map((item) => `<option value="${escapeHtml(item)}">${escapeHtml(item)}</option>`).join("");
  document.querySelector("#status-filter").style.display = github ? "none" : "block";
  renderRows();
}

async function loadSource(source) {
  try {
    const response = await fetch(config[source].file, { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    if (payload.dataset !== (source === "github" ? "github_trending_weekly" : "hugging_face_weekly") || !Array.isArray(payload.rows)) throw new Error("数据格式不正确");
    if (state.source === source) populate(payload);
  } catch (error) {
    if (state.source === source) {
      document.querySelector("#status").innerHTML = '<span class="error">该来源最新数据暂不可用，请稍后刷新。</span>';
      document.querySelector("#rows").innerHTML = '<tr><td colspan="8">无法读取看板数据。</td></tr>';
    }
    console.error(`Unable to load ${source}`, error);
  }
}

function switchSource(source) {
  state.source = source;
  document.querySelectorAll(".tab").forEach((button) => button.classList.toggle("active", button.dataset.source === source));
  document.querySelector("#source-link").href = config[source].link;
  document.querySelector("#source-link").textContent = config[source].linkText;
  if (state.data[source]) populate(state.data[source]); else loadSource(source);
}

document.querySelectorAll(".tab").forEach((button) => button.addEventListener("click", () => switchSource(button.dataset.source)));
document.querySelectorAll("#search, #status-filter, #category-filter").forEach((element) => element.addEventListener("input", renderRows));
loadSource("hugging-face");
loadSource("github");
