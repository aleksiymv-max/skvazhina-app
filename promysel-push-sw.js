'use strict';
self.addEventListener('install',()=>self.skipWaiting());
const PROMYSEL_PUBLIC_CACHE='promysel-static-0f0cd5a1a572';
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

self.addEventListener('push',event=>{
  event.waitUntil((async()=>{
    let data={};
    try{data=event.data?event.data.json():{};}catch(_){}
    const title=String(data.title||'Новое задание · Промысел').slice(0,150);
    const body=String(data.body||'Откройте приложение для просмотра задания').slice(0,240);
    const count=Math.max(1,Math.min(99,Number(data.badgeCount)||1));
    if(self.navigator&&typeof self.navigator.setAppBadge==='function'){
      try{await self.navigator.setAppBadge(count);}catch(_){}
    }
    await self.registration.showNotification(title,{
      body,
      icon:'/icons/Icon-192.png',
      badge:'/icons/Icon-192.png',
      tag:String(data.tag||'promysel-task'),
      renotify:false,
      data:{url:'/tasks',taskId:String(data.taskId||'')},
    });
  })());
});
self.addEventListener('notificationclick',event=>{
  event.notification.close();
  event.waitUntil((async()=>{
    const clients=await self.clients.matchAll({type:'window',includeUncontrolled:true});
    const match=clients.find(c=>c.url.startsWith(self.location.origin));
    if(match){await match.focus();if('navigate' in match)await match.navigate('/tasks');}
    else await self.clients.openWindow('/tasks');
  })());
});
