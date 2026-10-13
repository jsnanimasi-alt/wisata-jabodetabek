(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const store = {
    get: k => { try { return JSON.parse(localStorage.getItem(k)) || []; } catch { return []; } },
    set: (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch { toast('Penyimpanan browser tidak tersedia.'); } }
  };
  const favs = () => store.get('jj_fav');
  const plan = () => store.get('jj_plan');
  const page = document.body.dataset.page;
  let all = null;

  function toast(msg) {
    const t = $('#toast'); t.textContent = msg; t.classList.add('show');
    clearTimeout(toast.t); toast.t = setTimeout(() => t.classList.remove('show'), 2200);
  }
  async function fetchDest(params = '') {
    const r = await fetch('/api/destinations' + (params ? '?' + params : ''));
    if (!r.ok) throw new Error('Gagal memuat data');
    return (await r.json()).items;
  }

  // ----- UI states -----
  const loading = () => { $('#list').innerHTML = '<div class="skel"></div>'.repeat(3); $('#state').innerHTML = ''; };
  const showError = retry => {
    $('#list').innerHTML = '';
    $('#state').innerHTML = '<div class="empty err"><h3>Data tidak bisa dimuat</h3><p>Periksa koneksi, lalu coba lagi.</p><button class="btn" id="retry">Coba lagi</button></div>';
    $('#retry').onclick = retry;
  };
  const showEmpty = (title, text, btn) => {
    $('#list').innerHTML = '';
    $('#state').innerHTML = `<div class="empty"><h3>${title}</h3><p>${text}</p>${btn || ''}</div>`;
  };

  // ----- cards -----
  const heart = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-7-4.6-9.5-9C1 8.5 3 5 6.5 5c2 0 3.5 1 5.5 3 2-2 3.5-3 5.5-3C21 5 23 8.5 21.5 12c-2.5 4.4-9.5 9-9.5 9z"/></svg>';
  function card(d) {
    const on = favs().includes(d.slug);
    return `<article class="card">
      <a class="media ${d.cat_class}" href="/destinasi/${d.slug}" aria-label="${esc(d.name)}"><span class="ph">${esc(d.region)}</span>
        <img src="${d.image}" alt="${esc(d.name)}" loading="lazy" onerror="this.remove()"><span class="tag">${esc(d.category)}</span></a>
      <button class="fav${on ? ' on' : ''}" data-fav="${d.slug}" aria-pressed="${on}" aria-label="Favorit: ${esc(d.name)}">${heart}</button>
      <div class="body"><h3><a href="/destinasi/${d.slug}">${esc(d.name)}</a></h3>
        <p class="loc">${esc(d.area)}, ${esc(d.region)}</p><p>${esc(d.short)}</p></div></article>`;
  }
  const renderCards = items => { $('#state').innerHTML = ''; $('#list').innerHTML = items.map(card).join(''); };

  // ----- favorites -----
  function syncFav() {
    const n = favs().length, c = $('#favCount');
    c.hidden = !n; c.textContent = n;
    $$('[data-fav]').forEach(b => {
      const on = favs().includes(b.dataset.fav);
      b.classList.toggle('on', on); b.setAttribute('aria-pressed', on);
      if (b.dataset.label) b.textContent = on ? 'Hapus dari favorit' : 'Simpan ke favorit';
    });
  }
  document.addEventListener('click', e => {
    const f = e.target.closest('[data-fav]');
    if (f) {
      const s = f.dataset.fav, list = favs(), i = list.indexOf(s);
      i >= 0 ? list.splice(i, 1) : list.push(s);
      store.set('jj_fav', list); syncFav();
      toast(i >= 0 ? 'Dihapus dari favorit' : 'Disimpan ke favorit');
      if (page === 'favorites') loadFavorites();
    }
    const p = e.target.closest('[data-plan]');
    if (p) {
      const list = plan();
      if (list.some(x => x.slug === p.dataset.plan)) return toast('Sudah ada di rencana Anda');
      list.push({ slug: p.dataset.plan, day: 1 }); store.set('jj_plan', list);
      toast('Ditambahkan ke Hari 1 rencana');
    }
  });

  // ----- nav -----
  $('#burger').onclick = e => {
    const open = $('#menu').classList.toggle('open');
    e.currentTarget.setAttribute('aria-expanded', open);
  };

  // ----- home -----
  async function loadHome() {
    loading();
    try { renderCards(await fetchDest('featured=1')); } catch { showError(loadHome); }
  }

  // ----- destinations -----
  const state = { q: '', region: '', cat: '' };
  async function loadDest() {
    loading();
    try {
      const p = new URLSearchParams({ q: state.q, region: state.region, category: state.cat });
      const items = await fetchDest(p.toString());
      $('#result').textContent = `${items.length} destinasi ditemukan`;
      if (!items.length) {
        showEmpty('Tidak ada destinasi yang cocok', 'Coba kata kunci lain atau hapus filter.', '<button class="btn" id="reset">Hapus semua filter</button>');
        $('#reset').onclick = () => { Object.assign(state, { q: '', region: '', cat: '' }); $('#fq').value = ''; setChips(); loadDest(); };
      } else renderCards(items);
    } catch { $('#result').textContent = ''; showError(loadDest); }
  }
  function setChips() {
    $$('#regionChips .chip').forEach(c => c.classList.toggle('on', c.dataset.region === state.region));
    $$('#catChips .chip').forEach(c => c.classList.toggle('on', c.dataset.cat === state.cat));
  }
  function initDest() {
    const u = new URLSearchParams(location.search);
    state.q = u.get('q') || ''; state.region = u.get('region') || ''; state.cat = u.get('category') || '';
    $('#fq').value = state.q; setChips();
    let t; $('#fq').addEventListener('input', e => { clearTimeout(t); t = setTimeout(() => { state.q = e.target.value; loadDest(); }, 250); });
    $('#regionChips').onclick = e => { const b = e.target.closest('.chip'); if (b) { state.region = b.dataset.region; setChips(); loadDest(); } };
    $('#catChips').onclick = e => { const b = e.target.closest('.chip'); if (b) { state.cat = b.dataset.cat; setChips(); loadDest(); } };
    loadDest();
  }

  // ----- favorites page -----
  async function loadFavorites() {
    if (!favs().length) return showEmpty('Belum ada favorit', 'Tekan ikon hati pada kartu destinasi untuk menyimpannya di sini.', '<a class="btn" href="/destinasi">Cari destinasi</a>');
    if (!$('#list').children.length) loading();
    try { all = all || await fetchDest(); const items = all.filter(d => favs().includes(d.slug)); items.length ? renderCards(items) : showEmpty('Belum ada favorit', 'Destinasi favorit Anda sudah tidak tersedia.'); }
    catch { showError(loadFavorites); }
  }

  // ----- itinerary -----
  async function loadPlan() {
    try {
      all = all || await fetchDest();
      $('#state').innerHTML = '';
      $('#planDest').innerHTML = all.map(d => `<option value="${d.slug}">${esc(d.name)} (${esc(d.region)})</option>`).join('');
      renderPlan();
    } catch { $('#days').innerHTML = ''; showError(loadPlan); }
  }
  function renderPlan() {
    const list = plan().filter(x => all.some(d => d.slug === x.slug));
    const maxDay = Math.max(3, ...list.map(x => +x.day));
    $('#clearPlan').hidden = !list.length;
    if (!list.length) $('#state').innerHTML = '<div class="empty"><h3>Rencana masih kosong</h3><p>Pilih destinasi di atas, atau tambahkan dari halaman detail.</p></div>';
    else $('#state').innerHTML = '';
    let html = '';
    for (let d = 1; d <= maxDay; d++) {
      const stops = list.filter(x => +x.day === d).map(x => {
        const it = all.find(a => a.slug === x.slug);
        return `<div class="stop"><div><a href="/destinasi/${it.slug}">${esc(it.name)}</a><small>${esc(it.area)}, ${esc(it.region)} &middot; <a href="${it.maps_url}" target="_blank" rel="noopener">Maps</a></small></div><button data-rm="${it.slug}" aria-label="Hapus ${esc(it.name)}">Hapus</button></div>`;
      }).join('');
      html += `<section class="day"><h3>Hari ${d}</h3>${stops || '<p class="none">Belum ada destinasi.</p>'}</section>`;
    }
    $('#days').innerHTML = html;
  }
  function initPlan() {
    $('#planner').onsubmit = e => {
      e.preventDefault();
      const slug = $('#planDest').value, list = plan();
      if (list.some(x => x.slug === slug)) return toast('Destinasi ini sudah ada di rencana');
      list.push({ slug, day: +$('#planDay').value }); store.set('jj_plan', list); renderPlan();
    };
    $('#days').onclick = e => { const b = e.target.closest('[data-rm]'); if (b) { store.set('jj_plan', plan().filter(x => x.slug !== b.dataset.rm)); renderPlan(); } };
    $('#clearPlan').onclick = () => { if (confirm('Kosongkan seluruh rencana?')) { store.set('jj_plan', []); renderPlan(); } };
    loadPlan();
  }

  syncFav();
  if (page === 'home') loadHome();
  if (page === 'destinations') initDest();
  if (page === 'favorites') loadFavorites();
  if (page === 'itinerary') initPlan();
})();
