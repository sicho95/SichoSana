/* SichoSana — PWA locale, écrans adaptés iPhone/iPad/ordinateur.
   Conserver la charte graphique dans styles.css et l'identité Vivienne ResurGo. */
'use strict';
import * as Accounts from './auth.js';
const $ = (s) => document.querySelector(s);
const escapeHTML = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const uid = () => (crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + Math.random().toString(36).slice(2));
const formatTime = (n) => { const s = Math.max(0, Math.ceil(n)); return Math.floor(s/60).toString().padStart(2,'0')+':'+(s%60).toString().padStart(2,'0'); };
const todayKey = () => { const d = new Date(); return [d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-'); };
const logo = '<img class="lotus-mark" src="/icon.svg" alt="" width="40" height="40">';
const nav = [{id:'home',text:'Accueil',glyph:'home'},{id:'yoga',text:'Yoga',glyph:'lotus'},{id:'meditate',text:'Méditer',glyph:'sun'},{id:'astro',text:'Astro',glyph:'moon'},{id:'profile',text:'Profil',glyph:'user'}];
const iconPaths={
 home:'<path d="m3 10 9-7 9 7v10H3z"/><path d="M9 20v-7h6v7"/>',
 lotus:'<path d="M12 20C7.5 17 6 11 12 4c6 7 4.5 13 0 16z"/><path d="M11 20c-5 1-9-3-9-9 4 0 8 2 9 9zm2 0c5 1 9-3 9-9-4 0-8 2-9 9z"/>',
 sun:'<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M4.9 4.9l1.5 1.5m11.2 11.2 1.5 1.5m0-14.2-1.5 1.5M6.4 17.6l-1.5 1.5"/>',
 moon:'<path d="M20.3 15.7A9 9 0 0 1 8.3 3.7 9 9 0 1 0 20.3 15.7z"/>',
 user:'<circle cx="12" cy="8" r="4"/><path d="M4 21c0-5 3.6-8 8-8s8 3 8 8"/>',
 settings:'<circle cx="12" cy="12" r="3.5"/><path d="M12 2v3m0 14v3M2 12h3m14 0h3M5 5l2.3 2.3m9.4 9.4L19 19m0-14-2.3 2.3m-9.4 9.4L5 19"/>',
 bell:'<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9z"/><path d="M10 21h4"/>'
};
function uiIcon(key){return '<svg aria-hidden="true" viewBox="0 0 24 24" width="23" height="23" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'+(iconPaths[key]||iconPaths.lotus)+'</svg>';}
const signs = ['Bélier','Taureau','Gémeaux','Cancer','Lion','Vierge','Balance','Scorpion','Sagittaire','Capricorne','Verseau','Poissons'];
let reflections={reflections:[]}, poseMedia={photos:[]}, poseGuidance={poses:{}}, astrologyLive=null, astroPeriod='daily', yogaTab='seances';
const defaultProfile = () => ({id:uid(),name:'Mon espace',theme:'linen',meditationStyle:'equilibree',practiceMode:'initiation',zodiac:'',favorites:[],history:[],createdAt:Date.now(),modifiedAt:Date.now()});
const initialState = () => { const p=defaultProfile(); return {schemaVersion:1,profiles:[p],activeProfileId:p.id,revision:0}; };
let db, state, yoga={poses:[],routines:[]}, meditations={sessions:[]}, programs={programs:[]}, page='home', routineFilter='Tous', poseFilter='Tous', meditationFilter='Toutes', modal='', session=null, timer=null, audio=null, manifest=null, voiceStatus='', syncBusy=false, conflict=null, syncTimer=null, syncStatus='';
function openDB(){
 return new Promise((resolve,reject)=>{
   const request=indexedDB.open('sichosana-v1',1);
   request.onupgradeneeded=()=>{const d=request.result;if(!d.objectStoreNames.contains('state'))d.createObjectStore('state');};
   request.onerror=()=>reject(request.error);request.onsuccess=()=>resolve(request.result);
 });
}
function dbRead(key){return new Promise((resolve,reject)=>{const t=db.transaction('state','readonly').objectStore('state').get(key);t.onsuccess=()=>resolve(t.result);t.onerror=()=>reject(t.error);});}
function dbWrite(key,value){return new Promise((resolve,reject)=>{const t=db.transaction('state','readwrite').objectStore('state').put(value,key);t.onsuccess=()=>resolve();t.onerror=()=>reject(t.error);});}
function profile(){return state.profiles.find(x=>x.id===state.activeProfileId)||state.profiles[0];}
async function save(auto=true){try{if(Accounts.user())await dbWrite('account:'+Accounts.user().id,state);if(auto)scheduleAutoSync();}catch(err){notice('Sauvegarde locale impossible : '+err.message);}}
function touch(){profile().modifiedAt=Date.now();save();}
function notice(text){const e=$('#toast');e.textContent=text;e.classList.add('show');clearTimeout(notice.timeout);notice.timeout=setTimeout(()=>e.classList.remove('show'),4000);}
function brand(){return '<div class="brand">'+logo+'<span>Sicho<span>Sana</span></span></div>';}
function navButton(item){return '<button type="button" class="nav-link" data-action="page" data-value="'+item.id+'" '+(page===item.id?'aria-current="page"':'')+'><span class="nav-glyph">'+uiIcon(item.glyph)+'</span><span>'+item.text+'</span></button>';}
function renderShell(){
 const all=Accounts.user()?.role==='admin'?[...nav,{id:'admin',text:'Admin',glyph:'settings'}]:nav;
 $('#sidebar').innerHTML=brand()+'<nav>'+all.map(navButton).join('')+'</nav><p class="sidebar-tag">Un moment pour soi,<br>à son rythme.</p>';
 $('#bottomnav').innerHTML=nav.map(navButton).join(''); // cinq onglets fixes, admin dans Profil
 $('#topbar').innerHTML='<div class="desktop-brand">'+brand()+'</div><div class="top-actions"><span class="connection-pill">'+(navigator.onLine?'● En ligne':'○ Hors ligne')+'</span><button class="icon-btn" type="button" data-action="notifications" aria-label="Notifications">'+uiIcon('bell')+'</button><button class="profile-chip" type="button" data-action="page" data-value="profile"><span class="dot"></span>'+escapeHTML(Accounts.user()?.pseudo||'')+'</button></div>';
}
function heading(kicker,title,subtitle){return '<div class="page-heading"><div><div class="eyebrow">'+kicker+'</div><h1>'+title+'</h1>'+(subtitle?'<p class="subtitle">'+subtitle+'</p>':'')+'</div></div>';}
function routineCard(r){
 const fav=profile().favorites.includes(r.id);
 return '<article class="card routine-card"><div class="routine-visual"><span aria-hidden="true">◈</span></div><div class="routine-body"><div class="eyebrow">'+escapeHTML(r.family)+'</div><h3>'+escapeHTML(r.name)+'</h3><p>'+escapeHTML(r.subtitle)+'</p><div class="meta"><span>'+r.duration+' min</span><span>'+escapeHTML(r.level)+'</span><span>'+r.poseIds.length+' postures</span></div><div class="routine-footer"><button class="primary" type="button" data-action="start-yoga" data-value="'+escapeHTML(r.id)+'">Commencer</button><button class="small-btn" type="button" data-action="favorite" data-value="'+escapeHTML(r.id)+'" aria-label="'+(fav?'Retirer des favoris':'Ajouter aux favoris')+'">'+(fav?'♥':'♡')+'</button></div></div></article>';
}
function weeklyStats(){
 const now=new Date();const start=new Date(now);start.setDate(now.getDate()-((now.getDay()+6)%7));start.setHours(0,0,0,0);
 const dates=Array.from({length:7},(_,i)=>{const d=new Date(start);d.setDate(start.getDate()+i);return [d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-');});
 const done=new Set(profile().history.map(h=>h.date));
 return '<div class="week-dots" aria-label="Pratique cette semaine">'+dates.map((d,i)=>'<span class="'+(done.has(d)?'done':'')+'" title="'+d+'">'+['L','M','M','J','V','S','D'][i]+'</span>').join('')+'</div>';
}
function dailyReflection(){
 const p=profile(),list=reflections.reflections||[];
 if(!list.length)return 'Accorde-toi le droit d’habiter pleinement cet instant.';
 const history=(p.reflectionHistory||[]).filter(x=>x.date>=new Date(Date.now()-14*86400000).toISOString().slice(0,10));
 const found=history.find(x=>x.date===todayKey());
 if(found&&Number.isInteger(found.index)&&list[found.index])return list[found.index];
 const seed=(todayKey()+p.id+(Accounts.user()?.id||'')).split('').reduce((v,c)=>(v*33+c.charCodeAt(0))>>>0,5381);
 const recent=new Set(history.slice(-10).map(x=>x.index));
 let index=seed%list.length;
 for(let n=0;n<list.length&&recent.has(index);n++)index=(index+37)%list.length;
 p.reflectionHistory=[...history,{date:todayKey(),index}].slice(-30);
 touch();
 return list[index];
}
function localAstro(){
 const sign=profile().zodiac;
 if(!sign)return {text:'Choisis ton signe ci-dessous pour découvrir ton horoscope en français.',sign:'Non configuré',available:false};
 if(astrologyLive?.sign===sign && astrologyLive?.period===astroPeriod && astrologyLive?.date===todayKey())return astrologyLive;
 return {text:'Consulte ton horoscope en français, avec un lien direct vers la source.',sign,available:false};
}
async function refreshAstrology(){
 const sign=profile()?.zodiac;
 if(!sign||!navigator.onLine)return;
 try{
  const result=await Accounts.api('content/horoscope?sign='+encodeURIComponent(sign)+'&period='+astroPeriod);
  if(result.sign===profile()?.zodiac && result.period===astroPeriod){astrologyLive=result;if(page==='astro'||page==='home')render();}
 }catch(e){astrologyLive={sign,period:astroPeriod,text:'Source momentanément indisponible.',available:false};if(page==='astro')render();}
}
function activeProgram(){return programs.programs.find(x=>x.id===profile().selectedProgram)||programs.programs[0];}
function progressProgram(program){
 const counts=new Map();
 for(const h of profile().history){
  if(!h.completed)continue;
  const key=h.type+':'+h.ref;counts.set(key,(counts.get(key)||0)+1);
 }
 let done=0;
 for(const s of program.steps){
  const key=s.type+':'+s.ref,count=counts.get(key)||0;
  if(!count)break;
  counts.set(key,count-1);done++;
 }
 return done;
}
function programSidebar(){
 const p=activeProgram();if(!p)return '';
 const done=progressProgram(p),next=p.steps[Math.min(done,p.steps.length-1)],end=done>=p.steps.length;
 return '<div class="card program-panel"><div class="eyebrow">Mon parcours</div><h3>'+escapeHTML(p.name)+'</h3><div class="progress-track"><span style="width:'+Math.round(done/p.steps.length*100)+'%"></span></div><p>'+done+' / '+p.steps.length+' étapes terminées</p><p class="muted">'+escapeHTML(end?'Parcours terminé. Tu peux choisir un autre programme.':next.label)+'</p>'+(end?'<button class="secondary" data-action="page" data-value="yoga">Découvrir les programmes</button>':'<button class="primary" data-action="'+(next.type==='yoga'?'start-yoga':'start-med')+'" data-value="'+escapeHTML(next.ref)+'">Continuer mon parcours</button>')+'</div>';
}
function programsSection(){
 return '<div class="section-heading"><h2>Parcours & programmes</h2></div><div class="cards program-cards">'+programs.programs.map(p=>{
  const done=progressProgram(p),selected=activeProgram()?.id===p.id;
  return '<article class="card"><span class="eyebrow">'+escapeHTML(p.level)+' · '+p.steps.length+' étapes</span><h3>'+escapeHTML(p.name)+'</h3><p class="muted">'+escapeHTML(p.subtitle)+'</p><div class="progress-track"><span style="width:'+Math.round(done/p.steps.length*100)+'%"></span></div><p>'+done+' / '+p.steps.length+' terminées</p><button class="'+(selected?'secondary':'primary')+'" data-action="select-program" data-value="'+escapeHTML(p.id)+'">'+(selected?'Parcours actuel':'Choisir ce parcours')+'</button><ol class="program-steps">'+p.steps.map((step,i)=>'<li class="'+(i<done?'done':'')+'">'+escapeHTML(step.label)+'</li>').join('')+'</ol></article>';
 }).join('')+'</div>';
}
function practiceMode(){
 return ['initiation','douce','complete'].includes(profile().practiceMode)?profile().practiceMode:'initiation';
}
function dailyRoutine(){
 const p=profile(),day=todayKey();
 const saved=yoga.routines.find(r=>r.id===p.dailyChoice?.id);
 if(p.dailyChoice?.date===day&&saved)return saved;
 const eligible=yoga.routines.filter(r=>practiceMode()==='complete'||r.level!=='Intermédiaire');
 const options=eligible.length?eligible:yoga.routines;
 const recent=p.history.slice(-3).map(h=>h.ref);
 const hour=new Date().getHours();
 const hash=s=>s.split('').reduce((x,ch)=>(x*31+ch.charCodeAt(0))>>>0,7);
 const candidates=options.map(r=>({r,score:(hash(day+p.id+r.id)%17)/10+(recent.includes(r.id)?-9:0)+(hour<11&&r.id==='eveil-doux'?3:0)+(hour>=19&&r.id==='soir-calme'?3:0)+(p.favorites.includes(r.id)?.9:0)}));
 const chosen=candidates.sort((a,b)=>b.score-a.score)[0]?.r||yoga.routines[0];
 p.dailyChoice={date:day,id:chosen.id};
 save();
 return chosen;
}
function home(){
 const r=dailyRoutine(),astro=localAstro(),reflection=dailyReflection(),n=profile().history.filter(x=>x.date===todayKey()).length;
 return heading('Bienvenue','Un moment pour soi','Du mouvement, de la douceur et un peu de temps pour toi.')+
 '<div class="home-desktop-layout"><div class="home-main"><section class="hero"><div class="hero-content"><span class="pill">Séance du jour</span><h2>'+escapeHTML(r.name)+'</h2><p>'+escapeHTML(r.subtitle)+'</p><div class="meta"><span>'+r.duration+' min</span><span>'+escapeHTML(r.level)+'</span></div><button class="primary" type="button" data-action="start-yoga" data-value="'+r.id+'">▷ Commencer ma séance</button></div><div class="hero-art" aria-hidden="true">'+logo+'</div></section>'+
 '<div class="wellness-row"><article class="tile"><div class="tile-icon">☼</div><h3>Méditation guidée</h3><p>Une parenthèse calme, avec un niveau de guidage qui respecte ton rythme.</p><button class="text-link" data-action="page" data-value="meditate">Découvrir les séances ›</button></article><article class="tile"><div class="tile-icon">☾</div><h3>Astro du jour</h3><p>'+escapeHTML(astro.text)+'</p><button class="text-link" data-action="page" data-value="astro">Mon inspiration ›</button></article></div>'+
 '<div class="section-heading"><h2>Explorer le yoga</h2><button class="text-link" data-action="page" data-value="yoga">Toutes les séances ›</button></div><div class="cards">'+yoga.routines.slice(1,4).map(routineCard).join('')+'</div></div>'+
 '<aside class="home-aside">'+programSidebar()+'<div class="card"><div class="eyebrow">Rituel de la semaine</div><h3>7 jours de présence</h3><p class="muted">La régularité se construit sans pression.</p>'+weeklyStats()+'<p class="muted">'+n+' séance'+(n>1?'s':'')+' terminée'+(n>1?'s':'')+' aujourd’hui.</p></div>'+
 '<div class="card reflection-card"><div class="eyebrow">Réflexion du jour</div><p class="daily-reflection">'+escapeHTML(reflection)+'</p></div><div class="card"><div class="eyebrow">Ta progression</div>'+smallStats()+'<button class="text-link" data-action="page" data-value="profile">Voir mon suivi ›</button></div></aside></div>';
}
function pills(opts,active,action){return '<div class="filter-bar">'+opts.map(x=>'<button class="filter" type="button" data-action="'+action+'" data-value="'+escapeHTML(x)+'" aria-pressed="'+(x===active)+'">'+escapeHTML(x)+'</button>').join('')+'</div>';}
function yogaApiImage(id){
 const guidance=poseGuidance.poses?.[id];
 const ref=id.startsWith('yoga-api-')?id:guidance?.apiPose;
 const pose=yoga.poses.find(x=>x.id===ref);
 if(!ref||!pose?.imageSource)return null;
 return {src:'/media/yoga-api/'+ref+'.png',source:pose.imageSource};
}
function posePicture(id,kind='thumb'){
 const media=yogaApiImage(id);
 if(!media)return '<span class="pose-missing" aria-label="Illustration exacte non disponible">Illustration à compléter</span>';
 return '<img loading="lazy" decoding="async" data-pose-image="'+escapeHTML(id)+'" class="pose-photo '+kind+'" src="'+escapeHTML(media.src)+'" alt="Illustration Yoga API de la posture '+escapeHTML(yoga.poses.find(p=>p.id===id)?.nom||id)+'">';
}
function yogaPage(){
 const routines=yoga.routines.filter(r=>routineFilter==='Tous'||r.family===routineFilter||(routineFilter==='Favoris'&&profile().favorites.includes(r.id)));
 const poses=yoga.poses.filter(p=>poseFilter==='Tous'||p.niveau===poseFilter);
 return heading('Pratiquer','Yoga','Une séance à ton rythme et une bibliothèque pour découvrir chaque posture.')+
 '<div class="card yoga-mode-panel"><div><div class="eyebrow">Pratique adaptée</div><h3>Comment souhaites-tu pratiquer ?</h3><p class="muted">Chaque posture peut être préparée et simplifiée avant sa version complète.</p></div><div class="segment yoga-practice-modes">'+[['initiation','Découvrir pas à pas'],['douce','Version douce'],['complete','Pratique complète']].map(([id,label])=>'<button type="button" data-action="practice-mode" data-value="'+id+'" aria-pressed="'+(practiceMode()===id)+'">'+label+'</button>').join('')+'</div></div>'+
 '<div class="yoga-tabs" role="tablist" aria-label="Explorer le yoga">'+
 '<button type="button" role="tab" aria-selected="'+(yogaTab==='seances')+'" data-action="yoga-tab" data-value="seances">Mes séances</button>'+
 '<button type="button" role="tab" aria-selected="'+(yogaTab==='postures')+'" data-action="yoga-tab" data-value="postures">Bibliothèque des postures <small>'+yoga.poses.length+'</small></button></div>'+
 (yogaTab==='seances'?
 '<div class="section-heading"><h2>Les enchaînements</h2></div>'+pills(['Tous','Hatha','Vinyasa','Favoris'],routineFilter,'routine-filter')+
 '<div class="cards">'+(routines.length?routines.map(routineCard).join(''):'<p class="empty">Aucune séance pour ce filtre.</p>')+'</div>'+programsSection():
 '<div class="section-heading"><h2>Découvrir les postures</h2><span class="muted">'+poses.length+' postures</span></div>'+
 '<p class="muted">Une fiche pour chaque posture, avec consignes d’installation et précautions. Illustrations Yoga API locales : la provenance et les licences sont consultables dans le Profil.</p>'+
 pills(['Tous','Débutant','Intermédiaire'],poseFilter,'pose-filter')+
 '<div class="pose-list">'+poses.map(p=>'<button class="pose-item" type="button" data-action="pose" data-value="'+escapeHTML(p.id)+'">'+posePicture(p.id,'thumb')+'<span><strong>'+escapeHTML(p.nom)+'</strong><small>'+escapeHTML(p.sanskrit)+' · '+escapeHTML(p.focus)+'</small></span></button>').join('')+'</div>'+
 '<p class="library-info">La bibliothèque fonctionne sans réseau après une première ouverture. Les postures doivent rester confortables et adaptées à chacun.</p>');
}
function medCard(m){return '<article class="card routine-card meditation-card"><div class="routine-visual"></div><div class="routine-body"><div class="eyebrow">'+escapeHTML(m.category)+'</div><h3>'+escapeHTML(m.name)+'</h3><p>'+escapeHTML(m.description)+'</p><div class="meta"><span>'+m.minutes+' min</span><span>Voix guidée · FR</span></div><button class="primary" data-action="start-med" data-value="'+escapeHTML(m.id)+'">Méditer</button></div></article>';}
function meditationPage(){
 const opts=['Toutes',...new Set(meditations.sessions.map(m=>m.category))];
 const subset=meditations.sessions.filter(m=>meditationFilter==='Toutes'||m.category===meditationFilter);
 return heading('Ralentir','Méditation','Silence, présence et paroles à la juste mesure.')+
 '<div class="card meditation-intro"><div><div class="eyebrow">Un accompagnement à ton rythme</div><h3>Une voix apaisante, et des silences pour respirer</h3><p>Prends le temps d’écouter, de ressentir ou de savourer les pauses. L’accompagnement reste disponible sans réseau après téléchargement.</p></div><button class="secondary" data-action="cache-voice">Rendre les séances disponibles hors ligne</button><small id="voice-status">'+escapeHTML(voiceStatus)+'</small></div>'+
 '<div class="section-heading"><h2>Intensité du guidage</h2></div>'+
 '<div class="segment meditation-levels">'+[['discrete','Discrète'],['equilibree','Équilibrée'],['enveloppante','Enveloppante']].map(([id,t])=>'<button data-action="med-level" data-value="'+id+'" aria-pressed="'+(profile().meditationStyle===id)+'">'+t+'</button>').join('')+'</div><p class="muted">Discrète : longs silences · Équilibrée : quelques repères · Enveloppante : accompagnement plus présent.</p>'+
 '<div class="section-heading"><h2>Choisir un moment</h2></div>'+pills(opts,meditationFilter,'med-filter')+
 '<div class="cards">'+subset.map(medCard).join('')+'</div>';
}
function astroPage(){
 const a=localAstro(),reflection=dailyReflection();
 const link=escapeHTML(a.sourceUrl||'https://sigastra.com/fr/horoscope-du-jour');
 return heading('Un regard sur les étoiles','Astrologie du jour','Une lecture culturelle et symbolique, sans prédiction scientifique.')+
 '<div class="astro-controls"><div class="field"><label for="astro-sign">Mon signe astrologique</label><select id="astro-sign"><option value="">Choisir un signe</option>'+signs.map(s=>'<option value="'+s+'" '+(profile().zodiac===s?'selected':'')+'>'+s+'</option>').join('')+'</select></div>'+
 '<div class="segment astro-periods" role="group" aria-label="Période">'+[['daily','Aujourd’hui'],['weekly','Cette semaine'],['monthly','Ce mois']].map(([id,name])=>'<button type="button" data-action="astro-period" data-value="'+id+'" aria-pressed="'+(astroPeriod===id)+'">'+name+'</button>').join('')+'</div></div>'+
 '<div class="astro-layout"><div class="card astrology-card"><div class="celestial-icon">☾</div><span class="pill">'+escapeHTML(a.sign)+' · '+new Intl.DateTimeFormat('fr-FR',{dateStyle:'long'}).format(new Date())+'</span><h2>L’inspiration des astres</h2><p class="astro-quote">'+escapeHTML(a.text)+'</p>'+
 '<p class="muted">À lire comme une invitation à réfléchir.</p><div class="astro-attribution"><span>Source : </span><a class="text-link astro-source-link" target="_blank" rel="noopener noreferrer" href="'+link+'">Sigastra</a><a class="text-link" href="/astro-source.html">Horoscopes publics</a></div></div>'+
 '<div class="stack"><div class="card reflection-card"><div class="eyebrow">Réflexion du jour</div><h3>Un instant pour toi</h3><p class="daily-reflection">'+escapeHTML(reflection)+'</p></div><div class="card"><h3>Petit rituel</h3><p>Observe ta respiration et choisis une intention simple.</p><button class="primary" data-action="start-med" data-value="respirer">Prendre 5 minutes</button></div></div></div>';
}
function smallStats(){
 const h=profile().history,total=h.reduce((n,e)=>n+(e.duration||0),0);
 return '<div class="stats"><div class="stat"><strong>'+h.length+'</strong><span>séances</span></div><div class="stat"><strong>'+total+'</strong><span>minutes</span></div><div class="stat"><strong>'+new Set(h.map(x=>x.date)).size+'</strong><span>jours actifs</span></div></div>';
}
function profilePage(){
 const p=profile();
 return heading('Mon espace','Profil & progression','Retrouve tes séances et tes habitudes automatiquement sur tes appareils.')+
 '<div class="profile-layout"><div class="stack">'+Accounts.profilePanel()+
 '<section class="card"><div class="section-heading"><h2>Profils de pratique</h2><button class="small-btn" data-action="add-profile">+ Ajouter</button></div><div class="profile-options">'+state.profiles.map(x=>'<button class="profile-option '+(x.id===p.id?'active':'')+'" data-action="select-profile" data-value="'+escapeHTML(x.id)+'"><strong>'+escapeHTML(x.name)+'</strong><br><small>'+ (x.id===p.id?'Profil actuel':'Ouvrir ce profil')+'</small></button>').join('')+'</div><div class="field"><label for="profile-name">Nom du profil actuel</label><input id="profile-name" maxlength="50" value="'+escapeHTML(p.name)+'"></div><button class="secondary" data-action="save-name">Enregistrer le nom</button></section>'+
 '<section class="card"><h2>Mes préférences</h2><div class="field"><label>Univers graphique</label><div class="segment">'+[['linen','Lin & Sauge'],['horizon','Horizon & Sauge']].map(([id,name])=>'<button data-action="theme" data-value="'+id+'" aria-pressed="'+(p.theme===id)+'">'+name+'</button>').join('')+'</div></div><div class="field"><label for="zodiac">Signe astrologique (facultatif)</label><select id="zodiac"><option value="">Aucun</option>'+signs.map(s=>'<option value="'+s+'" '+(p.zodiac===s?'selected':'')+'>'+s+'</option>').join('')+'</select></div><p class="muted">Aucune date de naissance nécessaire.</p></section>'+
 '<section class="card"><h2>Mes données</h2><p>La synchronisation fonctionne automatiquement dès que la connexion est disponible. Tu peux conserver une copie personnelle de tes séances.</p><div class="session-controls"><button class="secondary" data-action="export">Exporter mes données</button><button class="secondary" data-action="import">Importer mes données</button><input type="file" id="import-json" accept="application/json,.json" hidden></div></section></div>'+
 '<div class="stack"><section class="card"><h2>Mes progrès</h2>'+smallStats()+'<h3>Historique</h3>'+(p.history.length?'<div class="history-list">'+p.history.slice().reverse().slice(0,15).map(x=>'<div>'+escapeHTML(x.date)+' · '+escapeHTML(x.name)+' <small>'+x.duration+' min</small></div>').join('')+'</div>':'<p class="muted">Ta première séance apparaîtra ici.</p>')+'</section>'+
 '<section class="card"><h2>Notifications</h2><p>Les rappels seront proposés une fois les horaires choisis et les autorisations activées.</p><button class="secondary" data-action="notifications">Mes notifications</button></section>'+(Accounts.user()?.role==='admin'?'<section class="card admin-entry"><div class="eyebrow">Espace administrateur</div><h2>Gestion des comptes</h2><p class="muted">Inscriptions, permissions et emails.</p><button class="primary" data-action="page" data-value="admin">Ouvrir l’administration</button></section>':'')+'</div></div>';
}
function poseModal(id){
 const p=yoga.poses.find(x=>x.id===id);if(!p)return;
 const guidance=poseGuidance.poses?.[id],image=yogaApiImage(id);
 modal='<div class="modal pose-modal" role="dialog" aria-modal="true" aria-label="Détail de posture">'+
 '<button class="icon-btn modal-close" data-action="close" aria-label="Fermer">×</button>'+
 '<div class="eyebrow">'+escapeHTML(p.niveau)+'</div><h2>'+escapeHTML(p.nom)+'</h2>'+
 '<p class="muted">'+escapeHTML(p.sanskrit)+'</p><div class="pose-modal-visual">'+posePicture(p.id,'large')+'</div>'+
 (image?'<p class="image-credit">Image : <a target="_blank" rel="noopener noreferrer" href="'+escapeHTML(image.source)+'">Yoga API</a> · crédits CC0 et Flaticon dans le Profil</p>':'<p class="image-credit">Pas d’illustration exacte identifiée dans Yoga API.</p>')+
 (guidance?'<div class="pose-pedagogy"><section><div class="eyebrow">1 · Préparation</div><p>'+escapeHTML(guidance.preparation)+'</p></section>'+
 '<section><div class="eyebrow">2 · Variante facile</div><p>'+escapeHTML(guidance.facile)+'</p></section>'+
 '<section><div class="eyebrow">3 · Posture complète</div><p>'+escapeHTML(p.instructions)+'</p></section>'+
 '<section><h3>Respiration</h3><p>'+escapeHTML(guidance.respiration)+'</p><h3>Alignement</h3><p>'+escapeHTML(guidance.alignement)+'</p></section></div>':
 '<h3>Installation</h3><p>'+escapeHTML(p.instructions)+'</p>')+
 '<h3>À respecter</h3><p class="attention">'+escapeHTML(guidance?.prudence||p.prudence||'Adapte la posture à ton confort.')+'</p></div>';
 renderModal();
}
function renderModal(){$('#overlay').innerHTML=modal;}
function closeModal(){modal='';renderModal();}
function sessionPage(){
 if(!session)return home();
 const i=stepIndex(session),step=session.steps[i],remaining=session.duration-session.elapsed,progress=Math.min(100,100*session.elapsed/session.duration);
 return '<div class="session"><div class="eyebrow">'+(session.type==='yoga'?'Yoga guidé':'Méditation guidée')+'</div><h1>'+escapeHTML(session.name)+'</h1><div class="session-stage"><span class="pill">Étape '+(i+1)+' sur '+session.steps.length+'</span><div class="session-clock" id="countdown">'+formatTime(remaining)+'</div>'+(step.imageId?'<div class="session-pose-image">'+posePicture(step.imageId,'session-photo')+'</div>':'')+'<h2>'+escapeHTML(step.title)+'</h2><p>'+escapeHTML(step.text)+'</p><div class="audio-panel"><p class="muted" id="audio-label" role="status">'+escapeHTML(voiceStatus||'Voix guidée disponible')+'</p><button class="secondary audio-replay" data-action="replay-voice" type="button">Écouter la consigne</button></div></div><div class="progress-track" aria-label="Progression"><span id="session-progress" style="width:'+progress+'%"></span></div><div class="session-controls"><button class="secondary" data-action="pause">'+(session.running?'Pause':'Reprendre')+'</button><button class="secondary" data-action="next-step">Étape suivante</button><button class="primary" data-action="finish">Terminer</button><button class="secondary" data-action="cancel-session">Quitter sans enregistrer</button></div><p class="muted">Si une posture provoque une douleur, interromps-la. Les consignes vocales ne remplacent pas l’écoute de ton corps.</p></div>';
}
function stepIndex(s){
 let elapsed=0;const total=s.steps.reduce((x,p)=>x+p.weight,0)||1;
 for(let i=0;i<s.steps.length;i++){elapsed+=s.duration*s.steps[i].weight/total;if(s.elapsed<elapsed)return i;}
 return s.steps.length-1;
}
function render(){
 if(!Accounts.loggedIn() || Accounts.mustChangePassword()){
  document.documentElement.dataset.theme='linen';
  $('#sidebar').innerHTML='';$('#bottomnav').innerHTML='';$('#topbar').innerHTML='';
  $('#main').innerHTML=Accounts.loggedIn()?Accounts.passwordScreen():Accounts.screen();
  renderModal();return;
 }
 document.documentElement.dataset.theme=profile().theme==='horizon'?'horizon':'linen';
 renderShell();
 const html=session?sessionPage():page==='home'?home():page==='yoga'?yogaPage():page==='meditate'?meditationPage():page==='astro'?astroPage():page==='admin'&&Accounts.user()?.role==='admin'?Accounts.adminScreen():profilePage();
 $('#main').innerHTML=html;renderModal();
}
function findRoutine(id){return yoga.routines.find(x=>x.id===id);}
function startSession(type,id){
 if(session)return notice('Termine ou quitte la séance actuelle.');
 let steps=[],duration=0,name='';
 if(type==='yoga'){
   const r=findRoutine(id);if(!r)return;name=r.name;duration=r.duration*60;
   const mode=practiceMode();
   for(const poseId of r.poseIds){
    const p=yoga.poses.find(x=>x.id===poseId),guidance=poseGuidance.poses?.[poseId];
    if(guidance&&mode!=='complete'){
      steps.push({title:(p?.nom||poseId)+' · se préparer',text:guidance.preparation,weight:.20,clip:'prepare_'+poseId,imageId:poseId,phase:'preparation'});
      steps.push({title:(p?.nom||poseId)+' · version douce',text:guidance.facile,weight:.35,clip:'easy_'+poseId,imageId:poseId,phase:'facile'});
    }
    if(mode!=='douce'||!guidance){
      steps.push({title:p?.nom||poseId,text:p?.instructions||'',weight:1,clip:'pose_'+poseId,imageId:poseId,phase:'finale'});
    }
   }
 }else{
  const med=meditations.sessions.find(x=>x.id===id);if(!med)return;name=med.name;duration=med.minutes*60;
  steps=(med.scripts[profile().meditationStyle]||[]).map((x,i)=>({title:i===0?'S’installer':i===med.scripts[profile().meditationStyle].length-1?'Revenir': 'Prendre le temps',text:x.text,weight:Math.max(1,Number(x.pause)||1),clip:med.id+'_'+profile().meditationStyle+'_'+String(i).padStart(2,'0')}));
 }
 if(!steps.length)return notice('Cette séance n’a pas de contenu.');
 session={id,type,name,duration,elapsed:0,running:true,last:Date.now(),steps,spoken:-1};
 page=type==='yoga'?'yoga':'meditate';render();
 announceStep();clearInterval(timer);timer=setInterval(tick,300);
}
let voicePlayId=0;
function stopAudio(){
 ++voicePlayId;
 if(audio){audio.pause();audio.removeAttribute('src');audio.load();}
}
async function voiceManifest(){
 if(manifest)return manifest;
 for(const path of ['/voice/vivienne-fr-v2/manifest.json','/voice/vivienne-fr-v1/manifest.json']){
  const res=await fetch(path,{cache:'no-store'});
  if(!res.ok)continue;
  const obj=await res.json();
  if(obj.format==='sichosana-voice-pack'&&obj.voiceId==='fr-FR-VivienneMultilingualNeural'){manifest=obj;return obj;}
 }
 throw Error('Le pack vocal ne semble pas installé.');
}
function playReadyClip(clip,pack){
 const record=pack.files?.[clip];
 if(!record)throw Error('Cette consigne est absente du pack audio.');
 const playId=++voicePlayId;
 if(!audio){audio=document.createElement('audio');audio.preload='auto';audio.setAttribute('playsinline','');}
 audio.pause();
 audio.src='/voice/'+encodeURIComponent(pack.packId)+'/'+encodeURIComponent(record.src);
 audio.volume=.94;
 audio.playbackRate=pack.packId==='vivienne-fr-v2'?1:(session?.type==='meditate'?.76:.88);
 audio.preservesPitch=true;
 if('webkitPreservesPitch' in audio)audio.webkitPreservesPitch=true;
 voiceStatus='Lecture de la consigne…';
 if($('#audio-label'))$('#audio-label').textContent=voiceStatus;
 const promise=audio.play();
 if(promise?.then)promise.then(()=>{
  if(playId!==voicePlayId)return;
  voiceStatus='Voix guidée active';
  if($('#audio-label'))$('#audio-label').textContent=voiceStatus;
 }).catch(err=>{
  if(playId!==voicePlayId)return;
  voiceStatus=err?.name==='NotAllowedError'
   ?'Appuie sur « Écouter la consigne » pour autoriser la lecture.'
   :err?.name==='NotSupportedError'
   ?'Ce format audio n’est pas pris en charge par ce navigateur.'
   :'Audio inaccessible : vérifier le fichier ou la connexion.';
  if($('#audio-label'))$('#audio-label').textContent=voiceStatus;
 });
}
function playVoice(clip){
 if(!session)return;
 // Safari iOS exige que play() soit appelé directement dans le geste de l'utilisateur.
 // La V2 produit un MP3 nommé exactement comme l'identifiant de la consigne.
 const pack=manifest?.files?.[clip]?manifest:{packId:'vivienne-fr-v2',files:{[clip]:{src:clip+'.mp3'}}};
 try{playReadyClip(clip,pack);}
 catch(err){
  voiceStatus='Impossible de lancer la voix. Appuie sur « Écouter la consigne ».';
  if($('#audio-label'))$('#audio-label').textContent=voiceStatus;
 }
 // Le contrôle du manifeste se fait en parallèle, et ne retarde jamais play().
 if(!manifest)voiceManifest().catch(()=>{});
}
function announceStep(){
 if(!session)return;const index=stepIndex(session);
 if(index===session.spoken)return;session.spoken=index;
 playVoice(session.steps[index].clip);
 const main=$('#main');if(main)main.innerHTML=sessionPage();
}
function tick(){
 if(!session)return;
 const now=Date.now();if(session.running){session.elapsed+=(now-session.last)/1000;}
 session.last=now;
 if(session.elapsed>=session.duration){finishSession(true);return;}
 if(stepIndex(session)!==session.spoken){announceStep();return;}
 const clock=$('#countdown'),bar=$('#session-progress');
 if(clock)clock.textContent=formatTime(session.duration-session.elapsed);
 if(bar)bar.style.width=Math.min(100,100*session.elapsed/session.duration)+'%';
}
function stepBoundary(s,idx){
 const total=s.steps.reduce((n,x)=>n+x.weight,0)||1;
 return s.duration*s.steps.slice(0,idx+1).reduce((n,x)=>n+x.weight,0)/total;
}
async function finishSession(automatic=false){
 if(!session)return;
 const s=session;session=null;clearInterval(timer);timer=null;stopAudio();
 const p=profile(),elapsed=automatic?s.duration:s.elapsed;
 p.history.push({id:uid(),type:s.type,ref:s.id,name:s.name,date:todayKey(),duration:Math.max(1,Math.round(elapsed/60)),completed:automatic||elapsed>=s.duration*.85,at:Date.now()});
 touch();render();notice('Séance enregistrée. Merci pour ce moment.');
}
function abortSession(){session=null;clearInterval(timer);timer=null;stopAudio();render();}
function mergedProfiles(local,remote){
 const map=new Map();
 for(const p of [...remote,...local]){
  const old=map.get(p.id);if(!old){map.set(p.id,p);continue;}
  const newer=(p.modifiedAt||0)>=(old.modifiedAt||0)?p:old;
  const history=new Map([...(old.history||[]),...(p.history||[])].map(x=>[x.id,x]));
  map.set(p.id,{...newer,history:[...history.values()].sort((a,b)=>(a.at||0)-(b.at||0)),favorites:[...new Set([...(old.favorites||[]),...(p.favorites||[])])]});
 }
 return [...map.values()];
}
function snapshot(){return {schemaVersion:1,profiles:state.profiles,activeProfileId:state.activeProfileId,exportedAt:new Date().toISOString()};}
function ingest(data,remote=false){
 if(!data||data.schemaVersion!==1||!Array.isArray(data.profiles)||data.profiles.length>100)throw Error('Fichier de sauvegarde non reconnu.');
 const fresh=data.profiles.filter(x=>x&&typeof x.id==='string'&&typeof x.name==='string'&&Array.isArray(x.history)).map(x=>({...x,name:x.name.slice(0,50),theme:x.theme==='horizon'?'horizon':'linen',favorites:Array.isArray(x.favorites)?x.favorites.slice(0,200):[],meditationStyle:['discrete','equilibree','enveloppante'].includes(x.meditationStyle)?x.meditationStyle:'equilibree',history:x.history.slice(-2000)}));
 if(!fresh.length)throw Error('Aucun profil valide.');
 if(remote&&state.profiles.length===1&&state.profiles[0].name==='Mon espace'&&!state.profiles[0].history.length){state.profiles=fresh;state.activeProfileId=fresh[0].id;}
 else{state.profiles=mergedProfiles(state.profiles,fresh);if(!state.profiles.some(p=>p.id===state.activeProfileId))state.activeProfileId=state.profiles[0].id;}
 save();render();
}
/* Synchronisation native : aucun jumelage, code NAS ou bouton manuel. */
function scheduleAutoSync(){
 if(!Accounts.loggedIn()||Accounts.mustChangePassword())return;
 clearTimeout(syncTimer);
 syncTimer=setTimeout(()=>autoSync(false),1200);
}
async function pullSync(){
 const remote=await Accounts.api('account/snapshot');
 if(remote.data)ingest(remote.data,true);
 state.revision=remote.revision;
 await save(false);
}
async function pushSync(){
 if(!Accounts.loggedIn()||Accounts.mustChangePassword())return;
 try{
  const out=await Accounts.api('account/snapshot',{method:'PUT',headers:{'If-Match':String(state.revision||0)},body:JSON.stringify({data:snapshot()})});
  state.revision=out.revision;await save(false);
 }catch(error){
  if(error.status!==409)throw error;
  if(error.data?.data)ingest(error.data.data,true);
  state.revision=error.data.revision;await save(false);
  const retry=await Accounts.api('account/snapshot',{method:'PUT',headers:{'If-Match':String(state.revision)},body:JSON.stringify({data:snapshot()})});
  state.revision=retry.revision;await save(false);
 }
}
async function autoSync(pullFirst=true){
 if(syncBusy||!navigator.onLine||!Accounts.loggedIn()||Accounts.mustChangePassword()||!state)return;
 syncBusy=true;
 try{
  if(pullFirst)await pullSync();
  await pushSync();
  syncStatus='';
 }catch(error){syncStatus=error.message;}
 finally{syncBusy=false;}
}
async function cacheVoicePack(){
 try{
  if(!('caches' in window))throw Error('Cache non disponible.');
  const m=await voiceManifest(),cache=await caches.open('sichosana-vivienne-'+m.packId),items=Object.values(m.files);
  let done=0;voiceStatus='Téléchargement : 0 / '+items.length;render();
  for(const x of items){
   const url='/voice/'+encodeURIComponent(m.packId)+'/'+encodeURIComponent(x.src);
   if(!await cache.match(url)){const r=await fetch(url);if(!r.ok)throw Error('Fichier absent : '+x.src);await cache.put(url,r.clone());}
   done++;voiceStatus='Téléchargement : '+done+' / '+items.length;
   const e=$('#voice-status');if(e)e.textContent=voiceStatus;
  }
  const mr=await fetch('/voice/'+encodeURIComponent(m.packId)+'/manifest.json');if(mr.ok)await cache.put('/voice/'+encodeURIComponent(m.packId)+'/manifest.json',mr);
  voiceStatus=done+' fichiers audio disponibles hors ligne.';render();notice('Pack vocal installé.');
 }catch(err){voiceStatus='Téléchargement hors ligne bloqué par Safari. Les consignes restent accessibles en ligne ; réessaie depuis l’écran d’accueil ou un autre navigateur.';render();notice('Téléchargement audio non autorisé sur cet appareil.');}
}
async function exportData(){
 const blob=new Blob([JSON.stringify(snapshot(),null,2)],{type:'application/json'});
 const link=document.createElement('a'),url=URL.createObjectURL(blob);
 link.href=url;link.download='SichoSana-sauvegarde-'+todayKey()+'.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),3000);
}
function notifications(){
 const supported='Notification' in window && 'serviceWorker' in navigator&& 'PushManager' in window;
 modal='<div class="modal" role="dialog" aria-modal="true"><button class="icon-btn modal-close" data-action="close">×</button><h2>Notifications</h2><p>'+ (supported?'Le navigateur est compatible avec les notifications web push.':'Cet appareil ou navigateur ne propose pas toutes les fonctions web push.')+'</p><p>Les horaires et clés VAPID ne sont pas encore configurés. Aucun rappel n’est activé automatiquement.</p><button class="secondary" data-action="close">Compris</button></div>';renderModal();
}
async function handle(action,value){
 if(action==='page'){if(session)abortSession();page=value;render();if(page==='admin')await Accounts.refreshAdmin();if(page==='astro')refreshAstrology();window.scrollTo(0,0);return;}
 if(action==='routine-filter'){routineFilter=value;render();return;}
 if(action==='pose-filter'){poseFilter=value;render();return;}
 if(action==='med-filter'){meditationFilter=value;render();return;}
 if(action==='med-level'){profile().meditationStyle=value;touch();render();return;}
 if(action==='theme'){profile().theme=value;touch();render();return;}
 if(action==='select-program'){profile().selectedProgram=value;touch();render();return;}
 if(action==='favorite'){const list=profile().favorites;profile().favorites=list.includes(value)?list.filter(x=>x!==value):[...list,value];touch();render();return;}
 if(action==='start-yoga')return startSession('yoga',value);
 if(action==='start-med')return startSession('meditate',value);
 if(action==='pose')return poseModal(value);
 if(action==='close')return closeModal();
 if(action==='pause'){if(session){session.running=!session.running;session.last=Date.now();if(!session.running)stopAudio();else session.spoken=-1;render();if(session.running)announceStep();}return;}
 if(action==='next-step'){if(session){const idx=stepIndex(session);session.elapsed=Math.min(session.duration,stepBoundary(session,idx)+0.01);session.spoken=-1;tick();}return;}
 if(action==='finish')return finishSession(false);
 if(action==='cancel-session')return abortSession();
 if(action==='add-profile'){const name=prompt('Nom du nouveau profil :');if(name&&name.trim()){const p=defaultProfile();p.name=name.trim().slice(0,50);state.profiles.push(p);state.activeProfileId=p.id;save();render();}return;}
 if(action==='select-profile'){state.activeProfileId=value;save();render();return;}
 if(action==='save-name'){profile().name=($('#profile-name')?.value||'Mon espace').trim().slice(0,50)||'Mon espace';touch();render();return;}
 if(action==='export')return exportData();
 if(action==='import')return $('#import-json')?.click();
 if(action==='cache-voice')return cacheVoicePack();
 if(action==='astro-period'){astroPeriod=value;astrologyLive=null;render();refreshAstrology();return;}
 if(action==='replay-voice'){if(session)return playVoice(session.steps[stepIndex(session)].clip);return;}
 if(action==='notifications')return notifications();
}
document.addEventListener('click',(e)=>{
 const accountButton=e.target.closest('[data-account]');
 if(accountButton){e.preventDefault();Promise.resolve(Accounts.onAction(accountButton.dataset.account,accountButton)).catch(err=>notice(err.message));return;}
 const target=e.target.closest('[data-action]');if(!target)return;e.preventDefault();
 Promise.resolve(handle(target.dataset.action,target.dataset.value||'')).catch(err=>notice(err.message));
});
document.addEventListener('submit',(e)=>{
 const form=e.target.closest('form[data-account-form]');if(!form)return;
 e.preventDefault();Accounts.onSubmit(form).catch(err=>notice(err.message));
});
document.addEventListener('change',async(e)=>{
 if(e.target.id==='zodiac'||e.target.id==='astro-sign'){profile().zodiac=e.target.value;astrologyLive=null;touch();render();refreshAstrology();}
 if(e.target.id==='import-json'){
  const file=e.target.files?.[0];if(!file)return;
  try{if(file.size>2_000_000)throw Error('Fichier trop volumineux.');ingest(JSON.parse(await file.text()));notice('Sauvegarde importée et fusionnée.');}catch(err){notice('Import impossible : '+err.message);}
 }
});
window.addEventListener('online',()=>{render();autoSync(true);});
window.addEventListener('offline',render);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)autoSync(true);});
async function init(){
 try{
  db=await openDB();
  Accounts.configure({
   read:dbRead,write:dbWrite,render,notice,
   enter:async user=>{
    state=await dbRead('account:'+user.id)||initialState();
    if(!state.profiles?.length)state=initialState();
    page='home';render();
    if(!user.mustChangePassword){await autoSync(true);refreshAstrology();}
   },
   welcome:async user=>{
    const key='welcome:'+user.id;
    if(await dbRead(key))return;
    await dbWrite(key,true);
    modal='<div class="modal welcome-modal" role="dialog" aria-modal="true" aria-label="Bienvenue dans SichoSana">'+
     '<button class="icon-btn modal-close" data-action="close" aria-label="Fermer">×</button>'+
     '<div class="eyebrow">Bienvenue dans ton espace</div>'+
     '<h2>Un instant rien qu’à toi</h2><p>Bienvenue, '+escapeHTML(user.pseudo)+'.</p>'+
     '<p>Ici, chaque respiration ouvre un espace pour ralentir, te retrouver et t’offrir un instant rien qu’à toi.</p>'+
     '<p>Prends le temps d’explorer, d’écouter ton corps et de cultiver ton propre rythme.</p>'+
     '<p class="welcome-signature">Avec douceur,<br>L’équipe de SichoSana</p>'+
     '<button class="primary" data-action="close">Découvrir mon espace</button></div>';
    renderModal();
   },
   exit:async()=>{clearTimeout(syncTimer);if(session)abortSession();state=null;page='home';}
  });
  const data=await Promise.all([fetch('/data/yoga.json').then(r=>{if(!r.ok)throw Error('Yoga indisponible');return r.json();}),fetch('/data/meditations.json').then(r=>{if(!r.ok)throw Error('Méditations indisponibles');return r.json();}),fetch('/data/programs.json').then(r=>{if(!r.ok)throw Error('Programmes indisponibles');return r.json();})]);
  yoga=data[0];meditations=data[1];programs=data[2];
  try{const q=await fetch('/data/pose-media.json');if(q.ok){const d=await q.json();if(Array.isArray(d.photos))poseMedia=d;}}catch(e){}
  try{const q=await fetch('/data/reflections.json');if(q.ok){const v=await q.json();if(Array.isArray(v.reflections)&&v.reflections.length>=400)reflections=v;}}catch(e){}
  try{const frozen=await fetch('/data/yoga-api-library.json');if(frozen.ok){const items=(await frozen.json()).poses||[];const ids=new Set(yoga.poses.map(p=>p.id));yoga.poses.push(...items.filter(p=>!ids.has(p.id)));}}catch(err){} // catalogue local, accessible même sans serveur
  try{const r=await fetch('/api/v1/poses');if(r.ok){const extra=(await r.json()).poses||[];const ids=new Set(yoga.poses.map(p=>p.id));yoga.poses.push(...extra.filter(p=>!ids.has(p.id)));}}catch(err){} // bibliothèque préchargée disponible hors réseau
  voiceManifest().catch(()=>{});
   await Accounts.resume();
  render();
  if('serviceWorker' in navigator)navigator.serviceWorker.register('/sw.js').catch(()=>{});
 }catch(err){$('#main').innerHTML='<div class="attention"><h2>Initialisation impossible</h2><p>'+escapeHTML(err.message)+'</p><p>Vérifie la connexion initiale et le stockage de ton appareil.</p></div>';}
}
init();
