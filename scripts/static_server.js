const http=require('http'),fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'..','site');
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8'};
let idleTimer;
const server=http.createServer((request,response)=>{
  clearTimeout(idleTimer);
  idleTimer=setTimeout(()=>server.close(()=>process.exit(0)),15000);
  const pathname=decodeURIComponent(new URL(request.url,'http://localhost').pathname);
  const target=path.resolve(root,'.'+(pathname==='/'?'/index.html':pathname));
  if(!target.startsWith(root)){response.writeHead(403);return response.end('forbidden');}
  fs.readFile(target,(error,data)=>{if(error){response.writeHead(404);return response.end('not found');}response.writeHead(200,{'Content-Type':types[path.extname(target)]||'application/octet-stream','Cache-Control':'no-store'});response.end(data);});
}).listen(4173,'127.0.0.1',()=>{
  console.log('dashboard test server: 4173');
  idleTimer=setTimeout(()=>server.close(()=>process.exit(0)),15000);
});
