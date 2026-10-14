const $=s=>document.querySelector(s);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num=v=>v===null||v===undefined||v===''?'—':Number(v).toLocaleString('zh-CN',{maximumFractionDigits:4});
const money=v=>v===null||v===undefined?'—':'$'+Number(v).toLocaleString('zh-CN',{maximumFractionDigits:4});
const tokenText=v=>{const n=Number(v||0);return n>=1e12?(n/1e12).toFixed(2)+'T':n>=1e9?(n/1e9).toFixed(2)+'B':n>=1e6?(n/1e6).toFixed(2)+'M':num(n)};
const link=(url,label)=>url?`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)} ↗</a>`:esc(label);
const modules={
  overview:{title:'AI 行业总览',subtitle:'上游硬件、中游模型与下游产业事件。'},
  news:{title:'AI 产业新闻',subtitle:'官方、监管与权威媒体的可核查事件。',paths:['news']},
  token:{title:'Token 自然周',subtitle:'OpenRouter 周一至周日用量与模型份额。',paths:['token','token-usage']},
  models:{title:'模型 API 价格',subtitle:'目录输入价、输出价、上下文与模态。',paths:['models','token-prices']},
  gpu:{title:'GPU 云实例报价',subtitle:'厂商、GPU、区域和计费方式的可比报价。',paths:['gpu','gpu-prices']},
  storage:{title:'存储硬件价格',subtitle:'DDR、GDDR、NAND、SSD 与 HBM 租赁代理。',paths:['storage']},
  'hugging-face':{title:'Hugging Face 趋势',subtitle:'三期快照差分与新上榜观察。',paths:['hugging-face']},
  github:{title:'GitHub AI 项目',subtitle:'Trending、Topic、官方仓库与 Stars 变化。',paths:['github']},
  'x-watch':{title:'X 账号动态',subtitle:'50 个 AI 产业核心账号的近七天动态；使用本机 Chrome 登录态采集。',paths:['x-watch']}
};
const state={module:'overview',manifest:null,cache:new Map(),pending:new Map(),query:'',filter:'all',weeks:26,selected:null,dataView:'summary',xPriority:false,xCategory:'all',xAccount:'all'};

function cards(items){$('#cards').innerHTML=items.map(([name,value,note])=>`<article class="card"><span>${esc(name)}</span><strong>${esc(value)}</strong><small>${esc(note||'')}</small></article>`).join('');}
function table(headers,rows){return `<div class="table-wrap"><table><thead><tr>${headers.map(h=>`<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map(cell=>`<td>${cell??'—'}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;}
function setStatus(text,type=''){ $('#status').innerHTML=text?`<div class="notice ${type}">${esc(text)}</div>`:''; }
function moduleStatus(name){return state.manifest?.modules?.[name]||state.manifest?.sources?.find?.(item=>item.module===name)||null;}
function isStale(status){return status&&['stale','partial','unavailable','error'].includes(status.status);}
function updateUrl(){const url=new URL(location.href);url.hash=state.module;state.query?url.searchParams.set('q',state.query):url.searchParams.delete('q');state.filter!=='all'?url.searchParams.set('filter',state.filter):url.searchParams.delete('filter');history.replaceState(null,'',url);}

async function fetchJson(path){const response=await fetch(path+(path.includes('?')?'&':'?')+'t='+Date.now(),{cache:'no-store'});if(!response.ok)throw new Error(`HTTP ${response.status}`);return response.json();}
async function loadManifest(force=false){if(state.manifest&&!force)return state.manifest;try{state.manifest=await fetchJson('data/manifest.json');}catch{state.manifest=await fetchJson('data/inventory.json');}return state.manifest;}
async function loadModule(name,force=false){if(force)state.cache.delete(name);if(state.cache.has(name))return state.cache.get(name);if(state.pending.has(name))return state.pending.get(name);const promise=(async()=>{let last;const paths=name==='x-watch'?['x-watch/latest.json']:(modules[name].paths||[]).map(path=>`data/${path}/latest.json`);for(const path of paths){try{const payload=await fetchJson(path);if(!Array.isArray(payload.rows))throw new Error('rows 契约错误');state.cache.set(name,payload);return payload;}catch(error){last=error;}}throw last||new Error('没有模块文件');})();state.pending.set(name,promise);try{return await promise;}finally{state.pending.delete(name);}}

function filterRows(rows,keys,categoryKey=''){const q=state.query.toLowerCase();return rows.filter(row=>{const text=keys.map(k=>row[k]??'').join(' ').toLowerCase();const category=categoryKey?row[categoryKey]:'all';return (!q||text.includes(q))&&(state.filter==='all'||String(category)===state.filter);});}
function renderFilters(rows,categoryKey,extras=''){const categories=[...new Set(rows.map(row=>row[categoryKey]).filter(Boolean))].sort();$('#filters').innerHTML=`<label><span class="sr-only">搜索</span><input id="search" type="search" value="${esc(state.query)}" placeholder="搜索关键词"></label>${categories.length?`<label><span class="sr-only">分类</span><select id="filter"><option value="all">全部分类</option>${categories.map(value=>`<option ${state.filter===String(value)?'selected':''}>${esc(value)}</option>`).join('')}</select></label>`:''}${extras}`;$('#search')?.addEventListener('input',event=>{state.query=event.target.value;updateUrl();renderCurrent();});$('#filter')?.addEventListener('change',event=>{state.filter=event.target.value;updateUrl();renderCurrent();});}
function isNumber(value){return value!==null&&value!==undefined&&value!==''&&Number.isFinite(Number(value));}
function validNumbers(values){return values.filter(isNumber).map(Number);}
function average(values){const clean=validNumbers(values);return clean.length?clean.reduce((sum,value)=>sum+value,0)/clean.length:null;}
function median(values){const clean=validNumbers(values).sort((a,b)=>a-b);if(!clean.length)return null;const middle=Math.floor(clean.length/2);return clean.length%2?clean[middle]:(clean[middle-1]+clean[middle])/2;}
function resultBlock(title,note,body){return `<div class="result-head"><div><b>${esc(title)}</b><small>${esc(note)}</small></div><div class="segmented" role="group" aria-label="数据展示"><button data-data-view="summary" class="${state.dataView==='summary'?'active':''}">基准概览</button><button data-data-view="detail" class="${state.dataView==='detail'?'active':''}">全部明细</button></div></div>${body}`;}
function bindDataView(){document.querySelectorAll('[data-data-view]').forEach(button=>button.onclick=()=>{state.dataView=button.dataset.dataView;renderCurrent();});}
function grouped(rows,keyFor){const groups=new Map();rows.forEach(row=>{const key=keyFor(row);if(!groups.has(key))groups.set(key,[]);groups.get(key).push(row);});return groups;}
function svgLine(points,key='price'){const clean=points.filter(p=>p[key]!==null&&p[key]!==undefined);if(clean.length<2)return '<div class="empty">从本次采集开始积累历史，至少两个快照后显示趋势。</div>';const values=clean.map(p=>Number(p[key])),min=Math.min(...values),max=Math.max(...values),span=max-min||1;const coords=clean.map((p,i)=>`${30+i*(640/Math.max(1,clean.length-1))},${170-(Number(p[key])-min)/span*130}`).join(' ');return `<svg viewBox="0 0 700 205" role="img" aria-label="价格历史折线图"><line x1="30" y1="170" x2="670" y2="170" class="axis"/><polyline points="${coords}" class="line"/><text x="30" y="195">${esc(clean[0].date)}</text><text x="610" y="195">${esc(clean.at(-1).date)}</text><text x="35" y="28">${num(max)}</text><text x="35" y="165">${num(min)}</text></svg>`;}

function renderOverview(){const map=state.manifest?.modules||{};const entries=Object.entries(map).filter(([name])=>name!=='restore'&&!name.startsWith('translation'));const ok=entries.filter(([,item])=>['ok','partial','stale'].includes(item.status)).length;const rows=entries.map(([name,item])=>[esc(modules[name]?.title||name),`<span class="status ${esc(item.status)}">${esc(item.status)}</span>`,num(item.rows),esc(item.snapshot_date||item.last_success_at_utc?.slice(0,10)||'—')]);cards([['可用板块',`${ok}/${entries.length}`,'单源失败不阻断整站'],['最新快照',state.manifest?.snapshot_date||'—','北京时间每日15:48后更新'],['历史保留',`${state.manifest?.history_days||90}天`,'压缩快照存于 Releases']]);$('#filters').innerHTML='';$('#chart').innerHTML='';$('#content').innerHTML=table(['板块','状态','记录数','数据日期'],rows);$('#method').textContent='页面按需读取各板块 JSON；浏览器不会直接携带密钥请求外部 API。';}

function renderNews(p){const rows=filterRows(p.rows,['title','summary','source','chain_category'],'chain_category');renderFilters(p.rows,'chain_category');cards([['本期事件',num(p.rows.length),'不足时不以低质量内容补数'],['官方/一级来源',num(p.rows.filter(r=>r.source_tier===1).length),'官方、IR、监管与权威技术社区'],['待翻译',num(p.translation_pending||0),'失败内容不伪装为中文']]);$('#chart').innerHTML='';$('#content').innerHTML=`<div class="news-grid">${rows.map(r=>`<article class="news"><div class="meta"><span class="tag">${esc(r.chain_category||r.region)}</span><span>${esc(r.source)}</span><time>${esc((r.published_at_utc||'').slice(0,10))}</time></div><h3>${link(r.url,r.title)}</h3><p>${esc(r.summary)}</p></article>`).join('')}</div>`;}

function tokenDrawer(week){$('#drawer-title').textContent=week.label;const rows=[...(week.top_models||[]).map(r=>[link('https://openrouter.ai/rankings',r.id),tokenText(r.tokens),r.share===null?'—':(r.share*100).toFixed(2)+'%']),['Others',tokenText(week.others_tokens),'—']];$('#drawer-content').innerHTML=table(['模型','Token','份额'],rows);$('#drawer').showModal();}
function renderToken(p){const all=p.rows||[],rows=all.slice(-state.weeks);renderFilters([], '', `<div class="segmented" role="group" aria-label="周数">${[13,26,52].map(n=>`<button data-weeks="${n}" class="${state.weeks===n?'active':''}">${n}周</button>`).join('')}</div>`);document.querySelectorAll('[data-weeks]').forEach(button=>button.onclick=()=>{state.weeks=Number(button.dataset.weeks);renderCurrent();});const max=Math.max(1,...rows.map(r=>Number(r.total_tokens||0)));$('#chart').innerHTML=`<div class="bar-chart" aria-label="Token 自然周柱状图">${rows.map(r=>`<button class="bar ${r.status==='preview'?'preview':''}" data-week="${esc(r.id)}" title="${esc(r.label)} · ${tokenText(r.total_tokens)}"><i style="height:${Math.max(2,Number(r.total_tokens||0)/max*160)}px"></i><small>${esc(r.week_start?.slice(5))}</small></button>`).join('')}</div>`;document.querySelectorAll('[data-week]').forEach(button=>button.onclick=()=>tokenDrawer(rows.find(r=>r.id===button.dataset.week)));const latest=[...all].reverse().find(r=>r.status==='complete')||all.at(-1)||{};cards([['最近完整周',tokenText(latest.total_tokens),'输入+输出，仅 OpenRouter'],['统计区间',latest.label||'—','UTC 周一至周日'],['观察周数',num(rows.length),'点击柱查看 Top 20 + Others']]);$('#content').innerHTML=table(['自然周','状态','观察日','Token','明细'],rows.slice().reverse().map(r=>[esc(r.label),esc(r.status),num(r.observed_days),tokenText(r.total_tokens),`<button data-week-row="${esc(r.id)}">查看</button>`]));document.querySelectorAll('[data-week-row]').forEach(button=>button.onclick=()=>tokenDrawer(rows.find(r=>r.id===button.dataset.weekRow)));}

function modelScatter(rows){const priced=rows.filter(r=>r.input_usd_per_million>0&&r.output_usd_per_million>0);if(!priced.length)return '<div class="empty">没有同时包含输入价与输出价的模型。</div>';const logs=priced.flatMap(r=>[Math.log10(r.input_usd_per_million),Math.log10(r.output_usd_per_million)]),min=Math.min(...logs),max=Math.max(...logs),span=max-min||1;return `<div class="scatter-hint" id="model-point-label" aria-live="polite">悬停或聚焦圆点查看模型与价格</div><svg viewBox="0 0 700 310" role="img" aria-label="模型输入输出价格散点图"><line x1="55" y1="270" x2="680" y2="270" class="axis"/><line x1="55" y1="20" x2="55" y2="270" class="axis"/>${priced.slice(0,300).map(r=>{const x=55+(Math.log10(r.input_usd_per_million)-min)/span*620,y=270-(Math.log10(r.output_usd_per_million)-min)/span*245,label=`${r.name||r.id} · 输入 ${money(r.input_usd_per_million)} · 输出 ${money(r.output_usd_per_million)}`;return `<circle cx="${x}" cy="${y}" r="3.2" tabindex="0" aria-label="${esc(label)}" data-point-label="${esc(label)}"><title>${esc(label)}</title></circle>`}).join('')}<text x="520" y="300">输入价（对数）→</text><text x="8" y="20">输出价</text></svg>`;}
function bindModelScatter(){const label=$('#model-point-label');document.querySelectorAll('#chart circle[data-point-label]').forEach(point=>{const show=()=>{document.querySelectorAll('#chart circle.active').forEach(item=>item.classList.remove('active'));point.classList.add('active');if(label)label.textContent=point.dataset.pointLabel;};point.addEventListener('pointerenter',show);point.addEventListener('focus',show);point.addEventListener('click',show);});}
function renderModels(p){
  const rows=filterRows(p.rows,['id','name','vendor','input_modalities','output_modalities'],'vendor');
  renderFilters(p.rows,'vendor');
  const inputs=rows.map(r=>r.input_usd_per_million).filter(v=>v!==null&&v!==undefined);
  const outputs=rows.map(r=>r.output_usd_per_million).filter(v=>v!==null&&v!==undefined);
  cards([['当前模型',num(rows.length),`${num(new Set(rows.map(r=>r.vendor)).size)} 个厂商`],['平均输入价',money(average(inputs)),`中位数 ${money(median(inputs))} / 百万 Token`],['平均输出价',money(average(outputs)),`中位数 ${money(median(outputs))} / 百万 Token`]]);
  $('#chart').innerHTML=modelScatter(rows);
  bindModelScatter();
  let body;
  if(state.dataView==='detail'){
    body=table(['模型','厂商','输入价/M','输出价/M','上下文','输入模态'],rows.slice(0,500).map(r=>[link(r.url,r.name||r.id),esc(r.vendor),money(r.input_usd_per_million),money(r.output_usd_per_million),num(r.context_length),esc((r.input_modalities||r.modalities||[]).join(', '))]));
  }else{
    const priced=rows.filter(r=>isNumber(r.input_usd_per_million)&&isNumber(r.output_usd_per_million)).map(r=>({...r,total_price:Number(r.input_usd_per_million)+Number(r.output_usd_per_million)})).sort((a,b)=>a.total_price-b.total_price);
    const points=[['最低价',0],['25 分位',.25],['中位数',.5],['75 分位',.75],['最高价',1]];
    const benchmarks=[];const seen=new Map();
    points.forEach(([label,position])=>{const row=priced[Math.round((priced.length-1)*position)];if(!row)return;const key=row.id||row.name;if(seen.has(key)){seen.get(key).labels.push(label);}else{const entry={row,labels:[label]};seen.set(key,entry);benchmarks.push(entry);}});
    const longest=rows.filter(r=>isNumber(r.context_length)).sort((a,b)=>Number(b.context_length)-Number(a.context_length))[0];
    if(longest){const key=longest.id||longest.name;if(seen.has(key))seen.get(key).labels.push('最长上下文');else benchmarks.push({row:longest,labels:['最长上下文']});}
    body=benchmarks.length?table(['基准','模型','厂商','输入价/M','输出价/M','合计价/M','上下文'],benchmarks.map(({row,labels})=>[esc(labels.join(' / ')),link(row.url,row.name||row.id),esc(row.vendor),money(row.input_usd_per_million),money(row.output_usd_per_million),money(Number(row.input_usd_per_million||0)+Number(row.output_usd_per_million||0)),num(row.context_length)])):'<div class="empty">当前筛选没有可计算的模型报价。</div>';
  }
  $('#content').innerHTML=resultBlock('价格分位基准','默认提取最低、四分位与最长上下文样本；可切换查看完整目录。',body);bindDataView();
}

function renderGpu(p){
  const rows=filterRows(p.rows,['provider','gpu','region','sku','billing'],'provider');renderFilters(p.rows,'provider');
  const providers=[...new Set(rows.map(r=>r.provider))],gpus=[...new Set(rows.map(r=>r.gpu))];
  const cells=gpus.map(gpu=>`<div class="heat-row"><b>${esc(gpu)}</b>${providers.map(provider=>{const quotes=validNumbers(rows.filter(r=>r.gpu===gpu&&r.provider===provider).map(r=>r.usd_per_gpu_hour)),min=quotes.length?Math.min(...quotes):null;return `<span title="${esc(provider)}">${min===null?'—':money(min)}</span>`}).join('')}</div>`).join('');
  const hourly=rows.map(r=>r.usd_per_gpu_hour).filter(v=>v!==null&&v!==undefined);
  cards([['当前报价',num(rows.length),`${num(providers.length)} 个云厂商 · ${num(gpus.length)} 种 GPU`],['平均单 GPU 时价',money(average(hourly)),'仅统计可比的 USD/GPU·h'],['中位单 GPU 时价',money(median(hourly)),'降低极端规格对判断的干扰']]);
  $('#chart').innerHTML=rows.length?`<div class="heatmap" style="--heat-cols:${Math.max(1,providers.length)}"><div class="heat-head"><b>GPU</b>${providers.map(v=>`<span>${esc(v)}</span>`).join('')}</div>${cells}</div>`:'<div class="empty">当前筛选没有 GPU 报价。</div>';
  let body;
  if(state.dataView==='detail'){
    body=table(['厂商','GPU','区域','计费','显存','实例$/h','单GPU$/h'],rows.slice(0,600).map(r=>[link(r.url,r.provider),esc(r.gpu),esc(r.region),esc(r.billing),r.memory_gb?num(r.memory_gb)+' GB':'—',money(r.instance_usd_hour),money(r.usd_per_gpu_hour)]));
  }else{
    const summaries=[...grouped(rows,r=>`${r.gpu}\u0000${r.billing||'未标注'}`).values()].map(group=>{const prices=validNumbers(group.map(r=>r.usd_per_gpu_hour));return {gpu:group[0].gpu,billing:group[0].billing||'未标注',count:prices.length,providers:new Set(group.map(r=>r.provider)).size,min:prices.length?Math.min(...prices):null,avg:average(prices),mid:median(prices),max:prices.length?Math.max(...prices):null};}).sort((a,b)=>String(a.gpu).localeCompare(String(b.gpu),'zh-CN')||String(a.billing).localeCompare(String(b.billing),'zh-CN'));
    body=summaries.length?table(['GPU','计费方式','样本/厂商','最低$/h','平均$/h','中位$/h','最高$/h'],summaries.map(r=>[esc(r.gpu),esc(r.billing),`${num(r.count)} / ${num(r.providers)}`,money(r.min),money(r.avg),money(r.mid),money(r.max)])):'<div class="empty">当前筛选没有可计算的 GPU 报价。</div>';
  }
  $('#content').innerHTML=resultBlock('GPU / 计费基准','按 GPU 型号与计费方式聚合，避免区域和实例规格一股脑展开。',body);bindDataView();
}

function storageComparable(row){if(row.category==='SSD'&&isNumber(row.usd_per_tb))return {value:Number(row.usd_per_tb),unit:'USD/TB'};if(isNumber(row.price))return {value:Number(row.price),unit:`${row.currency||''} ${row.unit||''}`.trim()};return null;}
function storageMetric(value,unit){return /^USD(?:\b|\/)/i.test(unit||'')?money(value):num(value);}
function renderStorage(p){
  const rows=filterRows(p.rows,['category','item','market','source'],'category');renderFilters(p.rows,'category');
  const selected=rows.find(r=>r.id===state.selected)||rows[0];state.selected=selected?.id||null;const history=selected?.history||[];
  const hbm=rows.filter(r=>r.category==='HBM rental proxy').map(r=>r.price);const ssd=rows.filter(r=>r.category==='SSD').map(r=>r.usd_per_tb);
  cards([['当前样本',num(rows.length),`${num(new Set(rows.map(r=>r.category)).size)} 个价格类别`],['HBM 代理中位价',money(median(hbm)),'USD / HBM-GB·hour，含计算成本'],['SSD 中位价',money(median(ssd)),'统一换算为 USD/TB']]);
  $('#chart').innerHTML=selected?`<div class="chart-title"><b>${esc(selected.item)}</b><span>${selected.currency==='USD'?money(selected.price):num(selected.price)} ${esc(selected.unit)}</span></div>${svgLine(history)}`:'<div class="empty">暂无合规的免费价格数据。</div>';
  let body;
  if(state.dataView==='detail'){
    body=table(['类别','项目','价格','单位','较前次','口径'],rows.map(r=>[`<button class="link-button" data-storage="${esc(r.id)}">${esc(r.category)}</button>`,link(r.url,r.item),r.currency==='USD'?money(r.price):num(r.price),esc(r.unit),r.change_percent==null?'—':`${r.change_percent>0?'+':''}${num(r.change_percent)}%`,esc(r.quote_type)]));
  }else{
    const comparable=rows.map(row=>({row,metric:storageComparable(row)})).filter(item=>item.metric);
    const summaries=[...grouped(comparable,item=>`${item.row.category}\u0000${item.metric.unit}`).values()].map(group=>{const values=group.map(item=>item.metric.value),mid=median(values),representative=group.reduce((best,item)=>Math.abs(item.metric.value-mid)<Math.abs(best.metric.value-mid)?item:best);return {category:group[0].row.category,unit:group[0].metric.unit,count:values.length,min:Math.min(...values),avg:average(values),mid,max:Math.max(...values),id:representative.row.id};}).sort((a,b)=>String(a.category).localeCompare(String(b.category),'zh-CN'));
    body=summaries.length?table(['类别','可比单位','样本','最低','平均','中位','最高'],summaries.map(r=>[`<button class="link-button" data-storage="${esc(r.id)}">${esc(r.category)}</button>`,esc(r.unit),num(r.count),storageMetric(r.min,r.unit),storageMetric(r.avg,r.unit),storageMetric(r.mid,r.unit),storageMetric(r.max,r.unit)])):'<div class="empty">当前筛选没有可计算的存储价格。</div>';
  }
  $('#content').innerHTML=resultBlock('类别价格基准','同一类别、同一单位分别聚合；SSD 统一换算为 USD/TB。点击类别查看中位样本趋势。',body);bindDataView();
  document.querySelectorAll('[data-storage]').forEach(button=>button.onclick=()=>{state.selected=button.dataset.storage;renderCurrent();});
}

function renderHf(p){const rows=filterRows(p.rows,['id','task_type','use_case_zh','remark'],'task_type');renderFilters(p.rows,'task_type');cards([['筛选结果',num(rows.length),`总计 ${num(p.rows.length)} 个模型`],['完整历史模型',num(rows.filter(r=>r.status==='exact').length),'当前结果中可进行三期差分'],['观察模型',num(rows.filter(r=>r.status==='watch').length),'历史不足，不伪造增量']]);$('#chart').innerHTML='';$('#content').innerHTML=rows.length?table(['排名','模型','任务','本期下载','加速度','说明'],rows.slice(0,500).map(r=>[num(r.rank),link(r.model_url,r.id),esc(r.task_type),num(r.downloads_this_period),num(r.download_acceleration),esc(r.download_note||r.use_case_zh)])):'<div class="empty">没有符合当前分类和关键词的模型。</div>';}
function renderGithub(p){const rows=filterRows(p.rows,['full_name','domain','use_case_zh','description_raw'],'domain');renderFilters(p.rows,'domain');cards([['AI 项目',num(p.rows.length),'Trending、Topic 与官方仓库'],['Stars 净变化',num(p.rows.reduce((sum,r)=>sum+(r.stars_net_change||0),0)),'与上次成功快照比较'],['最新 Release',num(p.rows.filter(r=>r.latest_release).length),'来自官方仓库 API']]);$('#chart').innerHTML='';$('#content').innerHTML=table(['项目','领域','来源','总 Stars','净变化','用途'],rows.map(r=>[link(r.url,r.full_name),esc(r.domain),esc(r.source_type||'trending'),num(r.stars),num(r.stars_net_change),esc(r.use_case_zh)]));}

function xDate(value){const date=new Date(value);return Number.isNaN(date.getTime())?'时间未知':date.toLocaleString('zh-CN',{timeZone:'Asia/Shanghai',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false});}
function xUrl(value){return /^https:\/\/x\.com\/[A-Za-z0-9_]+\/status\/\d+$/.test(value||'')?value:'';}
function positionXMenus(picker=$('#x-category-picker')){
  if(!picker||window.matchMedia('(max-width: 700px)').matches)return;
  const panel=picker.querySelector('.x-category-panel');
  if(!panel)return;
  const edge=8;
  picker.classList.remove('opens-left');
  const pickerRect=picker.getBoundingClientRect();
  const panelWidth=panel.getBoundingClientRect().width||Math.max(278,panel.scrollWidth);
  if(pickerRect.left+panelWidth>window.innerWidth-edge&&pickerRect.right-panelWidth>=edge)picker.classList.add('opens-left');
  picker.querySelectorAll('.x-category-entry').forEach(entry=>{
    const submenu=entry.querySelector('.x-account-submenu');
    const rect=entry.getBoundingClientRect();
    const measuredWidth=submenu.getBoundingClientRect().width;
    const submenuWidth=measuredWidth||360;
    const roomRight=window.innerWidth-rect.right-edge;
    const roomLeft=rect.left-edge;
    const opensLeft=roomRight<submenuWidth&&roomLeft>roomRight;
    entry.classList.toggle('opens-left',opensLeft);
    const available=Math.max(180,Math.min(360,opensLeft?roomLeft:roomRight));
    submenu.style.setProperty('--x-submenu-max-width',`${available}px`);
  });
}
window.addEventListener('resize',()=>{if(state.module==='x-watch')positionXMenus();},{passive:true});
function renderXWatch(p){
  const accounts=p.accounts||[];const categories=[...new Set(accounts.map(account=>account.category))];
  const returnedHandles=new Set(p.rows.map(row=>String(row.handle).toLowerCase()));
  const failedHandles=new Set((p.failed_accounts||[]).map(handle=>String(handle).toLowerCase()));
  const currentAccount=accounts.find(account=>account.handle.toLowerCase()===state.xAccount);
  const selection=state.xAccount!=='all'?`${currentAccount?.category||state.xCategory} › ${currentAccount?.name||state.xAccount}`:state.xCategory==='all'?'全部分类':state.xCategory;
  const picker=`<div class="x-category-picker" id="x-category-picker"><button class="x-category-trigger" type="button" aria-haspopup="true">${esc(selection)} <span aria-hidden="true">⌄</span></button><div class="x-category-panel" role="menu"><button type="button" class="x-all-categories" data-x-all role="menuitem">全部分类</button>${categories.map(category=>{const children=accounts.filter(account=>account.category===category);return `<div class="x-category-entry"><button type="button" class="x-category-option" data-x-category="${esc(category)}" aria-haspopup="true" role="menuitem">${esc(category)} <span aria-hidden="true">›</span></button><div class="x-account-submenu" role="menu" aria-label="${esc(category)}账号"><button type="button" data-x-account="all" data-x-account-category="${esc(category)}" role="menuitem">全部账号</button>${children.map(account=>{const handle=account.handle.toLowerCase();const note=failedHandles.has(handle)?' · 查询失败':returnedHandles.has(handle)?'':' · 本期无动态';return `<button type="button" data-x-account="${esc(account.handle)}" data-x-account-category="${esc(category)}" role="menuitem">${esc(account.name)} <small>@${esc(account.handle)}${note}</small></button>`}).join('')}</div></div>`}).join('')}</div></div>`;
  const extras=`${picker}<label><span class="sr-only">优先关注筛选</span><select id="x-scope" aria-label="优先关注筛选"><option value="all">全部 50 个账号</option><option value="priority" ${state.xPriority?'selected':''}>优先关注 15 个</option></select></label>`;
  renderFilters(p.rows,'',extras);
  const categoryPicker=$('#x-category-picker');
  categoryPicker?.addEventListener('pointerover',event=>{const entry=event.target.closest('.x-category-entry');if(entry)positionXMenus(categoryPicker);});
  categoryPicker?.addEventListener('focusin',()=>positionXMenus(categoryPicker));
  requestAnimationFrame(()=>positionXMenus(categoryPicker));
  $('#x-scope')?.addEventListener('change',event=>{state.xPriority=event.target.value==='priority';state.xAccount='all';state.xCategory='all';renderCurrent();});
  $('#x-category-picker')?.querySelector('[data-x-all]')?.addEventListener('click',()=>{state.xCategory='all';state.xAccount='all';renderCurrent();});
  $('#x-category-picker')?.querySelectorAll('[data-x-category]').forEach(button=>button.addEventListener('click',()=>{const entry=button.closest('.x-category-entry');entry.classList.toggle('is-open');}));
  $('#x-category-picker')?.querySelectorAll('[data-x-account]')?.forEach(button=>button.addEventListener('click',()=>{state.xCategory=button.dataset.xAccountCategory;state.xAccount=button.dataset.xAccount.toLowerCase();state.xPriority=false;renderCurrent();}));
  let rows=filterRows(p.rows,['text','handle','account_name','focus','category']);
  if(state.xCategory!=='all')rows=rows.filter(row=>row.category===state.xCategory);
  if(state.xAccount!=='all')rows=rows.filter(row=>row.handle.toLowerCase()===state.xAccount);
  if(state.xPriority)rows=rows.filter(row=>row.priority);
  const returned=p.returned_accounts_count??new Set(p.rows.map(row=>String(row.handle).toLowerCase())).size;
  const noActivity=(p.no_activity_accounts||[]).length;const failed=(p.failed_accounts||[]).length;
  const noActivityNote=`${noActivity} 个账号近7天未发布${failed?` · ${failed} 个账号查询失败`:''}`;
  cards([['本期动态',num(p.rows.length),`最近 ${num(p.days||7)} 天`],['返回账号',`${num(returned)}/${num(p.accounts_count||50)}`,noActivityNote],['优先账号',num(p.priority_accounts_count||15),'来自上传清单的精选子集']]);
  $('#chart').innerHTML='';
  if(!rows.length&&state.xAccount!=='all'&&(!returnedHandles.has(state.xAccount)||state.query)){
    const account=currentAccount;const message=failedHandles.has(state.xAccount)?'查询失败，暂不能判断本期动态':state.query?'没有符合搜索条件的动态':'本期无动态';$('#content').innerHTML=`<div class="x-grid"><article class="x-post x-no-activity"><div class="x-head"><div><strong>${esc(account?.name||state.xAccount)}</strong><span>@${esc(account?.handle||state.xAccount)}</span></div></div><p class="x-no-activity-label">${esc(message)}</p></article></div>`;
  }else{$('#content').innerHTML=rows.length?`<div class="x-grid">${rows.map(row=>{const url=xUrl(row.url);return `<article class="x-post"><div class="x-head"><div><strong>${esc(row.account_name||row.handle)}</strong><span>@${esc(row.handle)} · ${esc(xDate(row.published_at))}</span></div>${row.priority?'<span class="tag">优先关注</span>':''}</div><p class="x-focus">${esc(row.focus||'')}</p><p class="x-text">${esc(row.text)}</p><div class="x-foot"><span>${row.likes==null?'点赞 —':'点赞 '+num(row.likes)} · ${row.views==null?'浏览 —':'浏览 '+num(row.views)} · ${row.oembed_status==='ok'?'oEmbed 已复核':'Chrome 页面正文'}</span>${url?`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">查看 X 原文 ↗</a>`:''}</div></article>`}).join('')}</div>`:'<div class="empty">没有符合搜索条件的动态。</div>';}
  $('#method').textContent=(p.methodology||'')+` 清单 ${p.accounts_count||50} 个账号，本轮成功查询 ${(p.checked_accounts||[]).length} 个${failed?`，失败 ${failed} 个`:''}；采集完成时间 ${p.finished_at?xDate(p.finished_at):'—'}。`;
}

function renderPayload(name,p){if(name==='news')renderNews(p);else if(name==='token')renderToken(p);else if(name==='models')renderModels(p);else if(name==='gpu')renderGpu(p);else if(name==='storage')renderStorage(p);else if(name==='hugging-face')renderHf(p);else if(name==='github')renderGithub(p);else if(name==='x-watch')renderXWatch(p);if(name!=='x-watch')$('#method').textContent=p.methodology||'';}
async function renderCurrent(){const name=state.module,info=modules[name];$('#title').textContent=info.title;$('#subtitle').textContent=info.subtitle;$('#panel-title').textContent=name==='overview'?'数据源与板块':'数据与图表';$('#date').textContent=state.manifest?.snapshot_date||'读取中';document.querySelectorAll('[data-module]').forEach(button=>button.classList.toggle('active',button.dataset.module===name));const status=moduleStatus(name);setStatus(isStale(status)?`本板块状态：${status.status}。${status.error||'部分来源不可用，当前展示最近可用数据。'}`:'',isStale(status)?'warning':'');if(name==='overview'){renderOverview();return;}$('#chart').innerHTML='<div class="loading">读取模块数据…</div>';$('#content').innerHTML='';try{const payload=await loadModule(name);if(state.module!==name)return;renderPayload(name,payload);}catch(error){if(state.module!==name)return;$('#filters').innerHTML='';$('#chart').innerHTML='';$('#content').innerHTML=`<div class="empty">${esc(error.message)}。该板块尚无可发布快照。</div>`;$('#method').textContent='';}}
function health(){const modulesMap=state.manifest?.modules||Object.fromEntries((state.manifest?.sources||[]).map(item=>[item.module,item]));$('#health').innerHTML=table(['模块','状态','记录数','最后成功','异常'],Object.entries(modulesMap).map(([name,item])=>[esc(modules[name]?.title||name),`<span class="status ${esc(item.status)}">${esc(item.status)}</span>`,num(item.rows),esc(item.last_success_at_utc?.replace('T',' ').slice(0,19)||item.snapshot_date||'—'),esc(item.error||'')]));const terms=state.manifest?.terms||{};$('#terms').innerHTML=Object.entries(terms).map(([term,note])=>`<dt>${esc(term)}</dt><dd>${esc(note)}</dd>`).join('');}
async function boot(){const params=new URLSearchParams(location.search);state.query=params.get('q')||'';state.filter=params.get('filter')||'all';try{await loadManifest();health();}catch(error){setStatus('数据清单读取失败：'+error.message,'warning');}const requested=location.hash.slice(1);state.module=modules[requested]?requested:'overview';renderCurrent();}
document.querySelectorAll('[data-module]').forEach(button=>button.addEventListener('click',()=>{state.module=button.dataset.module;state.query='';state.filter='all';state.selected=null;state.dataView='summary';state.xPriority=false;state.xCategory='all';state.xAccount='all';updateUrl();renderCurrent();}));
window.addEventListener('hashchange',()=>{const name=location.hash.slice(1);if(modules[name]&&name!==state.module){state.module=name;state.dataView='summary';renderCurrent();}});
$('#refresh').addEventListener('click',async()=>{$('#refresh').disabled=true;try{await loadManifest(true);if(state.module!=='overview')await loadModule(state.module,true);health();renderCurrent();}finally{$('#refresh').disabled=false;}});
$('#show-health').addEventListener('click',()=>{$('#health-panel').hidden=false;$('#health-panel').scrollIntoView({behavior:'smooth'});});$('#close-health').addEventListener('click',()=>$('#health-panel').hidden=true);$('#close-drawer').addEventListener('click',()=>$('#drawer').close());
try{document.body.classList.toggle('dark',localStorage.getItem('ai-theme')==='dark');}catch{}
$('#theme').addEventListener('click',()=>{document.body.classList.toggle('dark');try{localStorage.setItem('ai-theme',document.body.classList.contains('dark')?'dark':'light');}catch{}});
boot();
