const {test,expect}=require('@playwright/test');
const manifest={schema_version:2,snapshot_date:'2026-10-05',history_days:90,modules:{news:{status:'ok',rows:2},models:{status:'ok',rows:4},gpu:{status:'ok',rows:3},storage:{status:'ok',rows:3},'hugging-face':{status:'ok',rows:3},github:{status:'ok',rows:2}},terms:{HBM:'高带宽内存'}};
const news={schema_version:2,dataset:'industry_news',status:'ok',rows:[
  {title:'Upstream chip event',summary:'Chip supply update',source:'Example',region:'全球',chain_category:'上游：算力、芯片与存储',url:'https://example.com/upstream',published_at_utc:'2026-10-05T00:00:00Z'},
  {title:'Application event',summary:'Application update',source:'Example',region:'全球',chain_category:'下游：行业应用',url:'https://example.com/application',published_at_utc:'2026-10-05T00:00:00Z'}
]};
const models={schema_version:2,dataset:'model_api_prices',status:'ok',rows:[
  {id:'openai/mini',name:'OpenAI Mini',vendor:'OpenAI',input_usd_per_million:.2,output_usd_per_million:.8,context_length:128000,input_modalities:['text'],url:'https://example.com/openai-mini'},
  {id:'openai/pro',name:'OpenAI Pro',vendor:'OpenAI',input_usd_per_million:2,output_usd_per_million:8,context_length:200000,input_modalities:['text'],url:'https://example.com/openai-pro'},
  {id:'qwen/fast',name:'Qwen Fast',vendor:'Qwen',input_usd_per_million:.1,output_usd_per_million:.4,context_length:32000,input_modalities:['text'],url:'https://example.com/qwen-fast'},
  {id:'qwen/long',name:'Qwen Long',vendor:'Qwen',input_usd_per_million:.4,output_usd_per_million:1.6,context_length:1000000,input_modalities:['text'],url:'https://example.com/qwen-long'}
]};
const gpu={schema_version:2,dataset:'gpu_cloud_prices',status:'ok',rows:[
  {provider:'Azure',gpu:'H100 80GB',region:'eastus',sku:'h100-a',billing:'on-demand',memory_gb:80,instance_usd_hour:8,usd_per_gpu_hour:4,url:'https://example.com/azure'},
  {provider:'Azure',gpu:'H100 80GB',region:'westus',sku:'h100-b',billing:'on-demand',memory_gb:80,instance_usd_hour:12,usd_per_gpu_hour:6,url:'https://example.com/azure'},
  {provider:'Lambda',gpu:'A100 80GB',region:'us',sku:'a100',billing:'on-demand',memory_gb:80,instance_usd_hour:2,usd_per_gpu_hour:2,url:'https://example.com/lambda'}
]};
const storage={schema_version:2,dataset:'storage_hardware_prices',status:'ok',snapshot_date:'2026-10-05',methodology:'只展示价格，不展示新闻。',rows:[
  {id:'ddr5',category:'DRAM',item:'DDR5 16Gb chip',price:8.2,currency:'USD',unit:'per chip',quote_type:'spot_session_average',url:'https://example.com',history:[{date:'2026-10-04',price:8},{date:'2026-10-05',price:8.2}]},
  {id:'hbm',category:'HBM rental proxy',item:'H100 Azure',price:.1,currency:'USD',unit:'per HBM-GB·hour',quote_type:'compute_inclusive_rental_proxy',history:[{date:'2026-10-05',price:.1}]},
  {id:'ssd',category:'SSD',item:'2TB NVMe',price:180,currency:'USD',unit:'per drive',usd_per_tb:90,quote_type:'street_average',url:'https://example.com/ssd',history:[{date:'2026-10-05',price:180}]}
]};
const huggingFace={schema_version:2,dataset:'hugging_face_trends',status:'ok',snapshot_date:'2026-10-05',rows:[
  {rank:1,id:'org/text-model',task_type:'LLM / Text Generation',status:'exact',downloads_this_period:1000,download_acceleration:100,use_case_zh:'文本生成',model_url:'https://huggingface.co/org/text-model'},
  {rank:2,id:'org/audio-model',task_type:'Audio / Speech',status:'exact',downloads_this_period:800,download_acceleration:80,use_case_zh:'语音识别',model_url:'https://huggingface.co/org/audio-model'},
  {rank:3,id:'org/image-model',task_type:'Image Generation',status:'watch',downloads_this_period:500,download_acceleration:null,use_case_zh:'图像生成',model_url:'https://huggingface.co/org/image-model'}
]};
const github={schema_version:2,dataset:'github_ai_projects',status:'ok',rows:[
  {full_name:'org/agent',domain:'Agent',category:'legacy-category',source_type:'trending',stars:100,stars_net_change:10,use_case_zh:'智能体',url:'https://github.com/org/agent'},
  {full_name:'org/vision',domain:'Vision',category:'legacy-category',source_type:'topic',stars:50,stars_net_change:5,use_case_zh:'视觉',url:'https://github.com/org/vision'}
]};
const xWatch={schema_version:2,dataset:'x_industry_watch',status:'ok',snapshot_date:'2026-10-10',days:7,accounts_count:50,priority_accounts_count:15,returned_accounts_count:2,checked_accounts:['thsottiaux','OpenAI'],failed_accounts:[],finished_at:'2026-10-10T12:30:00+08:00',methodology:'浏览器只读抽样。',rows:[
  {url:'https://x.com/thsottiaux/status/123',handle:'thsottiaux',account_name:'Tibo',category:'研究员、工程师与开发者',focus:'OpenAI；Codex、ChatGPT 产品迭代',priority:true,text:'Codex workflow update',published_at:'2026-10-10T10:00:00+08:00',likes:12,views:340,oembed_status:'ok'},
  {url:'javascript:alert(1)',handle:'OpenAI',account_name:'OpenAI',category:'模型厂商与官方账号',focus:'GPT、ChatGPT、前沿研究',priority:true,text:'<img src=x onerror=alert(1)>',published_at:'2026-10-10T09:00:00+08:00',likes:null,views:null,oembed_status:'unavailable'}
]};

test.beforeEach(async({page})=>{
  await page.route('**/data/manifest.json*',route=>route.fulfill({json:manifest}));
  await page.route('**/data/news/latest.json*',route=>route.fulfill({json:news}));
  await page.route('**/data/models/latest.json*',route=>route.fulfill({json:models}));
  await page.route('**/data/gpu/latest.json*',route=>route.fulfill({json:gpu}));
  await page.route('**/data/storage/latest.json*',route=>route.fulfill({json:storage}));
  await page.route('**/data/hugging-face/latest.json*',route=>route.fulfill({json:huggingFace}));
  await page.route('**/data/github/latest.json*',route=>route.fulfill({json:github}));
  await page.route('**/x-watch/latest.json*',route=>route.fulfill({json:xWatch}));
});

test('nine entries and overview load without eager module requests',async({page})=>{
  const requests=[];page.on('request',request=>requests.push(request.url()));
  await page.goto('/');
  await expect(page.locator('[data-module]')).toHaveCount(9);
  await expect(page.getByRole('heading',{name:'AI 行业总览'})).toBeVisible();
  expect(requests.some(url=>url.includes('/data/storage/latest.json'))).toBeFalsy();
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

test('storage shows prices and trends without news cards',async({page})=>{
  await page.goto('/#storage');
  await expect(page.getByRole('heading',{name:'存储硬件价格'})).toBeVisible();
  await expect(page.getByText('类别价格基准')).toBeVisible();
  await expect(page.getByRole('cell',{name:'USD/TB'})).toBeVisible();
  await expect(page.getByRole('cell',{name:'$90'})).toHaveCount(4);
  await expect(page.getByRole('cell',{name:'$8.2'})).toHaveCount(4);
  await expect(page.locator('.chart-area svg')).toBeVisible();
  await expect(page.locator('.news')).toHaveCount(0);
  await page.locator('#filter').selectOption('HBM rental proxy');
  await expect(page.locator('.chart-title')).toContainText('H100 Azure');
});

test('Hugging Face task filter uses task_type and returns matching models',async({page})=>{
  await page.goto('/#hugging-face');
  await expect(page.locator('#content tbody tr')).toHaveCount(3);
  await page.locator('#filter').selectOption('Audio / Speech');
  await expect(page.locator('#content tbody tr')).toHaveCount(1);
  await expect(page.getByRole('link',{name:/audio-model/})).toBeVisible();
  await expect(page.getByRole('link',{name:/text-model/})).toHaveCount(0);
});

test('news and GitHub filters use the category field displayed by their dropdowns',async({page})=>{
  await page.goto('/#news');
  await page.locator('#filter').selectOption('下游：行业应用');
  await expect(page.locator('.news')).toHaveCount(1);
  await expect(page.getByRole('link',{name:/Application event/})).toBeVisible();
  await expect(page.getByRole('link',{name:/Upstream chip event/})).toHaveCount(0);

  await page.getByRole('button',{name:/GitHub AI 项目/}).click();
  await page.locator('#filter').selectOption('Vision');
  await expect(page.getByRole('link',{name:/org\/vision/})).toBeVisible();
  await expect(page.getByRole('link',{name:/org\/agent/})).toHaveCount(0);
});

test('price pages default to benchmarks and retain filtered detail views',async({page})=>{
  await page.goto('/#models');
  await expect(page.getByText('价格分位基准')).toBeVisible();
  const searchBox=await page.getByRole('searchbox').boundingBox();
  const filterBox=await page.locator('#filter').boundingBox();
  expect(searchBox.height).toBe(filterBox.height);
  await expect(page.locator('#chart circle').first()).toHaveAttribute('r','3.2');
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
