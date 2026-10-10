const {test,expect}=require('@playwright/test');
const manifest={schema_version:2,snapshot_date:'2026-10-05',history_days:90,modules:{storage:{status:'ok',rows:2,snapshot_date:'2026-10-05'}},terms:{HBM:'高带宽内存'}};
const storage={schema_version:2,dataset:'storage_hardware_prices',status:'ok',snapshot_date:'2026-10-05',methodology:'只展示价格，不展示新闻。',rows:[
  {id:'ddr5',category:'DRAM',item:'DDR5 16Gb chip',price:8.2,currency:'USD',unit:'per chip',quote_type:'spot_session_average',url:'https://example.com',history:[{date:'2026-10-04',price:8},{date:'2026-10-05',price:8.2}]},
  {id:'hbm',category:'HBM rental proxy',item:'H100 Azure',price:.1,currency:'USD',unit:'per HBM-GB·hour',quote_type:'compute_inclusive_rental_proxy',history:[{date:'2026-10-05',price:.1}]}
]};
const xWatch={schema_version:2,dataset:'x_industry_watch',status:'ok',snapshot_date:'2026-10-10',days:7,accounts_count:50,priority_accounts_count:15,returned_accounts_count:2,checked_accounts:['thsottiaux','OpenAI'],failed_accounts:[],finished_at:'2026-10-10T12:30:00+08:00',methodology:'浏览器只读抽样。',rows:[
  {url:'https://x.com/thsottiaux/status/123',handle:'thsottiaux',account_name:'Tibo',category:'研究员、工程师与开发者',focus:'OpenAI；Codex、ChatGPT 产品迭代',priority:true,text:'Codex workflow update',published_at:'2026-10-10T10:00:00+08:00',likes:12,views:340,oembed_status:'ok'},
  {url:'javascript:alert(1)',handle:'OpenAI',account_name:'OpenAI',category:'模型厂商与官方账号',focus:'GPT、ChatGPT、前沿研究',priority:true,text:'<img src=x onerror=alert(1)>',published_at:'2026-10-10T09:00:00+08:00',likes:null,views:null,oembed_status:'unavailable'}
]};

test.beforeEach(async({page})=>{
  await page.route('**/data/manifest.json*',route=>route.fulfill({json:manifest}));
  await page.route('**/data/storage/latest.json*',route=>route.fulfill({json:storage}));
  await page.route('**/data/x-watch/latest.json*',route=>route.fulfill({json:xWatch}));
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
  await page.getByLabel('账号范围').selectOption('priority');
  await page.getByRole('searchbox').fill('Tibo');
  await expect(page.locator('.x-post')).toHaveCount(1);
  await expect(page.getByText('Codex workflow update')).toBeVisible();
  expect(await page.locator('img').count()).toBe(0);
});

test('storage shows prices and trends without news cards',async({page})=>{
  await page.goto('/#storage');
  await expect(page.getByRole('heading',{name:'存储硬件价格'})).toBeVisible();
  await expect(page.getByRole('link',{name:/DDR5 16Gb chip/})).toBeVisible();
  await expect(page.getByRole('cell',{name:'H100 Azure'})).toBeVisible();
  await expect(page.locator('.chart-area svg')).toBeVisible();
  await expect(page.locator('.news')).toHaveCount(0);
});
