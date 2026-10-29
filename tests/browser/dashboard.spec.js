const {test,expect}=require('@playwright/test');
const manifest={schema_version:2,snapshot_date:'2026-10-05',history_days:90,modules:{token:{status:'ok',rows:3},models:{status:'ok',rows:4},gpu:{status:'ok',rows:3},storage:{status:'ok',rows:4},'hugging-face':{status:'ok',rows:3},'github-trending':{status:'ok',rows:15},github:{status:'ok',rows:2},'ai-financials':{status:'ok',rows:1},'ai-frontier':{status:'partial',rows:2}},terms:{HBM:'高带宽内存'}};
const token={schema_version:2,dataset:'token_usage_weekly',status:'ok',rows:[
  {id:'2026-09-14',week_start:'2026-09-14',label:'2026-09-14—2026-09-20',status:'complete',observed_days:7,total_tokens:'1000',top_models:[{id:'openai/alpha',tokens:'600',share:.6},{id:'anthropic/beta',tokens:'300',share:.3}],others_tokens:'100'},
  {id:'2026-09-21',week_start:'2026-09-21',label:'2026-09-21—2026-09-27',status:'complete',observed_days:7,total_tokens:'800',top_models:[{id:'openai/alpha',tokens:'300',share:.375},{id:'google/gamma',tokens:'400',share:.5}],others_tokens:'100'},
  {id:'2026-09-28',week_start:'2026-09-28',label:'2026-09-28—2026-10-04',status:'preview',observed_days:2,total_tokens:'180',top_models:[{id:'google/gamma',tokens:'100',share:.5556},{id:'anthropic/beta',tokens:'40',share:.2222}],others_tokens:'40'}
]};
const models={schema_version:2,dataset:'model_api_prices',status:'ok',rows:[
  {id:'openai/mini',name:'OpenAI Mini',vendor:'OpenAI',input_usd_per_million:.2,output_usd_per_million:.8,context_length:128000,input_modalities:['text'],url:'https://example.com/openai-mini'},
  {id:'openai/pro',name:'OpenAI Pro',vendor:'OpenAI',input_usd_per_million:2,output_usd_per_million:8,context_length:200000,input_modalities:['text'],url:'https://example.com/openai-pro'},
  {id:'qwen/fast',name:'Qwen Fast',vendor:'Qwen',input_usd_per_million:.1,output_usd_per_million:.4,context_length:32000,input_modalities:['text'],url:'https://example.com/qwen-fast'},
  {id:'qwen/long',name:'Qwen Long',vendor:'Qwen',input_usd_per_million:.4,output_usd_per_million:1.6,context_length:1000000,input_modalities:['text'],url:'https://example.com/qwen-long'}
]};
const gpu={schema_version:2,dataset:'gpu_cloud_prices',status:'ok',price_history:{'Azure|H100 80GB|on-demand':[{date:'2026-10-03',p25:3,median:4,p75:5,sample_count:2},{date:'2026-10-04',p25:3.5,median:5,p75:6,sample_count:2}], 'Lambda|A100 80GB|on-demand':[{date:'2026-10-03',p25:1.5,median:2,p75:2.5,sample_count:1},{date:'2026-10-04',p25:1.7,median:2.2,p75:2.8,sample_count:1}]},rows:[
  {provider:'Azure',gpu:'H100 80GB',region:'eastus',sku:'h100-a',billing:'on-demand',memory_gb:80,instance_usd_hour:8,usd_per_gpu_hour:4,url:'https://example.com/azure'},
  {provider:'Azure',gpu:'H100 80GB',region:'westus',sku:'h100-b',billing:'on-demand',memory_gb:80,instance_usd_hour:12,usd_per_gpu_hour:6,url:'https://example.com/azure'},
  {provider:'Lambda',gpu:'A100 80GB',region:'us',sku:'a100',billing:'on-demand',memory_gb:80,instance_usd_hour:2,usd_per_gpu_hour:2,url:'https://example.com/lambda'}
]};
const storage={schema_version:2,dataset:'storage_hardware_prices',status:'ok',snapshot_date:'2026-10-05',methodology:'只展示价格，不展示新闻。',rows:[
  {id:'ddr5',category:'DRAM',item:'DDR5 16Gb chip',price:8.2,currency:'USD',unit:'per chip',quote_type:'spot_session_average',url:'https://example.com',history:[{date:'2026-10-04',price:8,value:8,unit:'USD per chip'},{date:'2026-10-05',price:8.2,value:8.2,unit:'USD per chip'}]},
  {id:'ddr4',category:'DRAM',item:'DDR4 16Gb chip',price:6.2,currency:'USD',unit:'per chip',quote_type:'spot_session_average',url:'https://example.com',history:[{date:'2026-10-04',price:6,value:6,unit:'USD per chip'},{date:'2026-10-05',price:6.2,value:6.2,unit:'USD per chip'}]},
  {id:'hbm',category:'HBM rental proxy',item:'H100 Azure',price:.1,currency:'USD',unit:'per HBM-GB·hour',quote_type:'compute_inclusive_rental_proxy',history:[{date:'2026-10-05',price:.1}]},
  {id:'ssd',category:'SSD',item:'2TB NVMe',price:180,currency:'USD',unit:'per drive',usd_per_tb:90,quote_type:'street_average',url:'https://example.com/ssd',history:[{date:'2026-10-05',price:180}]}
]};
const huggingFace={schema_version:2,dataset:'hugging_face_trends',status:'ok',snapshot_date:'2026-10-05',rows:[
  {rank:1,id:'org/text-model',task_type:'LLM / Text Generation',status:'exact',downloads_this_period:12345678,download_acceleration:1234567,use_case_zh:'文本生成',download_note:'本期增加了下载量',model_description:'A text model for multilingual question answering.',model_description_status:'verified',model_url:'https://huggingface.co/org/text-model'},
  {rank:2,id:'org/audio-model',task_type:'Audio / Speech',status:'exact',downloads_this_period:800,download_acceleration:80,use_case_zh:'语音识别',model_url:'https://huggingface.co/org/audio-model'},
  {rank:3,id:'org/image-model',task_type:'Image Generation',status:'watch',downloads_this_period:500,download_acceleration:null,use_case_zh:'图像生成',model_url:'https://huggingface.co/org/image-model'}
]};
const github={schema_version:2,dataset:'github_ai_projects',status:'ok',rows:[
  {full_name:'org/agent',domain:'Agent',category:'legacy-category',source_type:'trending',stars:12345678,stars_net_change:1234567,use_case_zh:'主要用于Agent；简介：协调多个 AI 代理的工具包。',use_case_translation_status:'machine',description_raw:'Official repository for a toolkit that coordinates AI agents.',url:'https://github.com/org/agent'},
  {full_name:'org/vision',domain:'Vision',category:'legacy-category',source_type:'topic',stars:50,stars_net_change:5,use_case_zh:'视觉',url:'https://github.com/org/vision'}
]};
const trending={schema_version:2,dataset:'github_trending_all',status:'ok',captured_at_utc:'2026-10-05T07:48:00Z',methodology:'GitHub 原榜单',rows:['daily','weekly','monthly'].flatMap(period=>[100,80,60,40,20].map((new_stars,index)=>({period,rank:index+1,full_name:`owner/${period}-${index+1}`,url:`https://github.com/owner/${period}-${index+1}`,stars:1000+index,new_stars,description_raw:index===4?'':`Original ${period} description ${index+1}`})))};
const xWatch={schema_version:2,dataset:'x_industry_watch',status:'ok',snapshot_date:'2026-10-10',days:7,accounts_count:50,priority_accounts_count:15,returned_accounts_count:2,checked_accounts:['thsottiaux','OpenAI'],failed_accounts:[],finished_at:'2026-10-10T12:30:00+08:00',methodology:'浏览器只读抽样。',rows:[
  {url:'https://x.com/thsottiaux/status/123',handle:'thsottiaux',account_name:'Tibo',category:'研究员、工程师与开发者',focus:'OpenAI；Codex、ChatGPT 产品迭代',priority:true,text:'Codex workflow update',published_at:'2026-10-10T10:00:00+08:00',likes:12,views:340,oembed_status:'ok'},
  {url:'javascript:alert(1)',handle:'OpenAI',account_name:'OpenAI',category:'模型厂商与官方账号',focus:'GPT、ChatGPT、前沿研究',priority:true,text:'<img src=x onerror=alert(1)>',published_at:'2026-10-10T09:00:00+08:00',likes:null,views:null,oembed_status:'unavailable'}
]};
const aiFinancials={schema_version:2,dataset:'ai_company_financials',status:'ok',methodology:'全公司资本开支不等于 AI 专项。',rows:[
  {ticker:'NVDA',company:'NVIDIA',company_url:'https://www.sec.gov/edgar/browse/?CIK=1045810',metrics:{capex:{value_usd:2000000000,period_start:'2026-01-01',period_end:'2026-06-30',filing_date:'2026-08-01',form:'10-Q',filing_url:'https://www.sec.gov/Archives/edgar/data/1045810/example-index.html'},revenue:null,operating_cash_flow:null}}
]};
const aiFrontier={schema_version:2,dataset:'ai_research_frontier',status:'partial',methodology:'未验证结果不能宣称已复核。',rows:[
  {kind:'benchmark',dimension:'代码智能体',benchmark:'SWE-bench Verified',benchmark_url:'https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified',rank:1,model_id:'org/model',score:83.2,verified:false,url:'https://huggingface.co/org/model',source_url:'https://huggingface.co/org/model',source_type:'模型卡'},
  {kind:'paper',dimension:'研究论文',paper_id:'2601.12345',title:'AI frontier paper',summary_raw:'Original English abstract',published_at_utc:'2026-10-10T00:00:00Z',submitted_at_utc:'2026-10-11T00:00:00Z',url:'https://huggingface.co/papers/2601.12345',arxiv_url:'https://arxiv.org/abs/2601.12345'}
]};

test.beforeEach(async({page})=>{
  await page.route('**/data/manifest.json*',route=>route.fulfill({json:manifest}));
  await page.route('**/data/token/latest.json*',route=>route.fulfill({json:token}));
  await page.route('**/data/models/latest.json*',route=>route.fulfill({json:models}));
  await page.route('**/data/gpu/latest.json*',route=>route.fulfill({json:gpu}));
  await page.route('**/data/storage/latest.json*',route=>route.fulfill({json:storage}));
  await page.route('**/data/hugging-face/latest.json*',route=>route.fulfill({json:huggingFace}));
  await page.route('**/data/github/latest.json*',route=>route.fulfill({json:github}));
  await page.route('**/data/github-trending/latest.json*',route=>route.fulfill({json:trending}));
  await page.route('**/x-watch/latest.json*',route=>route.fulfill({json:xWatch}));
  await page.route('**/data/ai-financials/latest.json*',route=>route.fulfill({json:aiFinancials}));
  await page.route('**/data/ai-frontier/latest.json*',route=>route.fulfill({json:aiFrontier}));
});

test('ten entries and overview load without eager module requests',async({page})=>{
  const requests=[];page.on('request',request=>requests.push(request.url()));
  await page.goto('/');
  await expect(page.locator('[data-module]')).toHaveCount(10);
  await expect(page.locator('[data-module="github"]')).toContainText('GitHub');
  await expect(page.getByRole('button',{name:/趋势榜/})).toHaveCount(0);
  await expect(page.getByRole('heading',{name:'AI 行业总览'})).toBeVisible();
  expect(requests.some(url=>url.includes('/data/storage/latest.json'))).toBeFalsy();
});

test('daily-news entry order and return navigation stay available',async({page})=>{
  await page.goto('/');
  const dailyEntry=page.locator('.daily-entry').first();
  await expect(dailyEntry.getByRole('link',{name:/AI 新闻日报/})).toBeVisible();
  await expect(dailyEntry.getByText('每日自动更新',{exact:true})).toBeVisible();
  expect(await dailyEntry.locator(':scope > *').evaluateAll(nodes=>nodes.map(node=>node.tagName))).toEqual(['A','SPAN']);
  await expect(page.locator('.schedule')).toHaveCSS('border-top-width','0px');
  await expect(page.getByRole('button',{name:/产业新闻/})).toHaveCount(0);
  await expect(page.getByRole('link',{name:/AI 新闻预览/})).toHaveCount(0);
  await dailyEntry.getByRole('link',{name:/AI 新闻日报/}).click();
  await expect(page).toHaveURL(/\/ai-news-daily\/index\.html$/);
  await expect(page.getByRole('link',{name:'← 返回总览'})).toHaveAttribute('href','../index.html');
  await expect(page.locator('.notice')).toHaveCount(0);
  await page.getByRole('link',{name:/查看完整报告/}).first().click();
  await expect(page).toHaveURL(/\/ai-news-daily\/reports\//);
  await expect(page.getByRole('link',{name:'← 返回 AI 新闻日报'})).toHaveAttribute('href','../index.html');
});

test('Token explains total changes with stacks and discontinuous model trends',async({page})=>{
  await page.goto('/#token');
  await expect(page.getByText('Token 总量构成与变化归因')).toBeVisible();
  await expect(page.locator('.token-stack-svg')).toBeVisible();
  await expect(page.locator('[data-token-week]')).not.toHaveCount(0);
  await expect(page.locator('.token-stack-svg')).toHaveCSS('max-height','none');
  await page.locator('[data-trend-tip][data-tip-name="openai/alpha"]').first().hover();
  await expect(page.locator('.chart-tooltip')).toContainText('openai/alpha');
  await expect(page.locator('.chart-tooltip')).toContainText('600');
  await expect(page.locator('.chart-tooltip')).not.toContainText('2026-09');
  await expect(page.getByText('入榜模型连续趋势')).toBeVisible();
  await expect(page.locator('.trend-line')).not.toHaveCount(0);
  const pickerPanel=page.locator('#trend-picker-token');
  await expect(pickerPanel).toBeHidden();
  await page.locator('[data-trend-vendor="token"]').selectOption('OpenAI');
  await expect(pickerPanel).toBeHidden();
  await page.getByRole('button',{name:/展开/}).click();
  await expect(pickerPanel).toBeVisible();
  await expect(pickerPanel.locator('fieldset:not([hidden])')).toHaveCount(1);
  await expect(page.locator('.trend-legend span')).toHaveCount(2);
  for(const id of ['openai/alpha','google/gamma']){
    await expect(page.locator(`[data-trend-series="${id}"]`)).toHaveCount(1);
    await expect(page.locator(`[data-trend-series-point="${id}"]`)).not.toHaveCount(0);
  }
  await page.getByRole('button',{name:'100% 堆积'}).click();
  await expect(page.getByText('模型份额构成')).toBeVisible();
  await expect(page.locator('.token-stack-svg')).toHaveAttribute('aria-label','Token 份额堆积柱状图');
  await expect(page.getByText('Others',{exact:true})).toHaveCount(0);
});

test('GPU and storage expose selectable, comparable trend series',async({page})=>{
  await page.goto('/#gpu');
  await expect(page.getByText('GPU 价格趋势')).toBeVisible();
  await expect(page.getByText(/每日中位价；色带为 P25/)).toBeVisible();
  await expect(page.locator('.trend-band')).not.toHaveCount(0);
  await expect(page.locator('.gpu-trend-card')).toHaveCount(2);
  await expect(page.locator('.gpu-trend-card svg').first()).toHaveCSS('min-width','0px');
  await expect(page.locator('.gpu-trend-card').first()).toContainText('2 个采集日');
  await page.goto('/#storage');
  await expect(page.getByText('DRAM 单品趋势')).toBeVisible();
  await expect(page.locator('[data-trend-picker="storage"]')).toHaveCount(2);
  await expect(page.getByText(/仅允许同一可比单位/)).toBeVisible();
});

test('SEC financials and research frontier retain their different evidence labels',async({page})=>{
  await page.goto('/#ai-financials');
  await expect(page.getByRole('button',{name:/上市公司Capex/})).toBeVisible();
  await expect(page.getByRole('heading',{name:'上市公司 AI 财务与资本开支'})).toBeVisible();
  await expect(page.locator('#content')).toContainText('$2B');
  await expect(page.locator('#chart')).toContainText('不等于 AI 专项');
  await page.getByRole('button',{name:/AI 研究前沿与模型能力/}).click();
  await expect(page.locator('#status')).toContainText('partial');
  await expect(page.locator('#content')).toContainText('未独立验证');
  await expect(page.locator('#content')).toContainText('AI frontier paper');
  await expect(page.locator('#content')).toContainText('2026-10-10');
  await page.locator('#filter').selectOption('研究论文');
  await expect(page.locator('#content')).not.toContainText('org/model');
});

test('financial period, source details and sector filters use the unified metrics contract',async({page})=>{
  const missing=reason=>({value_usd:null,value_pct:null,status:'missing',missing_reason:reason,period_start:null,period_end:null,filing_url:null});
  const fact=value=>({value_usd:value,value_pct:null,status:'ok',missing_reason:null,period_start:'2025-01-01',period_end:'2025-12-31',filing_date:'2026-02-01',form:'10-K',filing_url:'https://www.sec.gov/Archives/edgar/data/1/filing-index.html',concept:'us-gaap:Example'});
  const ratio=value=>({value_usd:null,value_pct:value,status:'ok',missing_reason:null,period_start:'2025-01-01',period_end:'2025-12-31',formula:'capex / revenue * 100',inputs:{capex:fact(2e9),revenue:fact(10e9)}});
  const metrics={capex:fact(2e9),revenue:fact(10e9),operating_cash_flow:fact(4e9),operating_income:fact(3e9),revenue_yoy:ratio(12),capex_yoy:ratio(20),capex_to_revenue:ratio(20),capex_to_ocf:ratio(50),free_cash_flow:{...fact(2e9),formula:'operating_cash_flow - capex'},free_cash_flow_margin:ratio(20),operating_margin:ratio(30)};
  const unavailable=Object.fromEntries(Object.keys(metrics).map(key=>[key,missing('当前期间未取得可靠事实')]));
  const periods={FY:{label:'FY',period_start:'2025-01-01',period_end:'2025-12-31',status:'ok',missing_reason:null,metrics},TTM:{label:'TTM',period_start:null,period_end:null,status:'missing',missing_reason:'TTM 暂不推算',metrics:unavailable},Quarter:{label:'Quarter',status:'missing',metrics:unavailable},YTD:{label:'YTD',status:'missing',metrics:unavailable}};
  const rows=[
    {company:'NVIDIA',ticker:'NVDA',sector_group:'Semiconductor Supply Chain',status:'ok',periods,metrics},
    {company:'Oracle',ticker:'ORCL',sector_group:'AI Infrastructure Buyers',status:'partial',periods:{...periods,FY:{...periods.FY,status:'partial',metrics:{...metrics,capex:missing('标准标签未匹配'),capex_yoy:missing('基础指标缺失'),capex_to_revenue:missing('基础指标缺失'),free_cash_flow:missing('基础指标缺失')}}}}
  ];
  await page.route('**/data/ai-financials/latest.json*',route=>route.fulfill({json:{schema_version:2,dataset:'ai_company_financials',status:'partial',rows}}));
  await page.goto('/#ai-financials');
  await expect(page.getByRole('combobox',{name:'财务期间'})).toHaveValue('FY');
  await expect(page.locator('.fin-company-row')).toHaveCount(2);
  await page.getByRole('button',{name:/NVIDIA · NVDA/}).click();
  const mobile=page.viewportSize().width<=700;
  const detail=page.locator(mobile?'#drawer-content':'.fin-detail-row:not([hidden])');
  await expect(detail.locator('.fin-metric')).toHaveCount(11);
  await expect(detail).toContainText('Reported');
  await expect(detail).toContainText('Derived');
  await expect(detail).toContainText('capex / revenue * 100');
  await expect(detail.locator('a[href*="sec.gov"]')).not.toHaveCount(0);
  if(mobile)await page.getByRole('button',{name:'关闭'}).click();
  await page.getByRole('combobox',{name:'财务期间'}).selectOption('TTM');
  await expect(page.locator('.fin-company-row').first()).toContainText('N/A');
  await page.getByRole('combobox',{name:'产业链分组'}).selectOption('AI Infrastructure Buyers');
  await expect(page.locator('.fin-company-row')).toHaveCount(1);
  await expect(page.locator('.fin-company-row')).toContainText('Oracle');
  await page.getByRole('combobox',{name:'财务期间'}).selectOption('FY');
  await page.getByRole('button',{name:/Oracle · ORCL/}).click();
  await expect(page.locator(mobile?'#drawer-content':'.fin-detail-row:not([hidden])')).toContainText('标准标签未匹配');
});

test('X watch is integrated in the sidebar with safe filtering and links',async({page})=>{
  await page.goto('/');
  await page.getByRole('button',{name:/X 账号动态/}).click();
  await expect(page.getByRole('heading',{name:'X 账号动态'})).toBeVisible();
  await expect(page.locator('.x-post')).toHaveCount(2);
  await expect(page.getByRole('link',{name:/查看 X 原文/})).toHaveCount(1);
  await page.getByLabel('优先关注筛选').selectOption('priority');
  await page.getByRole('searchbox').fill('Tibo');
  await expect(page.locator('.x-post')).toHaveCount(1);
  await expect(page.getByText('Codex workflow update')).toBeVisible();
  expect(await page.locator('img').count()).toBe(0);
});

test('storage shows prices and category trends without news cards',async({page})=>{
  await page.goto('/#storage');
  await expect(page.getByRole('heading',{name:'存储硬件价格'})).toBeVisible();
  await expect(page.getByText('类别价格基准')).toBeVisible();
  await expect(page.getByRole('cell',{name:'USD/TB'})).toBeVisible();
  await expect(page.getByRole('cell',{name:'$90'})).toHaveCount(4);
  await expect(page.getByRole('cell',{name:'$8.2'})).toBeVisible();
  await expect(page.locator('#chart .trend-svg')).toBeVisible();
  await expect(page.locator('.news')).toHaveCount(0);
  await page.locator('#storage-category').selectOption('HBM rental proxy');
  await expect(page.locator('.chart-title')).toContainText('HBM rental proxy');
});

test('Hugging Face task filter uses task_type and returns matching models',async({page})=>{
  await page.goto('/#hugging-face');
  await expect(page.locator('#content tbody tr')).toHaveCount(3);
  await expect(page.locator('#content tbody tr').first().locator('td').nth(5)).toHaveText('A text model for multilingual question answering.');
  await expect(page.locator('#content')).not.toContainText('本期增加了下载量');
  await expect(page.locator('#content tbody tr').nth(1).locator('td').nth(5)).toHaveText('暂无可核实简介');
  for(const column of [3,4])expect(await page.locator('.hf-table tbody tr').first().locator('td').nth(column).evaluate(el=>getComputedStyle(el).whiteSpace)).toBe('nowrap');
  await page.locator('#filter').selectOption('Audio / Speech');
  await expect(page.locator('#content tbody tr')).toHaveCount(1);
  await expect(page.getByRole('link',{name:/audio-model/})).toBeVisible();
  await expect(page.getByRole('link',{name:/text-model/})).toHaveCount(0);
});

test('GitHub filters use the domain field displayed by their dropdown',async({page})=>{
  await page.goto('/#github');
  await page.getByRole('button',{name:'AI 项目',exact:true}).click();
  await expect(page.locator('.project-table tbody tr').first().locator('td').last()).toHaveText('协调多个 AI 代理的工具包。');
  expect(await page.locator('.project-table tbody tr').first().locator('td').nth(3).evaluate(el=>getComputedStyle(el).whiteSpace)).toBe('nowrap');
  expect(await page.locator('.project-table tbody tr').first().locator('td').nth(4).evaluate(el=>getComputedStyle(el).whiteSpace)).toBe('nowrap');
  await page.locator('#filter').selectOption('Vision');
  await expect(page.getByRole('link',{name:/org\/vision/})).toBeVisible();
  await expect(page.getByRole('link',{name:/org\/agent/})).toHaveCount(0);
});

test('Trending period selector keeps GitHub order, original text and one capture time',async({page})=>{
  await page.goto('/#github');
  await expect(page.getByRole('heading',{name:'GitHub'})).toBeVisible();
  const filterChildren=page.locator('#filters').locator(':scope > *');
  await expect(filterChildren.first()).toHaveClass(/github-view-nav/);
  await expect(filterChildren.nth(1).getByRole('searchbox')).toBeVisible();
  await expect(page.locator('#date')).toContainText('采集于');
  await expect(page.locator('#content tbody tr')).toHaveCount(5);
  await expect(page.getByRole('link',{name:/owner\/daily-1/})).toBeVisible();
  await expect(page.locator('#content tbody tr').first().locator('.growth-hot')).toHaveText('+100');
  await expect(page.locator('#content .growth-hot')).toHaveCount(1);
  await expect(page.locator('#content')).toContainText('原站未提供项目简介');
  await page.locator('#trending-period').selectOption('weekly');
  await expect(page.getByRole('columnheader',{name:'本周新增 Stars'})).toBeVisible();
  await expect(page.getByRole('link',{name:/owner\/weekly-1/})).toBeVisible();
  await expect(page.getByRole('link',{name:/owner\/daily-1/})).toHaveCount(0);
  await page.locator('#trending-period').selectOption('monthly');
  await expect(page.getByRole('columnheader',{name:'本月新增 Stars'})).toBeVisible();
  await expect(page.getByRole('link',{name:/owner\/monthly-1/})).toBeVisible();
});

test('AI stars and Hugging Face acceleration mark only top positive quintile',async({page})=>{
  await page.goto('/#github');
  await page.getByRole('button',{name:'AI 项目',exact:true}).click();
  await expect(page.locator('#content .growth-hot')).toHaveCount(1);
  await expect(page.locator('#content .growth-hot')).toHaveText('+'+Math.max(...github.rows.map(row=>row.stars_net_change||0)).toLocaleString('zh-CN'));
  await page.goto('/#hugging-face');
  await expect(page.locator('#content .growth-hot')).toHaveCount(1);
  await expect(page.locator('#content .growth-hot')).toHaveText('+'+Math.max(...huggingFace.rows.map(row=>row.download_acceleration||0)).toLocaleString('zh-CN'));
  await expect(page.locator('#content tbody td:nth-child(4) .growth-hot')).toHaveCount(0);
});

test('price pages default to benchmarks and retain filtered detail views',async({page})=>{
  await page.goto('/#models');
  await expect(page.getByText('价格分位基准')).toBeVisible();
  const searchBox=await page.getByRole('searchbox').boundingBox();
  const filterBox=await page.locator('#filter').boundingBox();
  expect(searchBox.height).toBe(filterBox.height);
  await expect(page.locator('#chart circle').first()).toHaveAttribute('r','3.5');
  const scatterBounds=await page.locator('.scatter-svg circle').evaluateAll(points=>({x:points.map(point=>Number(point.getAttribute('cx'))),y:points.map(point=>Number(point.getAttribute('cy')))}));
  expect(Math.min(...scatterBounds.x)).toBeLessThanOrEqual(43);
  expect(Math.max(...scatterBounds.x)).toBeGreaterThanOrEqual(687);
  expect(Math.min(...scatterBounds.y)).toBeLessThanOrEqual(13);
  expect(Math.max(...scatterBounds.y)).toBeGreaterThanOrEqual(261);
  await page.locator('#chart circle').first().hover();
  await expect(page.locator('#model-point-label')).toContainText('输入 $');
  await page.locator('#filter').selectOption('OpenAI');
  await page.getByRole('button',{name:'全部明细'}).click();
  await expect(page.getByRole('link',{name:/OpenAI Mini/})).toBeVisible();
  await expect(page.getByRole('link',{name:/Qwen Fast/})).toHaveCount(0);

  await page.getByRole('button',{name:/GPU 云报价/}).click();
  await expect(page.getByText('GPU / 计费基准')).toBeVisible();
  await page.locator('#filter').selectOption('Lambda');
  await expect(page.locator('#content')).toContainText('A100 80GB');
  await expect(page.locator('#content')).not.toContainText('H100 80GB');
});
