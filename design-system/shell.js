/* ============================================================================
   MindMarket — App shell renderer
   Injects the identical rail (brand · nav · account menu) into every signed-in
   screen so navigation, iconography and account controls never drift.

   USAGE:
     <body data-page="settings">                       ← active nav key
       <div class="app"><main class="main">…</main></div>
       <script src="../../design-system/icons.js"></script>
       <script src="../../design-system/shell.js"></script>
   Optional: window.MM_USER = { name:'Reader', initial:'R', plan:'Signed in' }
   Exposes: window.MM.toast(message)
   ============================================================================ */
(function () {
  /* Idempotency guard: never mount the rail twice, even if this script is
     included more than once (a stale inline copy + the built one, an external
     re-include, etc.). The first run wins; later runs bail. */
  var appGuard = document.querySelector('.app');
  if (window.__mmShellMounted || (appGuard && appGuard.querySelector(':scope > .rail'))) return;
  window.__mmShellMounted = true;

  var p = (window.MMStore && MMStore.profile) ? MMStore.profile() : null;
  var user = {
    name: p ? p.name : 'Reader',
    initial: (window.MMStore && MMStore.initial) ? MMStore.initial() : 'R',
    plan: 'Signed in'
  };
  var page = document.body.getAttribute('data-page') || '';

  var NAV = [
    { key: 'assistant', label: 'Assistant', href: 'assistant.html', icon: 'ic-message' },
    { key: 'library',   label: 'Library',   href: 'library.html',   icon: 'ic-book-open' },
    { key: 'history',   label: 'History',   href: 'history.html',   icon: 'ic-clock' }
  ];
  var NAV2 = [
    { key: 'account',   label: 'Account',   href: 'account.html',   icon: 'ic-user' },
    { key: 'settings',  label: 'Settings',  href: 'settings.html',  icon: 'ic-settings' }
  ];

  function svg(id) { return '<svg class="ic"><use href="#' + id + '"/></svg>'; }
  function link(n) {
    var cur = n.key === page ? ' aria-current="page"' : '';
    return '<a class="rail-link" href="' + n.href + '"' + cur + '>' + svg(n.icon) + '<span>' + n.label + '</span></a>';
  }

  var railHTML =
    '<aside class="rail" aria-label="Primary">' +
      '<a class="brand" href="assistant.html" aria-label="Psychology Maverick — home">' +
        '<span class="mk" aria-hidden="true">' + svg('ic-logo') + '</span>' +
        '<span>Psychology Maverick<span class="sub">Grounded &amp; cited</span></span>' +
      '</a>' +
      '<a class="btn btn-primary" href="assistant.html" style="margin:2px 16px 12px;justify-content:center">' + svg('ic-plus') + 'New enquiry</a>' +
      '<nav class="rail-nav" aria-label="Sections">' +
        NAV.map(link).join('') +
        '<div class="rail-group">Your account</div>' +
        NAV2.map(link).join('') +
      '</nav>' +
      '<div class="rail-foot">' +
        '<div class="menu" id="acctMenu" role="menu" aria-label="Account">' +
          '<a role="menuitem" href="account.html">' + svg('ic-user') + 'Account</a>' +
          '<a role="menuitem" href="settings.html">' + svg('ic-settings') + 'Settings</a>' +
          '<div class="sep"></div>' +
          '<a role="menuitem" class="danger" href="auth.html">' + svg('ic-log-out') + 'Sign out</a>' +
        '</div>' +
        '<button class="account" id="acctBtn" aria-haspopup="menu" aria-expanded="false">' +
          '<span class="avatar">' + user.initial + '</span>' +
          '<span class="who">' + user.name + '<span>' + user.plan + '</span></span>' +
          '<span class="caret" aria-hidden="true">' + svg('ic-chevron-up') + '</span>' +
        '</button>' +
      '</div>' +
    '</aside>';

  var app = document.querySelector('.app');
  if (app) {
    app.insertAdjacentHTML('afterbegin', railHTML);
    app.insertAdjacentHTML('afterbegin', '<div class="scrim" id="scrim"></div>');
  }

  /* toast */
  var toastEl = document.createElement('div');
  toastEl.className = 'toast'; toastEl.setAttribute('role', 'status'); toastEl.setAttribute('aria-live', 'polite');
  document.body.appendChild(toastEl);
  var toastT;
  function toast(msg, icon) {
    toastEl.innerHTML = (icon ? svg(icon) : svg('ic-check-circle')) + '<span>' + msg + '</span>';
    toastEl.classList.add('show'); clearTimeout(toastT);
    toastT = setTimeout(function () { toastEl.classList.remove('show'); }, 2400);
  }
  window.MM = { toast: toast };

  /* account menu */
  var acctBtn = document.getElementById('acctBtn'), acctMenu = document.getElementById('acctMenu');
  function closeMenu() { if (!acctMenu) return; acctMenu.classList.remove('open'); acctBtn.setAttribute('aria-expanded', 'false'); }
  if (acctBtn) {
    acctBtn.addEventListener('click', function (e) { e.stopPropagation(); var o = acctMenu.classList.toggle('open'); acctBtn.setAttribute('aria-expanded', o ? 'true' : 'false'); });
    document.addEventListener('click', function (e) { if (acctMenu && !acctMenu.contains(e.target) && e.target !== acctBtn && !acctBtn.contains(e.target)) closeMenu(); });
  }

  /* mobile drawer */
  var appEl = document.querySelector('.app'), scrim = document.getElementById('scrim');
  var menuBtn = document.getElementById('menuBtn');
  if (menuBtn) menuBtn.addEventListener('click', function () { appEl.classList.add('nav-open'); });
  if (scrim) scrim.addEventListener('click', function () { appEl.classList.remove('nav-open'); });

  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    if (acctMenu && acctMenu.classList.contains('open')) { closeMenu(); acctBtn.focus(); return; }
    if (appEl && appEl.classList.contains('nav-open')) appEl.classList.remove('nav-open');
  });
})();
