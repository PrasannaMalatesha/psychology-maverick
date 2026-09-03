/* ============================================================================
   MindMarket — Icon System (single source of truth for iconography)

   One coherent stroke set on a 24×24 grid, 1.8 stroke, round caps + joins.
   Geometry only lives here; colour/size/stroke come from CSS on the host:
       .ic { width:1em; height:1em; fill:none; stroke:currentColor;
             stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round }

   USAGE  (self-contained, works over file:// where external <use> is blocked):
     Load icons.js as the first script in <body>, then reference by id:
     <svg class="ic"><use href="#ic-heart"/></svg>

   The two icons the previous prototype drew by hand — heart and settings —
   were off-grid and lopsided; they are replaced here with correct, symmetric
   geometry (Lucide-derived) so they read cleanly at every size.
   ============================================================================ */
(function () {
  var S = {
    /* brand + nav */
    'ic-logo':        '<path d="M4 5.5A1.5 1.5 0 0 1 5.5 4H12v16H5.5A1.5 1.5 0 0 1 4 18.5z"/><path d="M12 4h6.5A1.5 1.5 0 0 1 20 5.5v13a1.5 1.5 0 0 1-1.5 1.5H12"/>',
    'ic-menu':        '<path d="M4 6h16M4 12h16M4 18h16"/>',
    'ic-x':           '<path d="M18 6 6 18M6 6l12 12"/>',
    'ic-plus':        '<path d="M12 5v14M5 12h14"/>',
    'ic-plus-circle': '<circle cx="12" cy="12" r="9"/><path d="M12 8v8M8 12h8"/>',
    'ic-check':       '<path d="M20 6 9 17l-5-5"/>',
    'ic-check-circle':'<circle cx="12" cy="12" r="9"/><path d="m8.4 12 2.4 2.4 4.8-4.8"/>',
    'ic-search':      '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    'ic-filter':      '<path d="M22 3H2l8 9.5V19l4 2v-8.5z"/>',
    'ic-more':        '<circle cx="12" cy="5" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="12" cy="19" r="1.3"/>',

    /* arrows + chevrons */
    'ic-arrow-right': '<path d="M5 12h14M13 6l6 6-6 6"/>',
    'ic-arrow-left':  '<path d="M19 12H5M11 18l-6-6 6-6"/>',
    'ic-arrow-up-right':'<path d="M7 17 17 7"/><path d="M7 7h10v10"/>',
    'ic-chevron-right':'<path d="m9 6 6 6-6 6"/>',
    'ic-chevron-left':'<path d="m15 6-6 6 6 6"/>',
    'ic-chevron-down':'<path d="m6 9 6 6 6-6"/>',
    'ic-chevron-up':  '<path d="m18 15-6-6-6 6"/>',

    /* people + account */
    'ic-user':        '<circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 4-6 8-6s8 2 8 6"/>',
    'ic-users':       '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c0-3.4 3-5 6.5-5s6.5 1.6 6.5 5"/><path d="M16 5.2a3.5 3.5 0 0 1 0 6.6"/><path d="M18 14.7c2.4.5 3.5 2 3.5 5.3"/>',
    'ic-log-out':     '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/>',
    'ic-key':         '<circle cx="8" cy="15" r="4"/><path d="M10.8 12.2 21 2"/><path d="m18 5 3 3"/><path d="m14.5 8.5 3 3"/>',

    /* settings + preferences  (FIXED gear) */
    'ic-settings':    '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
    'ic-sliders':     '<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"/>',
    'ic-bell':        '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/>',
    'ic-moon':        '<path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"/>',
    'ic-sun':         '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    'ic-eye':         '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/>',
    'ic-eye-off':     '<path d="M9.9 4.24A9.1 9.1 0 0 1 12 4c6.5 0 10 8 10 8a13.2 13.2 0 0 1-2.2 3.1"/><path d="M6.1 6.1A13.2 13.2 0 0 0 2 12s3.5 8 10 8a9.1 9.1 0 0 0 4-.9"/><path d="M9.5 9.5a3 3 0 0 0 4.2 4.2"/><path d="M2 2l20 20"/>',

    /* content + knowledge */
    'ic-heart':       '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.29 1.5 4.04 3 5.5l7 7z"/>',
    'ic-shield':      '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    'ic-shield-check':'<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
    'ic-info':        '<circle cx="12" cy="12" r="9"/><path d="M12 11v5"/><path d="M12 8h.01"/>',
    'ic-alert-triangle':'<path d="M10.3 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.7 3.86a2 2 0 0 0-3.4 0z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    'ic-book-open':   '<path d="M2 4h6a4 4 0 0 1 4 4v12a3 3 0 0 0-3-3H2z"/><path d="M22 4h-6a4 4 0 0 0-4 4v12a3 3 0 0 1 3-3h7z"/>',
    'ic-database':    '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.66 3.58 3 8 3s8-1.34 8-3V5"/><path d="M4 12c0 1.66 3.58 3 8 3s8-1.34 8-3"/>',
    'ic-message':     '<path d="M21 11.5a8.4 8.4 0 0 1-9 8.4 9 9 0 0 1-3.7-.7L3 21l1.3-4a8.4 8.4 0 0 1-.8-3.6A8.5 8.5 0 0 1 12 4a8.5 8.5 0 0 1 9 7.5z"/>',
    'ic-clock':       '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/>',
    'ic-star':        '<path d="M12 3l2.7 5.5 6 .9-4.4 4.2 1 6L12 17.8 6.7 19.6l1-6L3.3 9.4l6-.9z"/>',
    'ic-sparkle':     '<path d="M12 3l1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7z"/><path d="M19 15l.6 1.9 1.9.6-1.9.6-.6 1.9-.6-1.9-1.9-.6 1.9-.6z"/>',

    /* actions + io */
    'ic-send':        '<path d="M5 12h13M13 6l6 6-6 6"/>',
    'ic-download':    '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/>',
    'ic-trash':       '<path d="M3 6h18"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="m19 6-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/>',
    'ic-edit':        '<path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4z"/>',
    'ic-copy':        '<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
    'ic-external':    '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
    'ic-lock':        '<rect x="3" y="11" width="18" height="10" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    'ic-mail':        '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 6-10 7L2 6"/>',
    'ic-globe':       '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a14 14 0 0 1 0 18 14 14 0 0 1 0-18z"/>'
  };

  var parts = '<svg aria-hidden="true" focusable="false" width="0" height="0" style="position:absolute;width:0;height:0;overflow:hidden" data-mm-icons>';
  for (var id in S) {
    parts += '<symbol id="' + id + '" viewBox="0 0 24 24">' + S[id] + '</symbol>';
  }
  parts += '</svg>';

  function inject() {
    if (document.querySelector('svg[data-mm-icons]')) return;
    document.body.insertAdjacentHTML('afterbegin', parts);
  }
  if (document.body) inject();
  else document.addEventListener('DOMContentLoaded', inject);
})();
