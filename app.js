(() => {
  const dataNode = document.getElementById('jobs-data');
  const jobsContainer = document.getElementById('jobsContainer');
  if (!dataNode || !jobsContainer) return;

  let allJobs = [];
  try {
    allJobs = JSON.parse(dataNode.textContent);
    if (!Array.isArray(allJobs)) throw new TypeError('El archivo de convocatorias no tiene el formato esperado.');
  } catch (error) {
    jobsContainer.innerHTML = '<p class="empty-state"><strong>No pudimos cargar las convocatorias.</strong><span>Recarga la página para intentarlo de nuevo.</span></p>';
    document.getElementById('resultsCount').textContent = 'No se pudieron cargar las oportunidades.';
    console.error('Error al leer las convocatorias:', error);
    return;
  }

  const appliedStorageKey = 'ipf-applied-jobs-v1';
  let appliedJobs = new Set();
  try {
    const storedJobs = JSON.parse(localStorage.getItem(appliedStorageKey) || '[]');
    if (Array.isArray(storedJobs)) appliedJobs = new Set(storedJobs.filter((url) => typeof url === 'string'));
  } catch { /* El portal funciona aunque el navegador bloquee el almacenamiento local. */ }

  let currentTab = 'todas';
  let currentBranch = 'TODOS';
  const searchInput = document.getElementById('searchInput');
  const applicationFilter = document.getElementById('applicationFilter');
  const resultsCount = document.getElementById('resultsCount');
  const applicationSummary = document.getElementById('applicationSummary');
  const jobsPanel = document.getElementById('jobsPanel');
  const guidePanel = document.getElementById('guidePanel');

  const normalize = (value) => String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('es');
  const text = (tag, className, content) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (content !== undefined) node.textContent = content;
    return node;
  };

  function makeJobCard(job) {
    const card = text('article', 'job-card');
    if (job.es_cierre_inminente) card.classList.add('urgent');
    if (job.es_exclusiva_fisica) card.classList.add('exclusive');
    const accent = /^#[\da-f]{3,8}$/i.test(job.color_principal || '') ? job.color_principal : '#176f68';
    card.style.setProperty('--job-accent', accent);

    const top = text('div', 'job-card-top');
    const badgeCopy = job.es_cierre_inminente ? 'Cierre próximo' : job.es_exclusiva_fisica ? 'Afinidad física' : job.afinidad || 'Oportunidad';
    top.append(text('span', `affinity-badge${job.es_cierre_inminente ? ' badge-urgent' : job.es_exclusiva_fisica ? ' badge-exclusive' : ''}`, badgeCopy));
    const date = text('span', 'job-date', job.fecha_publicacion || 'Convocatoria activa');
    top.append(date);
    card.append(top);

    card.append(text('h3', 'job-title', job.titulo || 'Oportunidad de práctica'));
    card.append(text('p', 'job-company', job.empresa || 'Empresa por confirmar'));

    const specs = text('div', 'job-specs');
    const location = text('span', 'job-spec');
    location.append(text('span', 'spec-mark', '↗'), document.createTextNode(job.ubicacion || 'Antioquia'));
    const source = text('span', 'job-spec');
    source.append(text('span', 'spec-mark', '◎'), document.createTextNode(job.fuente || 'Portal de empleo'));
    specs.append(location, source);
    card.append(specs);

    if (job.compensacion) {
      const pay = text('p', 'job-compensation');
      pay.append(text('span', 'compensation-mark', '＋'), document.createTextNode(job.compensacion));
      card.append(pay);
    }

    const tags = text('div', 'job-tags');
    (Array.isArray(job.ramas) ? job.ramas : []).forEach((branch) => {
      tags.append(text('span', 'job-tag', branch.nombre || 'Ingeniería física'));
    });
    card.append(tags);

    const detail = document.createElement('details');
    detail.className = 'job-detail';
    const summary = document.createElement('summary');
    summary.append(document.createTextNode('Ver encaje técnico '), text('span', 'detail-chevron', '＋'));
    detail.append(summary);
    const detailBody = text('div', 'job-detail-body');
    if (job.mision) {
      detailBody.append(text('span', 'detail-label', 'EL RETO'), text('p', 'detail-copy', job.mision));
    }
    if (job.perfil) {
      detailBody.append(text('span', 'detail-label', 'PERFIL'), text('p', 'detail-copy', job.perfil));
    }
    if (job.tareas) {
      detailBody.append(text('span', 'detail-label', 'EN QUÉ TRABAJARÍAS'), text('p', 'detail-copy', job.tareas));
    }
    detail.append(detailBody);
    card.append(detail);

    const footer = text('footer', 'job-card-footer');
    let targetUrl = '';
    try {
      const parsedUrl = new URL(job.url);
      if (parsedUrl.protocol === 'https:' || parsedUrl.protocol === 'http:') targetUrl = parsedUrl.href;
    } catch { /* Una oferta sin URL válida conserva el resto de su información. */ }
    if (targetUrl) {
      const applyLink = text('a', 'apply-link', 'Ver convocatoria');
      applyLink.href = targetUrl;
      applyLink.target = '_blank';
      applyLink.rel = 'noopener noreferrer';
      applyLink.append(text('span', 'apply-arrow', '↗'));
      footer.append(applyLink);
    } else {
      footer.append(text('span', 'apply-unavailable', 'Enlace de convocatoria no disponible'));
    }
    const isApplied = appliedJobs.has(job.url);
    const appliedButton = text('button', `application-toggle${isApplied ? ' is-applied' : ''}`, isApplied ? '✓  Ya me postulé' : 'Marcar como postulada');
    appliedButton.type = 'button';
    appliedButton.setAttribute('aria-pressed', String(isApplied));
    appliedButton.addEventListener('click', () => toggleApplied(job.url));
    footer.append(appliedButton);
    card.append(footer);
    return card;
  }

  function renderJobs(jobs) {
    jobsContainer.replaceChildren();
    if (!jobs.length) {
      const empty = text('div', 'empty-state');
      empty.append(text('span', 'empty-illustration', '∅'), text('h3', '', 'No encontramos coincidencias.'), text('p', '', 'Prueba otra búsqueda o quita alguno de los filtros.'), text('button', 'clear-filters', 'Limpiar filtros'));
      empty.querySelector('button').type = 'button';
      empty.querySelector('button').addEventListener('click', clearFilters);
      jobsContainer.append(empty);
      return;
    }
    const fragment = document.createDocumentFragment();
    jobs.forEach((job) => fragment.append(makeJobCard(job)));
    jobsContainer.append(fragment);
  }

  function handleFilter() {
    const query = normalize(searchInput.value.trim());
    const applicationState = applicationFilter.value;
    const appliedCount = allJobs.filter((job) => appliedJobs.has(job.url)).length;
    applicationSummary.textContent = `${appliedCount} postuladas · ${Math.max(allJobs.length - appliedCount, 0)} pendientes`;

    const filtered = allJobs.filter((job) => {
      if (currentTab === 'exclusivas' && !job.es_exclusiva_fisica) return false;
      if (currentTab === 'inminentes' && !job.es_cierre_inminente) return false;
      if (applicationState === 'pending' && appliedJobs.has(job.url)) return false;
      if (applicationState === 'applied' && !appliedJobs.has(job.url)) return false;
      const branches = Array.isArray(job.ramas) ? job.ramas : [];
      if (currentBranch !== 'TODOS' && !branches.some((branch) => branch.nombre === currentBranch)) return false;
      if (!query) return true;
      const searchable = [job.titulo, job.empresa, job.ubicacion, job.mision, job.tareas, job.perfil, job.compensacion, job.fuente, ...branches.map((branch) => branch.nombre)];
      return searchable.some((value) => normalize(value).includes(query));
    });

    resultsCount.textContent = `${filtered.length} ${filtered.length === 1 ? 'oportunidad encontrada' : 'oportunidades encontradas'}`;
    renderJobs(filtered);
  }

  function toggleApplied(url) {
    if (appliedJobs.has(url)) appliedJobs.delete(url);
    else appliedJobs.add(url);
    try { localStorage.setItem(appliedStorageKey, JSON.stringify([...appliedJobs])); } catch { /* El estado sigue disponible durante esta sesión. */ }
    handleFilter();
  }

  function clearFilters() {
    searchInput.value = '';
    applicationFilter.value = 'all';
    currentBranch = 'TODOS';
    document.querySelectorAll('.branch-pill').forEach((pill) => {
      const active = pill.dataset.branch === 'TODOS';
      pill.classList.toggle('active', active);
      pill.setAttribute('aria-pressed', String(active));
    });
    if (currentTab !== 'todas') activateTab('todas');
    handleFilter();
    searchInput.focus();
  }

  function activateTab(tabId, focus = false) {
    const tab = document.querySelector(`[data-tab="${tabId}"]`);
    if (!tab) return;
    currentTab = tabId;
    document.querySelectorAll('[role="tab"]').forEach((button) => {
      const selected = button === tab;
      button.classList.toggle('active', selected);
      button.setAttribute('aria-selected', String(selected));
      button.tabIndex = selected ? 0 : -1;
    });
    const isGuide = tabId === 'consejos';
    jobsPanel.hidden = isGuide;
    guidePanel.hidden = !isGuide;
    if (focus) tab.focus();
    if (!isGuide) handleFilter();
  }

  document.querySelectorAll('[data-tab]').forEach((tab) => tab.addEventListener('click', () => activateTab(tab.dataset.tab)));
  document.querySelector('.tabs-nav').addEventListener('keydown', (event) => {
    const tabs = [...document.querySelectorAll('[role="tab"]')];
    const activeIndex = tabs.indexOf(document.activeElement);
    if (activeIndex < 0) return;
    let nextIndex = activeIndex;
    if (event.key === 'ArrowRight') nextIndex = (activeIndex + 1) % tabs.length;
    else if (event.key === 'ArrowLeft') nextIndex = (activeIndex - 1 + tabs.length) % tabs.length;
    else if (event.key === 'Home') nextIndex = 0;
    else if (event.key === 'End') nextIndex = tabs.length - 1;
    else return;
    event.preventDefault();
    activateTab(tabs[nextIndex].dataset.tab, true);
  });
  document.querySelectorAll('.branch-pill').forEach((pill) => pill.addEventListener('click', () => {
    currentBranch = pill.dataset.branch;
    document.querySelectorAll('.branch-pill').forEach((item) => {
      const selected = item === pill;
      item.classList.toggle('active', selected);
      item.setAttribute('aria-pressed', String(selected));
    });
    handleFilter();
  }));
  searchInput.addEventListener('input', handleFilter);
  applicationFilter.addEventListener('change', handleFilter);
  document.querySelectorAll('[data-open-guide]').forEach((button) => button.addEventListener('click', () => {
    activateTab('consejos');
    document.getElementById('section-title').scrollIntoView({ behavior: 'smooth', block: 'start' });
    guidePanel.focus({ preventScroll: true });
  }));
  document.querySelector('[data-back-to-jobs]').addEventListener('click', () => {
    activateTab('todas');
    document.getElementById('section-title').scrollIntoView({ behavior: 'smooth', block: 'start' });
    searchInput.focus({ preventScroll: true });
  });

  const themeToggle = document.getElementById('themeToggle');
  function setTheme(theme) {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem('ipf-theme', theme); } catch { /* Tema de la sesión sin persistencia. */ }
    const isDark = theme === 'dark';
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', isDark ? '#101a19' : '#f5f4ee');
    themeToggle.setAttribute('aria-pressed', String(isDark));
    themeToggle.querySelector('.theme-label').textContent = isDark ? 'Tema claro' : 'Tema oscuro';
    themeToggle.querySelector('.theme-icon').textContent = isDark ? '☼' : '◐';
  }
  themeToggle.addEventListener('click', () => setTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'));

  document.addEventListener('keydown', (event) => {
    if (event.key === '/' && !event.metaKey && !event.ctrlKey && !event.altKey && !event.target.matches('input, textarea, select, [contenteditable="true"]')) {
      event.preventDefault();
      searchInput.focus();
    }
  });

  document.getElementById('activeCount').textContent = allJobs.length;
  document.getElementById('exclusiveCount').textContent = allJobs.filter((job) => job.es_exclusiva_fisica).length;
  document.getElementById('urgentCount').textContent = allJobs.filter((job) => job.es_cierre_inminente).length;
  handleFilter();
  setTheme(document.documentElement.dataset.theme || 'light');
})();
