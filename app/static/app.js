if (document.querySelector('[data-view]')) {
 const lastView = sessionStorage.getItem('clinic-return-view');
 sessionStorage.removeItem('clinic-return-view');
 if (!location.hash && lastView) history.replaceState(null,'','#'+lastView);
 document.querySelectorAll('.view-panel form').forEach(form=>form.addEventListener('submit',()=>sessionStorage.setItem('clinic-return-view',form.closest('.view-panel').id)));
}
const links = [...document.querySelectorAll('[data-view]')];
function showView() {
 const name = location.hash.slice(1) || 'overview';
 const chosen = links.find(link => link.dataset.view === name) || links[0];
 if (!chosen) return;
 document.querySelectorAll('.view-panel').forEach(panel => panel.hidden = panel.id !== chosen.dataset.view);
 links.forEach(link => { link.classList.toggle('active', link === chosen); if(link === chosen) link.setAttribute('aria-current','page'); else link.removeAttribute('aria-current'); });
 document.querySelector('#page-label').textContent = chosen.textContent.trim().slice(1).trim();
 document.querySelectorAll('.demo-panel').forEach(panel => panel.hidden = chosen.dataset.view !== 'overview');
}
window.addEventListener('hashchange',showView); showView();
const dateLabel = document.querySelector('#today-label');
if(dateLabel) dateLabel.textContent = new Intl.DateTimeFormat('vi-VN',{dateStyle:'full',timeZone:'Asia/Ho_Chi_Minh'}).format(new Date());
const toggle = document.querySelector('#toggle-password');
if(toggle) toggle.addEventListener('click',()=>{const input=document.querySelector('#password');const show=input.type==='password';input.type=show?'text':'password';toggle.textContent=show?'Ẩn':'Hiện';toggle.setAttribute('aria-pressed',String(show));});
document.querySelectorAll('[data-search]').forEach(input=>input.addEventListener('input',()=>{let visible=0;const query=input.value.toLocaleLowerCase('vi').trim();document.querySelectorAll('#patients details').forEach(row=>{row.hidden=!row.querySelector('summary').textContent.toLocaleLowerCase('vi').includes(query);if(!row.hidden)visible++;});const empty=document.querySelector('.search-empty');if(empty)empty.hidden=visible>0||!query;}));
