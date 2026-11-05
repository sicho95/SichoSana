/* SichoSana offline-first: shell, catalogues et assets audios optionnels. */
const VERSION='sichosana-v1-20261105';
const CORE=['/','/index.html','/styles.css','/app.js','/icon.svg','/manifest.webmanifest','/data/yoga.json','/data/meditations.json'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(VERSION).then(cache=>cache.addAll(CORE)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('sichosana-v1-')&&k!==VERSION).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{
 const req=e.request;if(req.method!=='GET'||new URL(req.url).origin!==location.origin)return;
 const url=new URL(req.url);
 if(url.pathname.startsWith('/api/'))return;
 if(url.pathname.startsWith('/voice/')){e.respondWith(caches.match(req).then(hit=>hit||fetch(req)));return}
 if(req.mode==='navigate'){e.respondWith(fetch(req).catch(()=>caches.match('/index.html')));return}
 e.respondWith(caches.match(req).then(hit=>hit||fetch(req).then(response=>{if(response.ok){const copy=response.clone();caches.open(VERSION).then(cache=>cache.put(req,copy))}return response})));
});
self.addEventListener('push',e=>{
 let data={};try{data=e.data.json()}catch(_){data={title:'SichoSana',body:'Un moment pour toi'}}
 e.waitUntil(self.registration.showNotification(String(data.title||'SichoSana'),{body:String(data.body||'Un moment pour toi'),icon:'/icon.svg',tag:'sichosana-reminder',data:{url:'/'}}))
});
self.addEventListener('notificationclick',e=>{e.notification.close();e.waitUntil(clients.matchAll({type:'window',includeUncontrolled:true}).then(windows=>{const open=windows.find(w=>new URL(w.url).origin===location.origin);return open?open.focus():clients.openWindow('/')}))});
