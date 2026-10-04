const news = document.querySelector('#news');
const buttons = document.querySelectorAll('[data-provider]');
const date = value => new Intl.DateTimeFormat(undefined,{month:'short',day:'numeric',year:'numeric'}).format(new Date(value));
async function load(provider='All') {
  news.innerHTML = '<div class="loading">Loading the latest signal…</div>';
  try {
    const response = await fetch(`/api/articles?provider=${encodeURIComponent(provider)}`);
    if (!response.ok) throw new Error('Request failed');
    const {articles} = await response.json();
    news.innerHTML = articles.length ? articles.map(a => `<article class="card"><div class="meta"><span>${escapeHtml(a.provider)}</span><span class="dot">•</span><time>${date(a.published_at)}</time></div><h2>${escapeHtml(a.title)}</h2><p>${escapeHtml(a.description || 'Read the original update for more details.')}</p><a href="${safeUrl(a.canonical_url)}" target="_blank" rel="noopener noreferrer">Read original ↗</a></article>`).join('') : '<div class="empty">No articles found for this provider yet.</div>';
  } catch { news.innerHTML = '<div class="empty">Could not load the radar right now. Please try again soon.</div>'; }
}
function escapeHtml(value=''){return value.replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}
function safeUrl(value){try{const u=new URL(value);return ['http:','https:'].includes(u.protocol)?u.href:'#'}catch{return '#'}}
buttons.forEach(button=>button.addEventListener('click',()=>{buttons.forEach(b=>b.classList.remove('active'));button.classList.add('active');load(button.dataset.provider)}));
load();

