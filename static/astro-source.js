'use strict';
const signs=['Bélier','Taureau','Gémeaux','Cancer','Lion','Vierge','Balance','Scorpion','Sagittaire','Capricorne','Verseau','Poissons'];
const panel=document.getElementById('signs');
const info=async sign=>{
 try{
 const res=await fetch('/api/v1/content/horoscope?sign='+encodeURIComponent(sign),{cache:'no-store'});
 if(!res.ok)throw Error('HTTP '+res.status);
 const data=await res.json();
 const section=document.createElement('article');section.className='card';
 const heading=document.createElement('h2');heading.textContent=sign;section.append(heading);
 const paragraph=document.createElement('p');paragraph.textContent=data.text||'Indisponible';section.append(paragraph);
 const link=document.createElement('a');link.href='https://sigastra.com/fr/horoscope-du-jour';link.textContent='Source Sigastra';section.append(link);
 return section;
 }catch(e){const item=document.createElement('article');item.className='card';item.textContent=sign+' — Indisponible';return item;}
};
(async()=>{const nodes=await Promise.all(signs.map(info));panel.replaceChildren(...nodes);})();
