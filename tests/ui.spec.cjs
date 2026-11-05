const {test,expect} = require('@playwright/test');
const url='http://127.0.0.1:8080/';
test('iPhone: navigation, chronomètre, progression et offline',async({page,context})=>{
 await page.setViewportSize({width:390,height:844});
 await page.goto(url);
 await expect(page.locator('.bottom-nav')).toBeVisible();
 await expect(page.locator('.sidebar')).toBeHidden();
 await expect(page.getByRole('heading',{name:'Un moment pour soi'})).toBeVisible();
 await page.locator('[data-action="start-yoga"]').first().click();
 await expect(page.locator('#countdown')).toBeVisible();
 await page.locator('[data-action="pause"]').click();
 await expect(page.locator('[data-action="pause"]')).toContainText('Reprendre');
 await page.locator('[data-action="pause"]').click();
 await page.locator('[data-action="finish"]').click();
 await page.locator('.bottom-nav [data-value="profile"]').click();
 await expect(page.getByText('Mon espace',{exact:true}).first()).toBeVisible();
 await expect(page.locator('.history-list')).toContainText('Hatha doux');
 await page.screenshot({path:'screenshots/iphone.png',fullPage:true});
 await page.evaluate(()=>navigator.serviceWorker.ready);
 await context.setOffline(true);
 await page.reload();
 await expect(page.locator('.bottom-nav')).toBeVisible();
 await expect(page.locator('h1').first()).toBeVisible();
});
test('iPad: navigation horizontale et grille spécifique',async({page})=>{
 await page.setViewportSize({width:834,height:1112});
 await page.goto(url);
 await expect(page.locator('.bottom-nav')).toBeVisible();
 await expect(page.locator('.sidebar')).toBeHidden();
 await expect(page.locator('.home-desktop-layout')).toBeVisible();
 await page.locator('.bottom-nav [data-value="meditate"]').click();
 await expect(page.getByRole('heading',{name:'Méditation'})).toBeVisible();
 await expect(page.locator('.meditation-levels button')).toHaveCount(3);
 await page.screenshot({path:'screenshots/ipad.png',fullPage:true});
});
test('ordinateur: panneau latéral, multi-profils et thèmes',async({page})=>{
 await page.setViewportSize({width:1440,height:900});
 await page.goto(url);
 await expect(page.locator('.sidebar')).toBeVisible();
 await expect(page.locator('.bottom-nav')).toBeHidden();
 await page.locator('.sidebar [data-value="profile"]').click();
 page.on('dialog', dialog=>dialog.accept('Compte de test'));
 await page.locator('[data-action="add-profile"]').click();
 await expect(page.locator('.profile-option.active')).toContainText('Compte de test');
 await page.locator('[data-action="theme"][data-value="horizon"]').click();
 await expect(page.locator('html')).toHaveAttribute('data-theme','horizon');
 await page.screenshot({path:'screenshots/desktop.png',fullPage:true});
});


test('Synchronisation de tous les profils entre deux appareils sans perte',async({browser})=>{
 const c1=await browser.newContext({viewport:{width:1280,height:900}}),c2=await browser.newContext({viewport:{width:1280,height:900}});
 try{
  const a=await c1.newPage(),b=await c2.newPage();
  await a.goto(url);await a.locator('.sidebar [data-value="profile"]').click();
  a.on('dialog',d=>d.accept('Profil A'));
  await a.locator('[data-action="add-profile"]').click();
  await a.locator('#sync-password').fill('MotDePasseUniqueDeTest2026');
  await a.locator('[data-action="pair"]').click();
  const toast=await a.locator('#toast').textContent();
  const code=(toast||'').match(/[A-F0-9]{10}/)?.[0];
  expect(code,'Un code d’association doit être communiqué').toBeTruthy();
  await b.goto(url);await b.locator('.sidebar [data-value="profile"]').click();
  await b.locator('#sync-code').fill(code);
  await b.locator('#sync-password').fill('MotDePasseUniqueDeTest2026');
  await b.locator('[data-action="pair"]').click();
  await expect(b.locator('.profile-option')).toHaveCount(2);
  await expect(b.locator('.profile-options')).toContainText('Profil A');
  b.on('dialog',d=>d.accept('Profil B'));
  await b.locator('[data-action="add-profile"]').click();
  await b.locator('[data-action="sync"]').click();
  await a.locator('[data-action="sync-pull"]').click();
  await expect(a.locator('.profile-option')).toHaveCount(3);
  await expect(a.locator('.profile-options')).toContainText('Profil A');
  await expect(a.locator('.profile-options')).toContainText('Profil B');
 }finally{await c1.close();await c2.close();}
});
