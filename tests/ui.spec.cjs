const {test,expect}=require('@playwright/test');
const url='http://127.0.0.1:8080/';
const ADMIN={pseudo:'Sicho',password:'TestAdminPassword2026!'};

async function signIn(page,pseudo=ADMIN.pseudo,password=ADMIN.password){
 await page.goto(url);
 await expect(page.getByRole('heading',{name:'Prendre un moment pour moi'})).toBeVisible();
 await page.locator('input[name="pseudo"]').fill(pseudo);
 await page.locator('input[name="password"]').fill(password);
 await page.getByRole('button',{name:'Me connecter'}).click();
 await expect(page.getByRole('heading',{name:'Un moment pour soi'})).toBeVisible({timeout:15000});
 await page.locator('.welcome-modal').waitFor({state:'visible',timeout:2500}).catch(()=>{});
 if(await page.locator('.welcome-modal').isVisible())await page.locator('.welcome-modal [data-action="close"]').first().click();
}

test('iPhone: inscription non affichée après connexion, yoga et progression',async({page,context})=>{
 await page.setViewportSize({width:390,height:844});
 await signIn(page);
 await expect(page.locator('.bottom-nav')).toBeVisible();
 await expect(page.locator('.bottom-nav .nav-link')).toHaveCount(5);
 await expect(page.locator('.bottom-nav [data-value="admin"]')).toHaveCount(0);
 const navHeight=await page.locator('.bottom-nav').evaluate(n=>n.getBoundingClientRect().height);
 expect(navHeight).toBeLessThan(110);
 await expect(page.locator('.sidebar')).toBeHidden();
 await page.locator('[data-action="start-yoga"]').first().click();
 await expect(page.locator('#countdown')).toBeVisible();
 await expect(page.locator('.audio-replay')).toBeVisible();
 await page.locator('[data-action="pause"]').click();
 await expect(page.locator('[data-action="pause"]')).toContainText('Reprendre');
 await page.locator('[data-action="pause"]').click();
 await page.locator('[data-action="finish"]').click();
 await page.locator('.bottom-nav [data-value="profile"]').click();
 await expect(page.locator('.history-list')).toContainText('Hatha doux');
 await expect(page.getByRole('heading',{name:'Synchronisation NAS'})).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Ouvrir l’administration'})).toBeVisible();
 await page.getByRole('button',{name:'Ouvrir l’administration'}).click();
 await expect(page.getByRole('heading',{name:'Administration'})).toBeVisible();
 await expect(page.locator('.admin-user')).toHaveCount(1);
 await page.screenshot({path:'screenshots/iphone.png',fullPage:true});
 await page.evaluate(()=>navigator.serviceWorker.ready);
 await context.setOffline(true);
 await page.reload();
 await expect(page.locator('.bottom-nav')).toBeVisible({timeout:15000});
});

test('iPad: composition adaptée et 3 niveaux de méditation',async({page})=>{
 await page.setViewportSize({width:834,height:1112});
 await signIn(page);
 await expect(page.locator('.bottom-nav')).toBeVisible();
 await expect(page.locator('.sidebar')).toBeHidden();
 await expect(page.locator('.home-desktop-layout')).toBeVisible();
 await page.locator('.bottom-nav [data-value="meditate"]').click();
 await expect(page.getByRole('heading',{name:'Méditation'})).toBeVisible();
 await expect(page.locator('.meditation-levels button')).toHaveCount(3);
 await page.screenshot({path:'screenshots/ipad.png',fullPage:true});
});

test('ordinateur: admin, multi-profils et thème',async({page})=>{
 await page.setViewportSize({width:1440,height:900});
 await signIn(page);
 await expect(page.locator('.sidebar')).toBeVisible();
 await expect(page.locator('.bottom-nav')).toBeHidden();
 await page.locator('.sidebar [data-value="profile"]').click();
 page.on('dialog',d=>d.accept('Compte de test'));
 await page.locator('[data-action="add-profile"]').click();
 await expect(page.locator('.profile-option.active')).toContainText('Compte de test');
 await page.locator('[data-action="theme"][data-value="horizon"]').click();
 await expect(page.locator('html')).toHaveAttribute('data-theme','horizon');
 await page.locator('.sidebar [data-value="admin"]').click();
 await expect(page.getByRole('heading',{name:'Administration'})).toBeVisible();
 await expect(page.locator('.admin-user')).toHaveCount(1);
 await page.screenshot({path:'screenshots/desktop.png',fullPage:true});
});

test('inscription puis approbation admin et connexion insensible à la casse',async({browser})=>{
 const c1=await browser.newContext(),c2=await browser.newContext();
 try{
  const applicant=await c1.newPage(),admin=await c2.newPage();
  await applicant.goto(url);
  await applicant.getByRole('button',{name:'M’inscrire'}).click();
  await applicant.locator('input[name="pseudo"]').fill('ZénitudeTest');
  await applicant.locator('input[name="email"]').fill('zenitude@example.test');
  await applicant.locator('input[name="password"]').fill('UnMotDePasseLong2026!');
  await applicant.getByRole('button',{name:'Demander mon inscription'}).click();
  await expect(applicant.getByText('Ta demande a bien été reçue')).toBeVisible();
  await signIn(admin);
  await admin.locator('.sidebar [data-value="admin"]').click();
  await expect(admin.locator('.admin-user')).toHaveCount(2);
  await admin.locator('.admin-user').filter({hasText:'ZénitudeTest'}).getByRole('button',{name:'Valider'}).click();
  await expect(admin.locator('.admin-user').filter({hasText:'ZénitudeTest'})).toContainText('active');
  await applicant.getByRole('button',{name:'Revenir à la connexion'}).click();
  await applicant.locator('input[name="pseudo"]').fill('zÉNITUDEtest');
  await applicant.locator('input[name="password"]').fill('UnMotDePasseLong2026!');
  await applicant.getByRole('button',{name:'Me connecter'}).click();
  await expect(applicant.getByRole('heading',{name:'Un moment pour soi'})).toBeVisible();
  await expect(applicant.locator('.welcome-modal')).toBeVisible();
 }finally{await c1.close();await c2.close();}
});

test('synchronisation de tous les profils sans réglage NAS',async({browser})=>{
 const c1=await browser.newContext({viewport:{width:1280,height:900}}),
       c2=await browser.newContext({viewport:{width:1280,height:900}});
 try{
  const a=await c1.newPage(),b=await c2.newPage();
  await signIn(a);await signIn(b);
  await a.locator('.sidebar [data-value="profile"]').click();
  a.on('dialog',d=>d.accept('Profil synchronisé'));
  await a.locator('[data-action="add-profile"]').click();
  await expect(a.locator('.profile-options')).toContainText('Profil synchronisé');
  await expect.poll(async()=>{
   const r=await a.evaluate(async()=>{
    const m=await import('/auth.js');
    const z=await m.api('account/snapshot');return z.data?.profiles?.length||0;
   });return r;
  },{timeout:16000}).toBeGreaterThanOrEqual(2);
  await b.reload();
  await b.locator('.sidebar [data-value="profile"]').click();
  await expect(b.locator('.profile-options')).toContainText('Profil synchronisé',{timeout:16000});
  await expect(b.locator('#sync-code')).toHaveCount(0);
 }finally{await c1.close();await c2.close();}
});
