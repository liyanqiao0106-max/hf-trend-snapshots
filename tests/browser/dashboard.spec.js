const {test,expect}=require('@playwright/test');
const manifest={schema_version:2,snapshot_date:'2026-10-05',history_days:90,modules:{storage:{status:'ok',rows:2,snapshot_date:'2026-10-05'}},terms:{HBM:'高带宽内存'}};
const storage={schema_version:2,dataset:'storage_hardware_prices',status:'ok',snapshot_date:'2026-10-05',methodology:'只展示价格，不展示新闻。',rows:[
  {id:'ddr5',category:'DRAM',item:'DDR5 16Gb chip',price:8.2,currency:'USD',unit:'per chip',quote_type:'spot_session_average',url:'https://example.com',history:[{date:'2026-10-04',price:8},{date:'2026-10-05',price:8.2}]},
  {id:'hbm',category:'HBM rental proxy',item:'H100 Azure',price:.1,currency:'USD',unit:'per HBM-GB·hour',quote_type:'compute_inclusive_rental_proxy',history:[{date:'2026-10-05',price:.1}]}
]};

test.beforeEach(async({page})=>{
  await page.route('**/data/manifest.json*',route=>route.fulfill({json:manifest}));
  await page.route('**/data/storage/latest.json*',route=>route.fulfill({json:storage}));
});

test('eight entries and overview load without eager module requests',async({page})=>{
  const requests=[];page.on('request',request=>requests.push(request.url()));
  await page.goto('/');
  await expect(page.locator('[data-module]')).toHaveCount(8);
  await expect(page.getByRole('heading',{name:'AI 行业总览'})).toBeVisible();
  expect(requests.some(url=>url.includes('/data/storage/latest.json'))).toBeFalsy();
});

test('storage shows prices and trends without news cards',async({page})=>{
  await page.goto('/#storage');
  await expect(page.getByRole('heading',{name:'存储硬件价格'})).toBeVisible();
  await expect(page.getByRole('link',{name:/DDR5 16Gb chip/})).toBeVisible();
  await expect(page.getByRole('cell',{name:'H100 Azure'})).toBeVisible();
  await expect(page.locator('.chart-area svg')).toBeVisible();
  await expect(page.locator('.news')).toHaveCount(0);
});
