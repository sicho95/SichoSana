/* Parcours compte de SichoSana V2. Aucune commande NAS ni synchronisation technique visible. */
'use strict';
const clean=(s)=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const errorMessage=(err)=>err?.message||'Une erreur est survenue.';
let callbacks=null, session=null, mode='login', pendingPseudo='', adminUsers=[],
    resetToken=new URLSearchParams(location.search).get('reset')||'', config=null;
if(resetToken)mode='reset';
export function configure(callbacksObject){callbacks=callbacksObject;}
export function user(){return session?.user||null;}
export function token(){return session?.token||null;}
export function loggedIn(){return !!session;}
export function mustChangePassword(){return !!session?.user?.mustChangePassword;}
export async function api(path,options={}){
 const headers={...(options.headers||{})};
 if(options.body && !headers['Content-Type'])headers['Content-Type']='application/json';
 if(session?.token)headers.Authorization='Bearer '+session.token;
 let res;
 try{res=await fetch('/api/v1/'+path,{...options,headers,cache:'no-store'});}
 catch(e){throw new Error('Connexion indisponible. Réessaie dès que le réseau revient.');}
 let data={};try{data=await res.json();}catch(e){}
 if(!res.ok){const error=new Error(data.error||'Erreur '+res.status);error.status=res.status;error.data=data;throw error;}
 return data;
}
export async function resume(){
 try{config=await api('auth/config');}catch(e){config={registrationOpen:false};}
 const saved=await callbacks.read('auth');
 if(!saved?.token)return;
 session=saved;
 try{
  const out=await api('auth/me');
  session.user=out.user;
  await callbacks.write('auth',session);
  await callbacks.enter(out.user);
 }catch(e){
  if(e.status===401||e.status===403){session=null;await callbacks.write('auth',null);}
  else if(saved.user){ // Hors ligne : préserver la session en cache, sans prétendre au serveur disponible.
   session=saved;await callbacks.enter(saved.user);
  }
 }
}
export function show(next){mode=next;callbacks.render();}
export function screen(){
 const brand='<div class="auth-emblem" aria-hidden="true"><img src="/icon.svg" alt="" width="64" height="64"></div><div class="eyebrow">SichoSana</div>';
 const fields=(parts)=>parts.join('');
 const intro='<div class="auth-intro">'+brand+'<h1>'+(mode==='register'?'Créer mon espace':mode==='forgot'?'Retrouver mon accès':mode==='reset'?'Nouveau mot de passe':'Prendre un moment pour moi')+'</h1><p>Un lieu doux pour respirer, bouger et se retrouver à son rythme.</p></div>';
 let form='';
 if(mode==='register'){
  form='<form class="auth-form" data-account-form="register">'+fields([
   '<label for="auth-pseudo">Pseudo unique</label><input id="auth-pseudo" name="pseudo" required maxlength="30" minlength="3" autocomplete="username" placeholder="Ton pseudo">',
   '<label for="auth-email">Adresse email</label><input id="auth-email" name="email" type="email" required autocomplete="email" placeholder="ton@email.fr">',
   '<label for="auth-pass">Mot de passe (10 caractères minimum)</label><input id="auth-pass" name="password" type="password" minlength="10" required autocomplete="new-password" placeholder="Choisis un mot de passe sûr">',
   '<button class="primary" type="submit">Demander mon inscription</button>'])+'</form>'+
   '<p class="auth-hint">Ton inscription devra être validée par un administrateur.</p>'+
   '<button class="text-link" data-account="show-login">Déjà inscrit ? Me connecter</button>';
 }else if(mode==='pending'){
  form='<div class="auth-result"><h2>Ta demande a bien été reçue</h2><p>Merci '+clean(pendingPseudo)+'. Un administrateur va examiner ton inscription et tu recevras un email après validation.</p><p>Ton espace de sérénité t’attend.</p></div><button class="secondary" data-account="show-login">Revenir à la connexion</button>';
 }else if(mode==='forgot'){
  form='<form class="auth-form" data-account-form="forgot"><label for="auth-identity">Pseudo ou adresse email</label><input id="auth-identity" name="pseudoOrEmail" required autocomplete="username"><button class="primary" type="submit">Recevoir un lien de réinitialisation</button></form><button class="text-link" data-account="show-login">Retour à la connexion</button>';
 }else if(mode==='reset'){
  form='<form class="auth-form" data-account-form="reset"><label for="auth-reset-pass">Nouveau mot de passe</label><input id="auth-reset-pass" name="newPassword" type="password" minlength="10" required autocomplete="new-password"><button class="primary" type="submit">Enregistrer mon nouveau mot de passe</button></form><button class="text-link" data-account="show-login">Retour à la connexion</button>';
 }else{
  form='<form class="auth-form" data-account-form="login"><label for="auth-pseudo">Pseudo</label><input id="auth-pseudo" name="pseudo" required autocomplete="username" autocapitalize="none" placeholder="Ton pseudo"><label for="auth-pass">Mot de passe</label><input id="auth-pass" name="password" type="password" required autocomplete="current-password"><button class="primary" type="submit">Me connecter</button></form><div class="auth-links"><button class="text-link" data-account="show-forgot">Mot de passe oublié ?</button><button class="text-link" data-account="show-register">M’inscrire</button></div>';
 }
 return '<section class="auth-layout"><div class="auth-photo"><div class="auth-photo-copy"><span>Respire, tout commence ici.</span><strong>Un instant rien qu’à soi.</strong></div></div><div class="auth-card">'+intro+form+'<div class="auth-signoff">Chaque jour est une invitation à revenir à l’essentiel.<br>L’équipe de SichoSana</div></div></section>';
}
export function passwordScreen(){
 return '<section class="auth-layout"><div class="auth-photo"></div><div class="auth-card"><div class="eyebrow">Sécurisation du compte</div><h1>Choisis ton mot de passe personnel</h1><p>Ton mot de passe provisoire doit être remplacé avant de commencer.</p><form class="auth-form" data-account-form="password"><label>Mot de passe actuel</label><input name="currentPassword" type="password" required autocomplete="current-password"><label>Nouveau mot de passe</label><input name="newPassword" type="password" minlength="10" required autocomplete="new-password"><button class="primary" type="submit">Sécuriser mon compte</button></form><button class="text-link" data-account="logout">Se déconnecter</button></div></section>';
}
export function profilePanel(){
 if(!user())return '';
 return '<section class="card account-card"><div class="section-heading"><h2>Mon compte</h2><span class="pill">'+(user().role==='admin'?'Administrateur':'Membre')+'</span></div><p><strong>'+clean(user().pseudo)+'</strong><br><span class="muted">'+clean(user().email)+'</span></p><p class="muted">Tes préférences et tes profils sont enregistrés automatiquement et retrouvés sur tes appareils connectés.</p><details><summary>Changer mon mot de passe</summary><form class="auth-form compact" data-account-form="password"><label>Mot de passe actuel</label><input name="currentPassword" type="password" required autocomplete="current-password"><label>Nouveau mot de passe</label><input name="newPassword" type="password" minlength="10" required autocomplete="new-password"><button class="secondary" type="submit">Changer mon mot de passe</button></form></details><button class="secondary" data-account="logout">Se déconnecter</button></section>';
}
export async function refreshAdmin(){
 if(user()?.role!=='admin')return;
 try{adminUsers=(await api('admin/users')).users||[];callbacks.render();}
 catch(e){callbacks.notice('Administration : '+errorMessage(e));}
}
export function adminScreen(){
 return '<div class="page-heading"><div><div class="eyebrow">Gestion des accès</div><h1>Administration</h1><p class="subtitle">Approuve les inscriptions, gère les comptes et les droits.</p></div></div><div class="admin-board"><div class="section-heading"><h2>Comptes</h2><button class="secondary" data-account="refresh-users">Actualiser</button></div>'+
 (adminUsers.length?adminUsers.map(u=>{
   const pending=u.status==='pending',active=u.status==='active',suspended=u.status==='suspended';
   return '<article class="card admin-user"><div><strong>'+clean(u.pseudo)+'</strong> <span class="pill">'+clean(u.status)+'</span> '+(u.role==='admin'?'<span class="pill">Admin</span>':'')+'<p class="muted">'+clean(u.email)+'</p></div><div class="admin-buttons">'+
   (pending?'<button class="primary" data-account="manage" data-admin-id="'+clean(u.id)+'" data-admin-action="approve">Valider</button>':'')+
   (active&&u.id!==user().id?'<button class="secondary" data-account="manage" data-admin-id="'+clean(u.id)+'" data-admin-action="suspend">Suspendre</button>':'')+
   (suspended?'<button class="secondary" data-account="manage" data-admin-id="'+clean(u.id)+'" data-admin-action="restore">Réactiver</button>':'')+
   (active&&(u.id!==user().id||u.role!=='admin')?'<button class="secondary" data-account="manage" data-admin-id="'+clean(u.id)+'" data-admin-action="'+(u.role==='admin'?'demote':'promote')+'">'+(u.role==='admin'?'Retirer droit admin':'Rendre admin')+'</button>':'')+
   (u.id!==user().id?'<button class="small-btn" data-account="manage" data-admin-id="'+clean(u.id)+'" data-admin-action="delete">Supprimer</button>':'')+
   '</div></article>';
 }).join(''):'<div class="card"><p>Charge les comptes pour voir les demandes.</p></div>')+
 '<section class="card smtp-admin"><div class="eyebrow">Communication</div><h3>Emails administratifs</h3><p>Les inscriptions sont signalées à tous les administrateurs actifs. Les emails partent de l’adresse configurée sur le NAS.</p><p class="pill">'+(config?.emailConfigured?'Service SMTP déclaré':'SMTP à configurer sur le NAS')+'</p><p class="muted">Pour utiliser Gmail provisoirement, exécuter le script local de configuration avec un mot de passe d’application Google. Le secret ne doit jamais être saisi sur le site ni envoyé à ChatGPT.</p><button class="secondary" data-account="retry-emails">Réessayer les emails en attente</button></section></div>';
}
export async function onSubmit(form){
 const data=Object.fromEntries(new FormData(form));
 try{
  if(form.dataset.accountForm==='register'){
   pendingPseudo=data.pseudo;
   await api('auth/register',{method:'POST',body:JSON.stringify(data)});
   mode='pending';callbacks.render();return;
  }
  if(form.dataset.accountForm==='login'){
   const out=await api('auth/login',{method:'POST',body:JSON.stringify(data)});
   session=out;await callbacks.write('auth',out);
   await callbacks.enter(out.user);
   if(out.user.mustChangePassword)callbacks.notice('Change ton mot de passe provisoire.');
   callbacks.render();
   if(!out.user.mustChangePassword)await callbacks.welcome(out.user);
   return;
  }
  if(form.dataset.accountForm==='forgot'){
   await api('auth/forgot',{method:'POST',body:JSON.stringify(data)});
   callbacks.notice('Si un compte correspond, un email a été demandé.');
   mode='login';callbacks.render();return;
  }
  if(form.dataset.accountForm==='reset'){
   await api('auth/reset',{method:'POST',body:JSON.stringify({...data,token:resetToken})});
   history.replaceState({},'',location.pathname);
   resetToken='';mode='login';callbacks.notice('Mot de passe changé : connecte-toi.');callbacks.render();return;
  }
  if(form.dataset.accountForm==='password'){
   await api('auth/password',{method:'POST',body:JSON.stringify(data)});
   session.user.mustChangePassword=false;
   await callbacks.write('auth',session);
   callbacks.notice('Ton nouveau mot de passe est enregistré.');
   callbacks.render();await callbacks.welcome(session.user);return;
  }
 }catch(err){callbacks.notice(errorMessage(err));}
}
export async function onAction(action,target){
 if(action==='show-login'||action==='show-register'||action==='show-forgot'){
  mode=action.replace('show-','');callbacks.render();return;
 }
 if(action==='logout'){
  try{await api('auth/logout',{method:'POST',body:'{}'});}catch(e){}
  session=null;await callbacks.write('auth',null);await callbacks.exit();
  mode='login';callbacks.render();return;
 }
 if(action==='refresh-users'){await refreshAdmin();return;}
 if(action==='retry-emails'){try{await api('admin/emails/retry',{method:'POST',body:'{}'});callbacks.notice('Envoi des messages en attente relancé.');}catch(e){callbacks.notice(errorMessage(e));}return;}
 if(action==='manage'){
  const id=target.dataset.adminId,change=target.dataset.adminAction;
  if(change==='delete'&&!confirm('Supprimer définitivement ce compte et toutes ses données ? Cette opération est irréversible.'))return;
  if(change==='promote'&&!confirm('Donner les droits administrateur à ce compte ?'))return;
  try{
   await api('admin/users/'+encodeURIComponent(id),{method:'PATCH',body:JSON.stringify({action:change})});
   callbacks.notice('Compte mis à jour.');await refreshAdmin();
  }catch(e){callbacks.notice(errorMessage(e));}
 }
}
