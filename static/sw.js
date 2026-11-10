/* SichoSana — cache versionné et flux MP3 compatibles Safari / HTTP Range.
   Une réponse HTTP 206 ne peut pas être stockée dans CacheStorage.
   Hors ligne, servir un fragment 206 depuis le fichier complet (200) en cache.
   Ne jamais mettre en cache l'API ni les données de compte. */
const VERSION='sichosana-static-v10';
const ESSENTIAL=['/','/index.html','/styles.css','/app.js','/auth.js','/icon.svg',
  '/manifest.webmanifest','/data/yoga.json','/data/yoga-api-library.json',
  '/data/pose-guidance.json','/data/salutations.json','/data/meditations.json','/data/programs.json',
  '/data/reflections.json','/data/pose-media.json','/media/yoga-hero.png'];

self.addEventListener('install',event=>{
 event.waitUntil(caches.open(VERSION).then(cache=>cache.addAll(ESSENTIAL)).then(()=>self.skipWaiting()));
});
self.addEventListener('activate',event=>{
 event.waitUntil(caches.keys().then(keys=>Promise.all(
   keys.filter(k=>k.startsWith('sichosana-static-')&&k!==VERSION).map(k=>caches.delete(k))
 )).then(()=>self.clients.claim()));
});

function parseAudioRange(value,total){
 if(!value||!/^bytes=\d*-\d*$/.test(value))return null;
 const [first,last]=value.slice(6).split('-');
 if(!first&&!last)return null;
 let from=first?Number(first):Math.max(0,total-Number(last));
 let to=last&&first?Math.min(total-1,Number(last)):total-1;
 if(!Number.isSafeInteger(from)||!Number.isSafeInteger(to)||from>=total||from>to||to<0)return null;
 return {from,to};
}
async function cachedAudioFragment(request){
 // Ne correspond qu'au MP3 téléchargé en entier (HTTP 200),
 // jamais à une réponse partielle HTTP 206.
 const fullRequest=new Request(request.url,{method:'GET'});
 const cached=await caches.match(fullRequest,{ignoreSearch:false});
 if(!cached||cached.status!==200)return null;
 const bytes=await cached.arrayBuffer();
 const length=bytes.byteLength,range=parseAudioRange(request.headers.get('Range'),length);
 if(!range)return new Response(null,{status:416,headers:{
   'Content-Range':'bytes */'+length,'Accept-Ranges':'bytes','Content-Length':'0'
 }});
 const {from,to}=range;
 const headers=new Headers();
 headers.set('Content-Type','audio/mpeg');
 headers.set('Accept-Ranges','bytes');
 headers.set('Content-Range','bytes '+from+'-'+to+'/'+length);
 headers.set('Content-Length',String(to-from+1));
 headers.set('Cache-Control','no-store');
 return new Response(bytes.slice(from,to+1),{status:206,headers});
}
const audioCaching=new Map();
async function cacheWholeAudio(url){
 if(audioCaching.has(url))return audioCaching.get(url);
 const promise=(async()=>{
  try{
   const cache=await caches.open(VERSION);
   const cached=await cache.match(url);
   if(cached?.status===200)return;
   // Fetch direct depuis le worker, sans en-tête Range :
   // le navigateur peut faire des requêtes 206, mais le cache hors-ligne a
   // besoin d'un fichier complet 200.
   const response=await fetch(new Request(url,{method:'GET',cache:'no-store'}));
   const len=Number(response.headers.get('content-length')||0);
   if(response.status!==200||!response.ok||len>8_000_000)return;
   await cache.put(url,response);
  }catch(_){
   // La lecture réseau partielle doit rester fonctionnelle.
  }finally{
   audioCaching.delete(url);
  }
 })();
 audioCaching.set(url,promise);
 return promise;
}
async function audioResponse(request){
 if(request.headers.has('Range')){
  try{
   const offline=await cachedAudioFragment(request);
   if(offline)return offline;
  }catch(e){
   // Safari peut refuser CacheStorage : repli direct sur le réseau.
  }
  // Ne PAS effectuer CacheStorage.put() sur ce fetch : statut 206.
  return fetch(request);
 }
 const cached=await caches.match(request);
 if(cached)return cached;
 const response=await fetch(request);
 if(response.status===200){
  // Ne jamais empêcher la lecture si cache.put échoue.
  caches.open(VERSION).then(cache=>cache.put(request,response.clone())).catch(()=>{});
 }
 return response;
}
self.addEventListener('fetch',event=>{
 const request=event.request;
 if(request.method!=='GET')return;
 const url=new URL(request.url);
 if(url.origin!==self.location.origin)return;
 if(url.pathname.startsWith('/api/'))return;
 if(url.pathname.startsWith('/voice/')&&url.pathname.endsWith('.mp3')){
  // Safari demande souvent des segments HTTP Range. Mettre en cache la
  // version complète en parallèle permet une vraie lecture hors ligne.
  if(request.headers.has('Range'))event.waitUntil(cacheWholeAudio(request.url));
  event.respondWith(audioResponse(request));
  return;
 }
 if(request.mode==='navigate'){
  event.respondWith(fetch(request).then(response=>response.ok?response:Promise.reject(Error('offline')))
    .catch(()=>caches.match('/index.html')));
  return;
 }
 event.respondWith(caches.match(request).then(cached=>cached||fetch(request).then(response=>{
  if(response.status===200&&(ESSENTIAL.includes(url.pathname)||url.pathname.startsWith('/media/'))){
   caches.open(VERSION).then(cache=>cache.put(request,response.clone())).catch(()=>{});
  }
  return response;
 })));
});
