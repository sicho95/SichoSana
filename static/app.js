/* SichoSana — PWA locale, écrans adaptés iPhone/iPad/ordinateur.
   Conserver la charte graphique dans styles.css et l'identité Vivienne ResurGo. */
'use strict';
const $ = (s) => document.querySelector(s);
const escapeHTML = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const uid = () => (crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + Math.random().toString(36).slice(2));
const formatTime = (n) => { const s = Math.max(0, Math.ceil(n)); return Math.floor(s/60).toString().padStart(2,'0')+':'+(s%60).toString().padStart(2,'0'); };
const todayKey = () => { const d = new Date(); return [d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-'); };
const logo = '<svg viewBox="0 0 64 64" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M32 49c-2-10-14-16-14-24 9 1 14 6 14 12 0-6 5-11 14-12 0 8-12 14-14 24Z"/><path d="M32 37C20 34 16 21 22 13c6 4 10 10 10 18 0-8 4-14 10-18 6 8 2 21-10 24Z"/><path d="M11 42c9 1 15 7 21 7s12-6 21-7M17 52h30"/></svg>';
const nav = [{id:'home',text:'Accueil',glyph:'⌂'},{id:'yoga',text:'Yoga',glyph:'◈'},{id:'meditate',text:'Méditer',glyph:'☼'},{id:'astro',text:'Astro',glyph:'☾'},{id:'profile',text:'Profil',glyph:'♙'}];
const signs = ['Bélier','Taureau','Gémeaux','Cancer','Lion','Vierge','Balance','Scorpion','Sagittaire','Capricorne','Verseau','Poissons'];
const inspirations = [
  'Accorde-toi une pause pour retrouver ton rythme.',
  'La simplicité peut être une façon de prendre soin de toi.',
  'Un petit geste de douceur peut changer la couleur du jour.',
  'Observe ce que tu ressens, sans chercher à le transformer.',
  'Écoute tes besoins et laisse une place au calme.',
  'Prends un instant pour te reconnecter à l’essentiel.',
  'La patience est aussi une forme de mouvement.',
  'Laisse respirer tes idées avant de décider.'
];
const defaultProfile = () => ({id:uid(),name:'Mon espace',theme:'linen',meditationStyle:'equilibree',zodiac:'',favorites:[],history:[],createdAt:Date.now(),modifiedAt:Date.now()});
const initialState = () => { const p=defaultProfile(); return {schemaVersion:1,profiles:[p],activeProfileId:p.id,revision:0,credentials:null}; };
let db, state, yoga={poses:[],routines:[]}, meditations={sessions:[]}, page='home', routineFilter='Tous', poseFilter='Tous', meditationFilter='Toutes', modal='', session=null, timer=null, audio=null, manifest=null, voiceStatus='', syncBusy=false, conflict=null;
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
async function save(){try{await dbWrite('app',state);}catch(err){notice('Sauvegarde locale impossible : '+err.message);}}
function touch(){profile().modifiedAt=Date.now();save();}
function notice(text){const e=$('#toast');e.textContent=text;e.classList.add('show');clearTimeout(notice.timeout);notice.timeout=setTimeout(()=>e.classList.remove('show'),4000);}
function brand(){return '<div class="brand">'+logo+'<span>Sicho<span>Sana</span></span></div>';}
function navButton(item){return '<button type="button" class="nav-link" data-action="page" data-value="'+item.id+'" '+(page===item.id?'aria-current="page"':'')+'><span class="nav-glyph">'+item.glyph+'</span><span>'+item.text+'</span></button>';}
function renderShell(){
 $('#sidebar').innerHTML=brand()+'<nav>'+nav.map(navButton).join('')+'</nav><p class="sidebar-tag">Un moment pour soi,<br>à son rythme.</p>';
 $('#bottomnav').innerHTML=nav.map(navButton).join('');
 $('#topbar').innerHTML='<div class="desktop-brand">'+brand()+'</div><div class="top-actions"><span class="connection-pill">'+(navigator.onLine?'● En ligne':'○ Hors ligne')+'</span><button class="icon-btn" type="button" data-action="notifications" aria-label="Notifications">♧</button><button class="profile-chip" type="button" data-action="page" data-value="profile"><span class="dot"></span>'+escapeHTML(profile().name)+'</button></div>';
}
function heading(kicker,title,subtitle){return '<div class="page-heading"><div><div class="eyebrow">'+kicker+'</div><h1>'+title+'</h1>'+(subtitle?'<p class="subtitle">'+subtitle+'</p>':'')+'</div></div>';}
function routineCard(r){
 const fav=profile().favorites.includes(r.id);
 return '<article class="card routine-card"><div class="routine-visual"><span aria-hidden="true">◈</span></div><div class="routine-body"><div class="eyebrow">'+escapeHTML(r.family)+'</div><h3>'+escapeHTML(r.name)+'</h3><p>'+escapeHTML(r.subtitle)+'</p><div class="meta"><span>'+r.duration+' min</span><span>'+escapeHTML(r.level)+'</span><span>'+r.poseIds.length+' postures</span></div><div class="routine-footer"><button class="primary" type="button" data-action="start-yoga" data-value="'+escapeHTML(r.id)+'">Commencer</button><button class="small-btn" type="button" data-action="favorite" data-value="'+escapeHTML(r.id)+'" aria-label="'+(fav?'Retirer des favoris':'Ajouter aux favoris')+'">'+(fav?'♥':'♡')+'</button></div></div></article>';
}
function weeklyStats(){
 const now=new Date();const start=new Date(now);start.setDate(now.getDate()-((now.getDay()+6)%7));start.setHours(0,0,0,0);
 const dates=Array.from({length:7},(_,i)=>{const d=new Date(start);d.setDate(start.getDate()+i);return d.toISOString().slice(0,10);});
 const done=new Set(profile().history.map(h=>h.date));
 return '<div class="week-dots" aria-label="Pratique cette semaine">'+dates.map((d,i)=>'<span class="'+(done.has(d)?'done':'')+'" title="'+d+'">'+['L','M','M','J','V','S','D'][i]+'</span>').join('')+'</div>';
}
function localAstro(){
 const sign=profile().zodiac;if(!sign)return {text:'Choisis ton signe dans Profil pour afficher ton inspiration quotidienne.',sign:'Non configuré'};
 const seed=(todayKey()+sign).split('').reduce((n,c)=>(n*31+c.charCodeAt(0))%100003,7);
 return {text:inspirations[seed%inspirations.length],sign};
}
function home(){
 const r=yoga.routines[0],astro=localAstro(),n=profile().history.filter(x=>x.date===todayKey()).length;
 return heading('Bienvenue','Un moment pour soi','Du mouvement, de la douceur et un peu de temps pour toi.')+
 '<div class="home-desktop-layout"><div class="home-main"><section class="hero"><div class="hero-content"><span class="pill">✧ Séance du jour</span><h2>'+escapeHTML(r.name)+'</h2><p>'+escapeHTML(r.subtitle)+'</p><div class="meta"><span>'+r.duration+' min</span><span>'+escapeHTML(r.level)+'</span></div><button class="primary" type="button" data-action="start-yoga" data-value="'+r.id+'">▷ Commencer ma séance</button></div><div class="hero-art" aria-hidden="true">'+logo+'</div></section>'+
 '<div class="wellness-row"><article class="tile"><div class="tile-icon">☼</div><h3>Méditation guidée</h3><p>Une parenthèse calme, avec la voix Vivienne et le niveau de guidage de ton choix.</p><button class="text-link" data-action="page" data-value="meditate">Découvrir les séances ›</button></article><article class="tile"><div class="tile-icon">☾</div><h3>Astro du jour</h3><p>'+escapeHTML(astro.text)+'</p><button class="text-link" data-action="page" data-value="astro">Mon inspiration ›</button></article></div>'+
 '<div class="section-heading"><h2>Explorer le yoga</h2><button class="text-link" data-action="page" data-value="yoga">Toutes les séances ›</button></div><div class="cards">'+yoga.routines.slice(1,4).map(routineCard).join('')+'</div></div>'+
 '<aside class="home-aside"><div class="card"><div class="eyebrow">Rituel de la semaine</div><h3>7 jours de présence</h3><p class="muted">La régularité se construit sans pression.</p>'+weeklyStats()+'<p class="muted">'+n+' séance'+(n>1?'s':'')+' terminée'+(n>1?'s':'')+' aujourd’hui.</p></div>'+
 '<div class="card"><div class="eyebrow">Ta progression</div>'+smallStats()+'<button class="text-link" data-action="page" data-value="profile">Voir mon suivi ›</button></div></aside></div>';
}
function pills(opts,active,action){return '<div class="filter-bar">'+opts.map(x=>'<button class="filter" type="button" data-action="'+action+'" data-value="'+escapeHTML(x)+'" aria-pressed="'+(x===active)+'">'+escapeHTML(x)+'</button>').join('')+'</div>';}
function yogaPage(){
 const routines=yoga.routines.filter(r=>routineFilter==='Tous'||r.family===routineFilter||(routineFilter==='Favoris'&&profile().favorites.includes(r.id)));
 const poses=yoga.poses.filter(p=>poseFilter==='Tous'||p.niveau===poseFilter);
 return heading('Pratiquer','Yoga','Choisis une séance à ton rythme, sans chercher la performance.')+
 '<div class="section-heading"><h2>Les enchaînements</h2></div>'+pills(['Tous','Hatha','Vinyasa','Favoris'],routineFilter,'routine-filter')+
 '<div class="cards">'+(routines.length?routines.map(routineCard).join(''):'<p class="empty">Aucune séance pour ce filtre.</p>')+'</div>'+
 '<div class="section-heading"><h2>Bibliothèque des postures</h2><span class="muted">'+yoga.poses.length+' postures</span></div>'+
 pills(['Tous','Débutant','Intermédiaire'],poseFilter,'pose-filter')+
 '<div class="pose-list">'+poses.map(p=>'<button class="pose-item" type="button" data-action="pose" data-value="'+escapeHTML(p.id)+'"><span class="pose-icon">◈</span><span><strong>'+escapeHTML(p.nom)+'</strong><small>'+escapeHTML(p.sanskrit)+' · '+escapeHTML(p.focus)+'</small></span></button>').join('')+'</div>'+
 '<p class="library-info">Postures disponibles localement. Bibliothèque enrichissable par import Yoga API, sans requête externe pendant la pratique. Adapte toute posture à ton confort.</p>';
}
function medCard(m){return '<article class="card routine-card"><div class="routine-visual">☼</div><div class="routine-body"><div class="eyebrow">'+escapeHTML(m.category)+'</div><h3>'+escapeHTML(m.name)+'</h3><p>'+escapeHTML(m.description)+'</p><div class="meta"><span>'+m.minutes+' min</span><span>Vivienne · FR</span></div><button class="primary" data-action="start-med" data-value="'+escapeHTML(m.id)+'">Méditer</button></div></article>';}
function meditationPage(){
 const opts=['Toutes',...new Set(meditations.sessions.map(m=>m.category))];
 const subset=meditations.sessions.filter(m=>meditationFilter==='Toutes'||m.category===meditationFilter);
 return heading('Ralentir','Méditation','Silence, présence et paroles à la juste mesure.')+
 '<div class="card meditation-intro"><div><div class="eyebrow">Voix de la coach Running ResurGo</div><h3>Vivienne, un peu plus douce et plus lente</h3><p>Fichiers audio pré-générés. Identité vocale conservée ; si les fichiers ne sont pas encore installés, l’audio est annoncé indisponible.</p></div><button class="secondary" data-action="cache-voice">Télécharger les audios pour le hors ligne</button><small id="voice-status">'+escapeHTML(voiceStatus)+'</small></div>'+
 '<div class="section-heading"><h2>Intensité du guidage</h2></div>'+
 '<div class="segment meditation-levels">'+[['discrete','Discrète'],['equilibree','Équilibrée'],['enveloppante','Enveloppante']].map(([id,t])=>'<button data-action="med-level" data-value="'+id+'" aria-pressed="'+(profile().meditationStyle===id)+'">'+t+'</button>').join('')+'</div><p class="muted">Discrète : longs silences · Équilibrée : quelques repères · Enveloppante : accompagnement plus présent.</p>'+
 '<div class="section-heading"><h2>Choisir un moment</h2></div>'+pills(opts,meditationFilter,'med-filter')+
 '<div class="cards">'+subset.map(medCard).join('')+'</div>';
}
function astroPage(){
 const a=localAstro();
 return heading('Saison intérieure','Astrologie du jour','Un espace poétique de réflexion, sans prédiction présentée comme un fait.')+
 '<div class="astro-layout"><div class="card astrology-card"><div class="celestial-icon">☾</div><span class="pill">'+escapeHTML(a.sign)+' · '+new Intl.DateTimeFormat('fr-FR',{dateStyle:'long'}).format(new Date())+'</span><h2>Une pensée pour aujourd’hui</h2><p class="astro-quote">« '+escapeHTML(a.text)+' »</p><p class="muted">Inspiration symbolique générée localement à partir du jour et du signe. Aucun calcul de position planétaire ni horoscope d’une source externe n’est revendiqué.</p><button class="secondary" data-action="page" data-value="profile">Personnaliser mon signe</button></div><div class="card"><h3>Petit rituel</h3><p>Ferme les yeux quelques instants. Observe ta respiration, puis choisis une intention simple pour aujourd’hui.</p><button class="primary" data-action="start-med" data-value="respirer">Prendre 5 minutes</button></div></div>';
}
function smallStats(){
 const h=profile().history,total=h.reduce((n,e)=>n+(e.duration||0),0);
 return '<div class="stats"><div class="stat"><strong>'+h.length+'</strong><span>séances</span></div><div class="stat"><strong>'+total+'</strong><span>minutes</span></div><div class="stat"><strong>'+new Set(h.map(x=>x.date)).size+'</strong><span>jours actifs</span></div></div>';
}
function profilePage(){
 const p=profile(),connected=!!state.credentials;
 return heading('Mon espace','Profil & progression','Tes habitudes et tes données restent d’abord sur cet appareil.')+
 '<div class="profile-layout"><div class="stack"><section class="card"><div class="section-heading"><h2>Profils</h2><button class="small-btn" data-action="add-profile">+ Ajouter</button></div><div class="profile-options">'+state.profiles.map(x=>'<button class="profile-option '+(x.id===p.id?'active':'')+'" data-action="select-profile" data-value="'+escapeHTML(x.id)+'"><strong>'+escapeHTML(x.name)+'</strong><br><small>'+ (x.id===p.id?'Profil actuel':'Ouvrir ce profil')+'</small></button>').join('')+'</div><div class="field"><label for="profile-name">Nom du profil actuel</label><input id="profile-name" maxlength="50" value="'+escapeHTML(p.name)+'"></div><button class="secondary" data-action="save-name">Enregistrer le nom</button></section>'+
 '<section class="card"><h2>Mes préférences</h2><div class="field"><label>Univers graphique</label><div class="segment">'+[['linen','Lin & Sauge'],['horizon','Horizon & Sauge']].map(([id,name])=>'<button data-action="theme" data-value="'+id+'" aria-pressed="'+(p.theme===id)+'">'+name+'</button>').join('')+'</div></div><div class="field"><label for="zodiac">Signe astrologique (facultatif)</label><select id="zodiac"><option value="">Aucun</option>'+signs.map(s=>'<option value="'+s+'" '+(p.zodiac===s?'selected':'')+'>'+s+'</option>').join('')+'</select></div><p class="muted">Aucune date de naissance nécessaire.</p></section>'+
 '<section class="card"><h2>Sauvegarde locale</h2><p>Export JSON complet de tous les profils et de leur progression. Les codes et jetons d’accès ne sont jamais inclus dans l’export.</p><div class="session-controls"><button class="secondary" data-action="export">Exporter JSON</button><button class="secondary" data-action="import">Importer JSON</button><input type="file" id="import-json" accept="application/json,.json" hidden></div></section></div>'+
 '<div class="stack"><section class="card"><h2>Mes progrès</h2>'+smallStats()+'<h3>Historique</h3>'+(p.history.length?'<div class="history-list">'+p.history.slice().reverse().slice(0,15).map(x=>'<div>'+escapeHTML(x.date)+' · '+escapeHTML(x.name)+' <small>'+x.duration+' min</small></div>').join('')+'</div>':'<p class="muted">Ta première séance apparaîtra ici.</p>')+'</section>'+
 '<section class="card"><h2>Synchronisation NAS</h2><p>Association par code et mot de passe. Le serveur SQLite permet de retrouver tous les profils sur tes appareils. Aucun effacement silencieux en cas de conflit.</p>'+
 (connected?'<p class="pill">Association présente sur cet appareil</p><div class="session-controls"><button class="primary" data-action="sync">Synchroniser maintenant</button><button class="secondary" data-action="sync-pull">Récupérer les données</button><button class="secondary" data-action="disconnect">Dissocier cet appareil</button></div>':
 '<div class="field"><label for="sync-code">Code d’association (vide pour créer)</label><input id="sync-code" autocapitalize="off" autocomplete="off" placeholder="Code si autre appareil"></div><div class="field"><label for="sync-password">Mot de passe (au moins 12 caractères)</label><input id="sync-password" type="password" autocomplete="new-password"></div><button class="primary" data-action="pair">Créer / associer</button>')+
 '<p id="sync-status" class="muted">'+(syncBusy?'Synchronisation en cours…':'')+'</p></section>'+
 '<section class="card"><h2>Notifications</h2><p>Les rappels web push restent désactivés jusqu’à ton choix d’horaires et la configuration des clés du serveur. Aucune notification imposée.</p><button class="secondary" data-action="notifications">État des notifications</button></section></div></div>';
}
function poseModal(id){
 const p=yoga.poses.find(x=>x.id===id);if(!p)return;
 modal='<div class="modal" role="dialog" aria-modal="true" aria-label="Détail de posture"><button class="icon-btn modal-close" data-action="close" aria-label="Fermer">×</button><div class="eyebrow">'+escapeHTML(p.niveau)+'</div><h2>'+escapeHTML(p.nom)+'</h2><p class="muted">'+escapeHTML(p.sanskrit)+'</p><div class="session-stage"><div class="pose-illustration">◈</div><p>'+escapeHTML(p.focus)+'</p></div><h3>Installation</h3><p>'+escapeHTML(p.instructions)+'</p><h3>À respecter</h3><p class="attention">'+escapeHTML(p.prudence)+'</p></div>';renderModal();
}
function renderModal(){$('#overlay').innerHTML=modal;}
function closeModal(){modal='';renderModal();}
function sessionPage(){
 if(!session)return home();
 const i=stepIndex(session),step=session.steps[i],remaining=session.duration-session.elapsed,progress=Math.min(100,100*session.elapsed/session.duration);
 return '<div class="session"><div class="eyebrow">'+(session.type==='yoga'?'Yoga guidé':'Méditation guidée')+'</div><h1>'+escapeHTML(session.name)+'</h1><div class="session-stage"><span class="pill">Étape '+(i+1)+' sur '+session.steps.length+'</span><div class="session-clock" id="countdown">'+formatTime(remaining)+'</div><h2>'+escapeHTML(step.title)+'</h2><p>'+escapeHTML(step.text)+'</p><p class="muted" id="audio-label">'+escapeHTML(voiceStatus)+'</p></div><div class="progress-track" aria-label="Progression"><span id="session-progress" style="width:'+progress+'%"></span></div><div class="session-controls"><button class="secondary" data-action="pause">'+(session.running?'Pause':'Reprendre')+'</button><button class="secondary" data-action="next-step">Étape suivante</button><button class="primary" data-action="finish">Terminer</button><button class="secondary" data-action="cancel-session">Quitter sans enregistrer</button></div><p class="muted">Si une posture provoque une douleur, interromps-la. Les consignes vocales ne remplacent pas l’écoute de ton corps.</p></div>';
}
function stepIndex(s){
 let elapsed=0;const total=s.steps.reduce((x,p)=>x+p.weight,0)||1;
 for(let i=0;i<s.steps.length;i++){elapsed+=s.duration*s.steps[i].weight/total;if(s.elapsed<elapsed)return i;}
 return s.steps.length-1;
}
function render(){
 document.documentElement.dataset.theme=profile().theme==='horizon'?'horizon':'linen';
 renderShell();
 const html=session?sessionPage():page==='home'?home():page==='yoga'?yogaPage():page==='meditate'?meditationPage():page==='astro'?astroPage():profilePage();
 $('#main').innerHTML=html;renderModal();
}
function findRoutine(id){return yoga.routines.find(x=>x.id===id);}
function startSession(type,id){
 if(session)return notice('Termine ou quitte la séance actuelle.');
 let steps=[],duration=0,name='';
 if(type==='yoga'){
  const r=findRoutine(id);if(!r)return;name=r.name;duration=r.duration*60;
  steps=r.poseIds.map((poseId)=>{const p=yoga.poses.find(x=>x.id===poseId);return {title:p?.nom||poseId,text:p?.instructions||'',weight:1,clip:'pose_'+poseId};});
 }else{
  const med=meditations.sessions.find(x=>x.id===id);if(!med)return;name=med.name;duration=med.minutes*60;
  steps=(med.scripts[profile().meditationStyle]||[]).map((x,i)=>({title:i===0?'S’installer':i===med.scripts[profile().meditationStyle].length-1?'Revenir': 'Prendre le temps',text:x.text,weight:Math.max(1,Number(x.pause)||1),clip:med.id+'_'+profile().meditationStyle+'_'+String(i).padStart(2,'0')}));
 }
 if(!steps.length)return notice('Cette séance n’a pas de contenu.');
 session={id,type,name,duration,elapsed:0,running:true,last:Date.now(),steps,spoken:-1};
 page=type==='yoga'?'yoga':'meditate';render();
 announceStep();clearInterval(timer);timer=setInterval(tick,300);
}
function stopAudio(){if(audio){audio.pause();audio.src='';audio=null;}}
async function voiceManifest(){
 if(manifest)return manifest;
 const res=await fetch('/voice/vivienne-fr-v1/manifest.json');
 if(!res.ok)throw Error('Pack Vivienne non installé.');
 const obj=await res.json();
 if(obj.format!=='sichosana-voice-pack'||obj.voiceId!=='fr-FR-VivienneMultilingualNeural')throw Error('Identité vocale inconnue.');
 manifest=obj;return obj;
}
async function playVoice(clip){
 stopAudio();
 try{
  const m=await voiceManifest(),record=m.files[clip];if(!record)throw Error('Segment absent : '+clip);
  const path='/voice/vivienne-fr-v1/'+encodeURIComponent(record.src);
  audio=new Audio(path);audio.preload='auto';audio.volume=0.94;
  await audio.play();voiceStatus='Voix Vivienne';
 }catch(err){voiceStatus='Audio indisponible : '+err.message;}
 const label=$('#audio-label');if(label)label.textContent=voiceStatus;
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
function syncAuth(){const t=state.credentials?.token;if(!t)throw Error('Association manquante.');return {'Content-Type':'application/json','Authorization':'Bearer '+t};}
async function syncRequest(path,options={}){
 const res=await fetch('/api/v1/'+path,{...options,headers:{...(options.headers||{})}});
 let data={};try{data=await res.json();}catch(e){}
 if(!res.ok){const error=new Error(data.error||'Erreur serveur '+res.status);error.status=res.status;error.data=data;throw error;}
 return data;
}
async function beginPairing(){
 const code=($('#sync-code')?.value||'').trim().toUpperCase(),password=$('#sync-password')?.value||'';
 if(password.length<12)return notice('Mot de passe : au moins 12 caractères.');
 syncBusy=true;
 try{
  const path=code?'pair':'groups';
  const out=await syncRequest(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code,password,deviceId:uid()})});
  state.credentials={token:out.token,code:out.code};state.revision=out.revision||0;await save();
  if(code){await pullSync();}else{await pushSync();notice('Code d’association : '+out.code+' — conserve-le avec ton mot de passe.');}
 }catch(err){notice('Association impossible : '+err.message);}finally{syncBusy=false;render();}
}
async function pullSync(){
 const out=await syncRequest('snapshot',{headers:syncAuth()});
 if(out.data)ingest(out.data,true);state.revision=out.revision;await save();render();notice('Tous les profils ont été récupérés et fusionnés.');
}
async function pushSync(){
 const auth=syncAuth();
 try{
  const out=await syncRequest('snapshot',{method:'PUT',headers:{...auth,'If-Match':String(state.revision||0)},body:JSON.stringify({data:snapshot()})});
  state.revision=out.revision;await save();notice('Sauvegarde synchronisée.');
 }catch(err){
  if(err.status!==409)throw err;
  const remote=err.data;
  if(remote?.data)ingest(remote.data,true);
  state.revision=remote.revision;await save();
  const retry=await syncRequest('snapshot',{method:'PUT',headers:{...auth,'If-Match':String(state.revision)},body:JSON.stringify({data:snapshot()})});
  state.revision=retry.revision;await save();notice('Conflit fusionné : aucun profil effacé.');
 }
}
async function doSync(pull=false){
 if(syncBusy)return;syncBusy=true;render();
 try{if(pull)await pullSync();else await pushSync();}catch(err){notice('Synchronisation : '+err.message);}finally{syncBusy=false;render();}
}
async function cacheVoicePack(){
 try{
  if(!('caches' in window))throw Error('Cache non disponible.');
  const m=await voiceManifest(),cache=await caches.open('sichosana-vivienne-'+m.packId),items=Object.values(m.files);
  let done=0;voiceStatus='Téléchargement : 0 / '+items.length;render();
  for(const x of items){
   const url='/voice/vivienne-fr-v1/'+encodeURIComponent(x.src);
   if(!await cache.match(url)){const r=await fetch(url);if(!r.ok)throw Error('Fichier absent : '+x.src);await cache.put(url,r.clone());}
   done++;voiceStatus='Téléchargement : '+done+' / '+items.length;
   const e=$('#voice-status');if(e)e.textContent=voiceStatus;
  }
  const mr=await fetch('/voice/vivienne-fr-v1/manifest.json');if(mr.ok)await cache.put('/voice/vivienne-fr-v1/manifest.json',mr);
  voiceStatus=done+' fichiers Vivienne disponibles hors ligne.';render();notice('Pack vocal installé.');
 }catch(err){voiceStatus='Audio indisponible : '+err.message;render();notice(voiceStatus);}
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
 if(action==='page'){if(session)abortSession();page=value;render();window.scrollTo(0,0);return;}
 if(action==='routine-filter'){routineFilter=value;render();return;}
 if(action==='pose-filter'){poseFilter=value;render();return;}
 if(action==='med-filter'){meditationFilter=value;render();return;}
 if(action==='med-level'){profile().meditationStyle=value;touch();render();return;}
 if(action==='theme'){profile().theme=value;touch();render();return;}
 if(action==='favorite'){const list=profile().favorites;profile().favorites=list.includes(value)?list.filter(x=>x!==value):[...list,value];touch();render();return;}
 if(action==='start-yoga')return startSession('yoga',value);
 if(action==='start-med')return startSession('meditate',value);
 if(action==='pose')return poseModal(value);
 if(action==='close')return closeModal();
 if(action==='pause'){if(session){session.running=!session.running;session.last=Date.now();if(!session.running)stopAudio();render();if(session.running)announceStep();}return;}
 if(action==='next-step'){if(session){const idx=stepIndex(session);session.elapsed=Math.min(session.duration,stepBoundary(session,idx)+0.01);session.spoken=-1;tick();}return;}
 if(action==='finish')return finishSession(false);
 if(action==='cancel-session')return abortSession();
 if(action==='add-profile'){const name=prompt('Nom du nouveau profil :');if(name&&name.trim()){const p=defaultProfile();p.name=name.trim().slice(0,50);state.profiles.push(p);state.activeProfileId=p.id;save();render();}return;}
 if(action==='select-profile'){state.activeProfileId=value;save();render();return;}
 if(action==='save-name'){profile().name=($('#profile-name')?.value||'Mon espace').trim().slice(0,50)||'Mon espace';touch();render();return;}
 if(action==='export')return exportData();
 if(action==='import')return $('#import-json')?.click();
 if(action==='pair')return beginPairing();
 if(action==='sync')return doSync(false);
 if(action==='sync-pull')return doSync(true);
 if(action==='disconnect'){state.credentials=null;state.revision=0;save();render();return;}
 if(action==='cache-voice')return cacheVoicePack();
 if(action==='notifications')return notifications();
}
document.addEventListener('click',(e)=>{const target=e.target.closest('[data-action]');if(!target)return;e.preventDefault();handle(target.dataset.action,target.dataset.value||'').catch?.(err=>notice(err.message));});
document.addEventListener('change',async(e)=>{
 if(e.target.id==='zodiac'){profile().zodiac=e.target.value;touch();render();}
 if(e.target.id==='import-json'){
  const file=e.target.files?.[0];if(!file)return;
  try{if(file.size>2_000_000)throw Error('Fichier trop volumineux.');ingest(JSON.parse(await file.text()));notice('Sauvegarde importée et fusionnée.');}catch(err){notice('Import impossible : '+err.message);}
 }
});
window.addEventListener('online',render);window.addEventListener('offline',render);
async function init(){
 try{
  db=await openDB();state=await dbRead('app')||initialState();
  if(!state.profiles?.length){state=initialState();await save();}
  const data=await Promise.all([fetch('/data/yoga.json').then(r=>{if(!r.ok)throw Error('Yoga indisponible');return r.json();}),fetch('/data/meditations.json').then(r=>{if(!r.ok)throw Error('Méditations indisponibles');return r.json();})]);
  yoga=data[0];meditations=data[1];render();
  if('serviceWorker' in navigator)navigator.serviceWorker.register('/sw.js').catch(()=>{});
 }catch(err){$('#main').innerHTML='<div class="attention"><h2>Initialisation impossible</h2><p>'+escapeHTML(err.message)+'</p><p>Vérifie la connexion initiale et le stockage de ton appareil.</p></div>';}
}
init();
