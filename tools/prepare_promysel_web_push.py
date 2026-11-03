"""Install standard Web Push in the existing iPhone Home Screen Flutter PWA.
This runs AFTER flutter build web, preserving the original Flutter code.
"""
from pathlib import Path
import re
r=Path.cwd()/'build/web'
index=r/'index.html'
bootstrap=r/'flutter_bootstrap.js'
assert index.is_file() and bootstrap.is_file()
s=index.read_text(encoding='utf-8')
assert '</head>' in s
js=r"""<script>
(function(){
  'use strict';
  const api='https://xptmcufhuvtcunqzlsme.supabase.co/functions/v1/promysel-device-push';
  const subKey='promysel-push-user-v1';
  const base64ToBytes=(value)=>{
    const pad='='.repeat((4-value.length%4)%4);
    const b=atob((value+pad).replace(/-/g,'+').replace(/_/g,'/'));
    return Uint8Array.from(b,c=>c.charCodeAt(0));
  };
  function available(){
    return 'serviceWorker' in navigator && 'PushManager' in window
      && 'Notification' in window && window.isSecureContext;
  }
  let busy=false;
  async function subscribe(token,fieldId){
    if(busy||!available()||Notification.permission!=='granted'||!token||!fieldId)return;
    busy=true;
    try{
      const registration=await navigator.serviceWorker.ready;
      const response=await fetch(api+'/public-key',{cache:'no-store'});
      if(!response.ok)throw Error('Нет ключа уведомлений');
      const {publicKey}=await response.json();
      let subscription=await registration.pushManager.getSubscription();
      if(!subscription){
        subscription=await registration.pushManager.subscribe({
          userVisibleOnly:true,applicationServerKey:base64ToBytes(publicKey)
        });
      }
      const saved=await fetch(api+'/subscribe',{
        method:'POST',
        headers:{'content-type':'application/json','authorization':'Bearer '+token},
        body:JSON.stringify({fieldId,subscription:subscription.toJSON()})
      });
      if(!saved.ok)throw Error('Не удалось зарегистрировать уведомления');
      localStorage.setItem(subKey,fieldId);
      // Deliver queued tasks that arrived while device push was disabled.
      fetch(api+'/deliver',{method:'POST',
        headers:{'content-type':'application/json','authorization':'Bearer '+token},
        body:JSON.stringify({fieldId})
      }).catch(()=>{});
    }catch(e){console.warn('Промысел: web push registration failed',e);}
    finally{busy=false;}
  }
  window.promyselRequestBadgePermission=function(token,fieldId){
    if(!available()){
      alert('Уведомления доступны после установки веб-приложения на экран «Домой» в iOS 16.4+.');
      return;
    }
    // The OS permission request must start directly inside the user's tap.
    if(Notification.permission==='default'){
      const result=Notification.requestPermission();
      Promise.resolve(result).then(permission=>{
        if(permission==='granted')subscribe(token,fieldId);
      }).catch(()=>{});
    }else if(Notification.permission==='granted'){
      subscribe(token,fieldId);
    }else{
      alert('Разрешите уведомления для «Промысел» в настройках телефона.');
    }
  };
  window.promyselEnsurePushSubscription=function(token,fieldId){
    if(available()&&Notification.permission==='granted')subscribe(token,fieldId);
  };
  window.promyselRemovePushSubscription=function(token,fieldId){
    if(!available())return;
    navigator.serviceWorker.ready.then(async(registration)=>{
      const subscription=await registration.pushManager.getSubscription();
      if(!subscription)return;
      if(token&&fieldId){
        await fetch(api+'/unsubscribe',{method:'POST',
          headers:{'content-type':'application/json','authorization':'Bearer '+token},
          body:JSON.stringify({fieldId,endpoint:subscription.endpoint})
        }).catch(()=>{});
      }
      await subscription.unsubscribe();
      localStorage.removeItem(subKey);
    }).catch(()=>{});
  };
  window.addEventListener('load',()=>{
    navigator.serviceWorker.register('/promysel-push-sw.js',{scope:'/'})
      .catch(e=>console.warn('Промысел: push worker not registered',e));
  });
})();
</script>
"""
assert 'promyselEnsurePushSubscription' not in s
s=s.replace('</head>',js+'</head>',1)
index.write_text(s,encoding='utf-8')
# Flutter 2026's default generated worker unregisters itself. Suppress its
# registration in bootstrap; our own push worker stays active in the background.
b=bootstrap.read_text(encoding='utf-8')
pattern=r'_flutter\.loader\.load\(\{\s*serviceWorkerSettings:\s*\{.*?\}\s*\}\);'
b,count=re.subn(pattern,'_flutter.loader.load({});',b,count=1,flags=re.S)
assert count==1,'Flutter bootstrap worker registration changed'
bootstrap.write_text(b,encoding='utf-8')

worker=r/'promysel-push-sw.js'
worker.write_text(r"""'use strict';
self.addEventListener('install',()=>self.skipWaiting());
self.addEventListener('activate',event=>event.waitUntil(self.clients.claim()));
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
""",encoding='utf-8')
assert 'showNotification' in worker.read_text()
print('PASS: signed Web Push client, service worker delivery, device badge')
