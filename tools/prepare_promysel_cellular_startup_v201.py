#!/usr/bin/env python3
"""v2.01: make the Flutter Web startup independent from Google's CanvasKit CDN.

Runs on the final Flutter build after prepare_promysel_web_push.py.
Only local app assets are cached. NEVER cache Supabase API/auth/chat responses.
Tuqo runs static files and cannot act as the API proxy.
"""
from pathlib import Path
import html
import json
import re

root=Path('build/web')
bootstrap=root/'flutter_bootstrap.js'
index=root/'index.html'
worker=root/'promysel-push-sw.js'
assert all(p.is_file() for p in (bootstrap,index,worker))
assert (root/'canvaskit/canvaskit.wasm').is_file(), 'Local CanvasKit wasm is required'
assert (root/'canvaskit/canvaskit.js').is_file(), 'Local CanvasKit JS is required'
assert (root/'main.dart.js').is_file()
build_id=(root/'.last_build_id').read_text().strip()[:12] if (root/'.last_build_id').exists() else 'static-v201'
assert re.fullmatch(r'[0-9A-Za-z_-]{6,32}',build_id), 'Invalid build identifier'

# Official Flutter loader config: avoid the implicit www.gstatic.com origin.
# Keep the default callback and engine initialization unchanged.
s=bootstrap.read_text(encoding='utf-8')
old='_flutter.loader.load({});'
new='_flutter.loader.load({config:{canvasKitBaseUrl:"/canvaskit/",useLocalCanvasKit:true}});'
assert s.count(old)==1, 'Flutter loader changed; do not silently fall back to CDN'
bootstrap.write_text(s.replace(old,new,1),encoding='utf-8')

# A simple progress/repair screen makes a failed first mobile visit diagnosable
# rather than trapping the user at an undifferentiated blank screen.
s=index.read_text(encoding='utf-8')
assert s.count('<script src="flutter_bootstrap.js" async></script>')==1
assert '</head>' in s and '<body>' in s and '</body>' in s
s=s.replace('</head>',"""<meta name="theme-color" content="#0B4F91">
<link rel="preload" href="/main.dart.js" as="script">
<style>
#promysel-startup{box-sizing:border-box;position:fixed;inset:0;z-index:999999;
 display:flex;align-items:center;justify-content:center;background:#edf5fb;
 color:#173650;font:500 15px/1.5 system-ui,-apple-system,sans-serif;padding:26px}
#promysel-startup .startup-content{text-align:center;max-width:390px}
#promysel-startup .logo{font-weight:800;letter-spacing:.03em;font-size:29px}
#promysel-startup .spinner{margin:24px auto;border:3px solid #c3d8e9;
 border-top-color:#0b4f91;border-radius:100%;width:34px;height:34px;
 animation:promyselSpin .85s linear infinite}
@keyframes promyselSpin{to{transform:rotate(360deg)}}
#promysel-startup .muted{font-size:13px;color:#537086;margin-top:8px}
#promysel-startup .controls{display:none;margin-top:18px}
#promysel-startup button,#promysel-startup a{display:inline-block;box-sizing:border-box;
 margin:5px;padding:10px 16px;border-radius:10px;border:1px solid #0b4f91;
 background:#0b4f91;color:#fff;text-decoration:none;font:600 14px system-ui}
#promysel-startup a{background:#fff;color:#0b4f91}
</style>
</head>""",1)
banner="""<div id="promysel-startup" role="status" aria-live="polite">
  <div class="startup-content">
    <div class="logo">Промысел</div>
    <div class="spinner" aria-hidden="true"></div>
    <div id="promysel-status">Загружаем приложение…</div>
    <div class="muted">Первая загрузка через мобильный интернет может занять немного времени.</div>
    <div id="promysel-controls" class="controls">
      <button type="button" onclick="location.reload()">Повторить загрузку</button>
      <a href="/diagnostics.html">Проверить подключение</a>
    </div>
  </div>
</div>
<script>
(function(){
  const startup=document.getElementById('promysel-startup');
  const status=document.getElementById('promysel-status');
  const controls=document.getElementById('promysel-controls');
  let done=false;
  const ready=()=>{
    if(done)return;done=true;startup.remove();
    if(observer)observer.disconnect();
  };
  let observer;
  // Both document and window are used by Flutter engine versions.
  document.addEventListener('flutter-first-frame',ready,{once:true});
  window.addEventListener('flutter-first-frame',ready,{once:true});
  // A web engine can mount its view before dispatching first-frame.
  observer=new MutationObserver(()=>{
    if(document.querySelector('flutter-view,flt-glass-pane')){
      window.setTimeout(()=>{
        if(document.querySelector('flutter-view,flt-glass-pane'))ready();
      },700);
    }
  });
  observer.observe(document.documentElement,{childList:true,subtree:true});
  window.setTimeout(()=>{
    if(!done)status.textContent='Подключаем графический движок и загружаем данные…';
  },9000);
  window.setTimeout(()=>{
    if(done)return;
    status.textContent='Загрузка занимает слишком много времени. Проверьте связь и доступность файлов приложения.';
    controls.style.display='block';
  },27000);
  window.addEventListener('error',e=>{
    if(done)return;
    const src=String(e.target&&e.target.src||'');
    if(src.includes('flutter_bootstrap.js')||src.includes('main.dart.js')){
      status.textContent='Не удалось загрузить файлы приложения из этой сети.';
      controls.style.display='block';
    }
  },true);
})();
</script>
"""
s=s.replace('<body>','<body>\n'+banner,1)
index.write_text(s,encoding='utf-8')

# The existing push worker had NO fetch caching; mobile reloads downloaded
# CanvasKit and sqlite wasm again and again. Cache ONLY versioned public static
# same-origin resources. Never intercept personal data, API endpoints or uploads.
s=worker.read_text(encoding='utf-8')
assert s.count("self.addEventListener('activate',event=>event.waitUntil(self.clients.claim()));")==1
new_worker="""const PROMYSEL_PUBLIC_CACHE='promysel-static-__BUILD__';
self.addEventListener('activate',event=>event.waitUntil((async()=>{
  const names=await caches.keys();
  await Promise.all(names.filter(n=>n.startsWith('promysel-static-')&&
    n!==PROMYSEL_PUBLIC_CACHE).map(n=>caches.delete(n)));
  await self.clients.claim();
})()));
self.addEventListener('fetch',event=>{
  const request=event.request;
  if(request.method!=='GET')return;
  const url=new URL(request.url);
  if(url.origin!==self.location.origin)return;
  const path=url.pathname;
  const publicAsset=path.startsWith('/canvaskit/')||path.startsWith('/assets/')||
    path==='/sqlite3.wasm'||path==='/sqflite_sw.js';
  if(!publicAsset)return;
  event.respondWith((async()=>{
    const cache=await caches.open(PROMYSEL_PUBLIC_CACHE);
    const cached=await cache.match(request);
    if(cached)return cached;
    const response=await fetch(request);
    if(response.ok)event.waitUntil(cache.put(request,response.clone()).catch(()=>{}));
    return response;
  })());
});
""".replace('__BUILD__',build_id)
s=s.replace("self.addEventListener('activate',event=>event.waitUntil(self.clients.claim()));",new_worker,1)
worker.write_text(s,encoding='utf-8')

# A tiny diagnostic page can be opened on the actual mobile operator's
# network. It does not collect user identity, session tokens or traffic.
diagnostics="""<!doctype html><html lang="ru"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Проверка сети — Промысел</title>
<style>
body{max-width:580px;margin:20px auto;padding:18px;color:#1b3243;
font:15px/1.5 system-ui,-apple-system,sans-serif;background:#f4f9fd}
h1{font-size:23px}.item{background:#fff;border-radius:12px;padding:12px;margin:10px 0;
border:1px solid #dfebf4}.ok{color:#176f46}.bad{color:#b33d39}
button{background:#0b4f91;color:#fff;padding:11px 17px;border:0;border-radius:9px;font-size:15px}
small{color:#557287}#report{white-space:pre-wrap;overflow-wrap:anywhere}
</style></head><body>
<h1>Промысел · проверка подключения</h1>
<p>Откройте эту страницу через сотовую сеть, без Wi-Fi и VPN. Проверяем только
доступность статических файлов и публичного API, без входа в аккаунт.</p>
<p id="network"></p><button id="run">Проверить повторно</button>
<div id="results"></div><button id="copy">Скопировать результат</button>
<p><small>При ошибке DNS/HTTPS, когда браузер вообще не может открыть эту
страницу, проблема возникает до загрузки приложения: проверьте доступность
домена у мобильного оператора либо другой адрес сайта.</small></p>
<script>
const api='https://xptmcufhuvtcunqzlsme.supabase.co/functions/v1/promysel-compat/health';
const targets=[
 ['Страница сайта','/index.html','HEAD'],
 ['Загрузчик Flutter','/flutter_bootstrap.js','HEAD'],
 ['Приложение JavaScript','/main.dart.js','HEAD'],
 ['Локальный CanvasKit WebAssembly','/canvaskit/canvaskit.wasm','HEAD'],
 ['Локальная SQLite','/sqlite3.wasm','HEAD'],
 ['Сервер Supabase',api,'GET']
];
const div=document.getElementById('results');
document.getElementById('network').textContent=
 'Сеть: '+(navigator.connection?.effectiveType||'не определена')+
 '; браузер сообщает: '+(navigator.onLine?'онлайн':'офлайн');
let latest='';
async function probe(name,path,method){
 const ac=new AbortController(),start=performance.now();
 const timer=setTimeout(()=>ac.abort(),9500);
 try{
  const res=await fetch(path,{method,cache:'no-store',signal:ac.signal});
  const ms=Math.round(performance.now()-start);
  let info='HTTP '+res.status+' · '+ms+' мс';
  if(path.endsWith('.wasm'))info+=' · MIME '+(res.headers.get('content-type')||'не указан');
  const ok=res.ok;
  return{name,ok,info};
 }catch(e){return{name,ok:false,info:e.name==='AbortError'?'Тайм-аут 9,5 с':'Сетевая ошибка / DNS / CORS'};}
 finally{clearTimeout(timer);}
}
async function run(){
 div.textContent='Выполняется проверка…';
 const rs=await Promise.all(targets.map(t=>probe(...t)));
 latest='Промысел v2.01 · '+location.hostname+' · '+new Date().toISOString()+'\\n'+
 rs.map(x=>x.name+': '+x.info).join('\\n');
 div.innerHTML='';
 for(const r of rs){
  const el=document.createElement('div');el.className='item '+(r.ok?'ok':'bad');
  el.textContent=(r.ok?'✓ ':'✕ ')+r.name+': '+r.info;div.appendChild(el);
 }
}
document.getElementById('run').onclick=run;
document.getElementById('copy').onclick=async()=>{
 try{await navigator.clipboard.writeText(latest);}catch(_){
  const el=document.createElement('textarea');el.value=latest;
  document.body.appendChild(el);el.select();document.execCommand('copy');el.remove();
 }
};
run();
</script></body></html>"""
(root/'diagnostics.html').write_text(diagnostics,encoding='utf-8')
assert 'gstatic.com/flutter-canvaskit' not in bootstrap.read_text().split('_flutter.loader.load(')[-1]
assert 'canvasKitBaseUrl:"/canvaskit/"' in bootstrap.read_text()
assert 'Cache-Control' not in worker.read_text()
assert (root/'diagnostics.html').is_file()
print('PASS v2.01: local CanvasKit, startup status, same-origin asset cache, diagnostic for mobile operators')
