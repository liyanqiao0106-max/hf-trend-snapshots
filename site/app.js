const state = { payload: null };
const format = new Intl.NumberFormat("zh-CN");
const shanghai = new Intl.DateTimeFormat("zh-CN", { dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Shanghai", hour12: false });

const text = (value) => String(value ?? "");
const escapeHtml = (value) => text(value).replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
const number = (value) => value === undefined || value === null ? "—" : format.format(value);

function renderRows() {
  const payload = state.payload;
  const query = document.querySelector("#search").value.trim().toLowerCase();
  const status = document.querySelector("#status-filter").value;
  const category = document.querySelector("#category-filter").value;
  const rows = payload.rows.filter((row) => (status === "all" || row.status === status) && (category === "all" || row.task_type === category) && (!query || row.id.toLowerCase().includes(query)));
  document.querySelector("#row-count").textContent = `显示 ${format.format(rows.length)} / ${format.format(payload.rows.length)} 条`;
  document.querySelector("#rows").innerHTML = rows.length ? rows.map((row) => {
    const acceleration = row.download_acceleration;
    const accelerationClass = acceleration > 0 ? "positive" : acceleration < 0 ? "negative" : "";
    const statusBadge = row.status === "watch" ? '<span class="badge watch">观察</span>' : '<span class="badge">完整</span>';
    return `<tr><td class="number">${row.rank ?? statusBadge}</td><td><a href="${escapeHtml(row.model_url)}" target="_blank" rel="noreferrer">${escapeHtml(row.id)} ↗</a></td><td>${escapeHtml(row.task_type)}</td><td class="number">${number(row.downloads_this_period)}</td><td class="number">${number(row.downloads_last_period)}</td><td class="number ${accelerationClass}">${number(acceleration)}</td><td class="number">${number(row.likes)}</td><td class="note">${escapeHtml(row.download_note)}</td></tr>`;
  }).join("") : '<tr><td colspan="8">没有符合条件的模型。</td></tr>';
}

function populate(payload) {
  state.payload = payload;
  document.querySelector("#exact-count").textContent = number(payload.exact_count);
  document.querySelector("#watch-count").textContent = number(payload.watch_count);
  document.querySelector("#invalid-count").textContent = number(payload.invalid_count);
  document.querySelector("#status").textContent = `最新成功生成：${shanghai.format(new Date(payload.generated_at_utc))}（上海时间）`;
  document.querySelector("#period").textContent = `比较快照：${payload.snapshot_dates.join(" → ")}`;
  const categories = [...new Set(payload.rows.map((row) => row.task_type))].sort();
  const options = categories.map((item) => `<option value="${escapeHtml(item)}">${escapeHtml(item)}</option>`).join("");
  document.querySelector("#category-filter").insertAdjacentHTML("beforeend", options);
  document.querySelectorAll("#search, #status-filter, #category-filter").forEach((element) => element.addEventListener("input", renderRows));
  renderRows();
}

async function load() {
  try {
    const response = await fetch("data/hugging-face/latest.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    if (payload.dataset !== "hugging_face_weekly" || !Array.isArray(payload.rows)) throw new Error("数据格式不正确");
    populate(payload);
  } catch (error) {
    document.querySelector("#status").innerHTML = '<span class="error">最新数据暂不可用，请稍后刷新。</span>';
    document.querySelector("#rows").innerHTML = '<tr><td colspan="8">无法读取看板数据。</td></tr>';
    console.error("Unable to load dashboard data", error);
  }
}

load();
