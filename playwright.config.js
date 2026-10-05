const {defineConfig}=require('@playwright/test');
const localExecutable=process.env.PLAYWRIGHT_EXECUTABLE_PATH;
module.exports=defineConfig({
  testDir:'tests/browser',
  timeout:30000,
  use:{baseURL:'http://127.0.0.1:4173',trace:'retain-on-failure',launchOptions:localExecutable?{executablePath:localExecutable}:{}},
  webServer:{command:'node scripts/static_server.js',url:'http://127.0.0.1:4173',reuseExistingServer:true,timeout:15000},
  projects:[
    {name:'desktop',use:{viewport:{width:1440,height:1000}}},
    {name:'mobile',use:{viewport:{width:390,height:844},isMobile:true}}
  ]
});
