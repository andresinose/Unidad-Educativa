
(() => {
  'use strict';
  const pages = [...document.querySelectorAll('.page-card')];
  const total = pages.length;
  const pageInput = document.getElementById('pageNumber');
  const prevBtn = document.getElementById('prevPage');
  const nextBtn = document.getElementById('nextPage');
  const progressBar = document.getElementById('progressBar');
  const progressText = document.getElementById('progressText');
  const root = document.documentElement;
  const body = document.body;
  let currentPage = 1;
  let pageWidth = Math.min(920, Math.max(520, window.innerWidth - 330));

  const clamp = (value, min, max) => Math.min(Math.max(value, min), max);
  const goToPage = (number) => {
    const target = clamp(Number(number) || 1, 1, total);
    document.getElementById(`page-${target}`)?.scrollIntoView({behavior: 'smooth', block: 'start'});
  };
  const setCurrent = (number) => {
    currentPage = clamp(number, 1, total);
    pageInput.value = currentPage;
    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = currentPage === total;
    document.querySelectorAll('.page-link.active').forEach(x => x.classList.remove('active'));
    document.querySelector(`.page-link[data-page="${currentPage}"]`)?.classList.add('active');
    pages.forEach(p => p.classList.toggle('current', Number(p.dataset.page) === currentPage));
    const pct = Math.round((currentPage / total) * 100);
    progressBar.style.width = `${pct}%`;
    progressText.textContent = `${pct}%`;
    history.replaceState(null, '', `#page-${currentPage}`);
  };

  prevBtn.addEventListener('click', () => goToPage(currentPage - 1));
  nextBtn.addEventListener('click', () => goToPage(currentPage + 1));
  pageInput.addEventListener('change', e => goToPage(e.target.value));
  pageInput.addEventListener('keydown', e => { if (e.key === 'Enter') goToPage(e.target.value); });
  document.querySelectorAll('[data-go-page]').forEach(btn => btn.addEventListener('click', () => {
    goToPage(btn.dataset.goPage);
    body.classList.remove('sidebar-open');
  }));

  const observer = new IntersectionObserver(entries => {
    const visible = entries.filter(e => e.isIntersecting).sort((a,b) => b.intersectionRatio - a.intersectionRatio);
    if (visible[0]) setCurrent(Number(visible[0].target.dataset.page));
  }, { rootMargin: '-20% 0px -60% 0px', threshold: [0.05, 0.25, 0.5] });
  pages.forEach(p => observer.observe(p));

  document.getElementById('menuToggle').addEventListener('click', () => {
    if (window.matchMedia('(max-width: 980px)').matches) body.classList.toggle('sidebar-open');
    else body.classList.toggle('sidebar-closed');
  });
  document.getElementById('closeSidebar').addEventListener('click', () => body.classList.remove('sidebar-open'));

  const applyWidth = () => root.style.setProperty('--page-width', `${pageWidth}px`);
  document.getElementById('zoomIn').addEventListener('click', () => { pageWidth = clamp(pageWidth + 90, 420, 1500); applyWidth(); });
  document.getElementById('zoomOut').addEventListener('click', () => { pageWidth = clamp(pageWidth - 90, 420, 1500); applyWidth(); });
  document.getElementById('fitWidth').addEventListener('click', () => {
    const sidebar = (!window.matchMedia('(max-width: 980px)').matches && !body.classList.contains('sidebar-closed')) ? 315 : 45;
    pageWidth = clamp(window.innerWidth - sidebar, 420, 1100); applyWidth();
  });
  document.getElementById('printDoc').addEventListener('click', () => window.print());
  document.getElementById('fullscreen').addEventListener('click', async () => {
    try {
      if (!document.fullscreenElement) await document.documentElement.requestFullscreen();
      else await document.exitFullscreen();
    } catch (_) {}
  });

  // Student notes and completion status are stored only in this browser.
  document.querySelectorAll('[data-note-page]').forEach(area => {
    const key = `uei-math8-note-${area.dataset.notePage}`;
    area.value = localStorage.getItem(key) || '';
    area.addEventListener('input', () => localStorage.setItem(key, area.value));
  });
  document.querySelectorAll('[data-complete-page]').forEach(box => {
    const key = `uei-math8-complete-${box.dataset.completePage}`;
    box.checked = localStorage.getItem(key) === '1';
    box.addEventListener('change', () => {
      localStorage.setItem(key, box.checked ? '1' : '0');
      updateCompletion();
    });
  });
  document.querySelectorAll('[data-clear-note]').forEach(btn => btn.addEventListener('click', () => {
    const p = btn.dataset.clearNote;
    const area = document.querySelector(`[data-note-page="${p}"]`);
    if (area && confirm('¿Borrar las respuestas y notas de esta página?')) {
      area.value = ''; localStorage.removeItem(`uei-math8-note-${p}`);
    }
  }));
  const updateCompletion = () => {
    const done = document.querySelectorAll('[data-complete-page]:checked').length;
    document.getElementById('completionCount').textContent = `${done} de ${total} páginas marcadas`;
  };
  updateCompletion();

  document.getElementById('clearAll').addEventListener('click', () => {
    if (!confirm('¿Borrar todas las notas y marcas de progreso guardadas en este navegador?')) return;
    for (let i=1; i<=total; i++) {
      localStorage.removeItem(`uei-math8-note-${i}`);
      localStorage.removeItem(`uei-math8-complete-${i}`);
    }
    document.querySelectorAll('[data-note-page]').forEach(x => x.value = '');
    document.querySelectorAll('[data-complete-page]').forEach(x => x.checked = false);
    updateCompletion();
  });

  const normalize = s => s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const search = document.getElementById('searchText');
  const results = document.getElementById('searchResults');
  search.addEventListener('input', () => {
    const q = normalize(search.value.trim());
    results.innerHTML = '';
    if (q.length < 3) return;
    const matches = pages.filter(p => normalize(p.querySelector('.sr-page-text')?.textContent || '').includes(q)).slice(0, 18);
    matches.forEach(p => {
      const b = document.createElement('button');
      b.className = 'search-result'; b.type = 'button';
      b.textContent = `Página ${p.dataset.page}: ${p.dataset.title}`;
      b.addEventListener('click', () => { goToPage(p.dataset.page); body.classList.remove('sidebar-open'); });
      results.appendChild(b);
    });
    if (!matches.length) {
      const msg = document.createElement('div'); msg.className = 'search-result'; msg.textContent = 'Sin coincidencias'; results.appendChild(msg);
    }
  });

  document.addEventListener('keydown', e => {
    if (['INPUT','TEXTAREA'].includes(document.activeElement.tagName)) return;
    if (e.key === 'ArrowRight' || e.key === 'PageDown') { e.preventDefault(); goToPage(currentPage + 1); }
    if (e.key === 'ArrowLeft' || e.key === 'PageUp') { e.preventDefault(); goToPage(currentPage - 1); }
    if (e.key === 'Home') { e.preventDefault(); goToPage(1); }
    if (e.key === 'End') { e.preventDefault(); goToPage(total); }
  });

  applyWidth();
  const hashMatch = location.hash.match(/page-(\d+)/);
  if (hashMatch) setTimeout(() => goToPage(hashMatch[1]), 250);
  else setCurrent(1);
})();
