/* SichoSana — caches indépendants, sans toucher aux autres PWA. */
const VERSION='sichosana-static-v2';
const ESSENTIAL=['/','/index.html','/styles.css','/app.js','/icon.svg','/manifest.webmanifest','/data/yoga.json','/data/meditations.json'];
self.addEventListener('install',event=>{event.waitUntil(caches.open(VERSION).then(cache=>cache.addAll(ESSENTIAL)).then(()=>self.skipWaiting()));});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('sichosana-static-')&&k!==VERSION).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',event=>{
 const request=event.request;
 if(request.method!=='GET')return;
 const url=new URL(request.url);if(url.origin!==self.location.origin)return;
 if(url.pathname.startsWith('/api/'))return; // Ne jamais conserver des comptes ou jetons en cache.
 if(request.mode==='navigate'){
  event.respondWith(fetch(request).then(response=>response.ok?response:Promise.reject(new Error('offline'))).catch(()=>caches.match('/index.html')));
  return;
 }
 event.respondWith(caches.match(request).then(cached=>cached||fetch(request).then(async response=>{
   if(response.ok && (ESSENTIAL.includes(url.pathname) || url.pathname.startsWith('/voice/') || url.pathname.startsWith('/media/'))){
     const cache=await caches.open(VERSION);await cache.put(request,response.clone());
   }
   return response;
 })));
});
