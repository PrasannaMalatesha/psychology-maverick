/* ============================================================================
   MindMarket — Shared application state (the thing that makes it an app)

   One source of truth across every screen, persisted in localStorage:
     · profile   — who is signed in (name, email, joined)   → shell, account, assistant
     · settings  — preferences that actually take effect      → settings ⇄ assistant
     · enquiries — what the user has asked                     → assistant → history, account

   window.MMStore is available on every page that includes this file BEFORE its
   own script. Reads are safe if storage is blocked (private mode) — they fall
   back to in-memory defaults so the prototype never breaks.
   ============================================================================ */
(function () {
  var KEY = 'pm.v1';
  var mem = null; // in-memory fallback when localStorage is unavailable

  var DEFAULTS = {
    profile: { name: 'Reader', email: 'reader@example.com', joined: 'Aug 2026' },
    settings: {
      theme: 'system', textsize: 'm', reducemotion: false,
      length: 'standard', register: 'auto', citations: true,
      region: 'us', disclaimer: true, updates: false, digest: false, savehistory: true
    },
    saved: [],
    // seeded so history / account are not empty on first run; the assistant
    // appends to this list as the user asks.
    enquiries: seed()
  };

  function daysAgo(n) { return Date.now() - n * 86400000; }
  function seed() {
    return [
      { id: 'e1', q: 'What is the difference between classical and operant conditioning?', ts: daysAgo(0), category: 'Cognitive', register: 'Textbook', sources: 2 },
      { id: 'e2', q: 'What are the common signs of generalized anxiety?', ts: daysAgo(0), category: 'Clinical', register: 'NIMH', sources: 1 },
      { id: 'e3', q: 'What is cognitive dissonance?', ts: daysAgo(1), category: 'Social', register: 'Textbook', sources: 1 },
      { id: 'e4', q: 'How does sleep affect memory consolidation?', ts: daysAgo(1), category: 'Cognitive', register: 'Textbook', sources: 1 },
      { id: 'e5', q: 'What does the research say about exposure therapy?', ts: daysAgo(3), category: 'Clinical', register: 'NIMH', sources: 2 },
      { id: 'e6', q: 'What is the bystander effect?', ts: daysAgo(4), category: 'Social', register: 'Textbook', sources: 1 }
    ];
  }

  function load() {
    if (mem) return mem;
    var data;
    try { data = JSON.parse(localStorage.getItem(KEY)); } catch (e) { data = null; }
    if (!data) data = JSON.parse(JSON.stringify(DEFAULTS));
    // shallow-fill any missing top-level keys (forward-compat)
    for (var k in DEFAULTS) if (!(k in data)) data[k] = DEFAULTS[k];
    for (var s in DEFAULTS.settings) if (!(s in data.settings)) data.settings[s] = DEFAULTS.settings[s];
    mem = data;
    return data;
  }
  function persist() {
    try { localStorage.setItem(KEY, JSON.stringify(mem)); } catch (e) {}
  }

  var TEXT_SCALE = { s: 0.92, m: 1, l: 1.14 };

  var API = {
    // ---- profile ----
    profile: function () { return load().profile; },
    initial: function () { return (load().profile.name || 'R').trim().charAt(0).toUpperCase() || 'R'; },
    setProfile: function (patch) { var d = load(); Object.assign(d.profile, patch); persist(); },

    // ---- settings ----
    settings: function () { return load().settings; },
    setSetting: function (k, v) { var d = load(); d.settings[k] = v; persist(); this.applySettings(); },

    // apply preference side-effects to the live document (reading size + motion)
    applySettings: function (doc) {
      var root = (doc || document).documentElement;
      var s = load().settings;
      root.style.setProperty('--read-scale', TEXT_SCALE[s.textsize] || 1);
      root.setAttribute('data-reduce-motion', s.reducemotion ? '1' : '0');
    },

    // ---- enquiries ----
    enquiries: function () { return load().enquiries.slice().sort(function (a, b) { return b.ts - a.ts; }); },
    addEnquiry: function (q, meta) {
      var d = load();
      if (!d.settings.savehistory) return null;
      var e = { id: 'e' + Date.now(), q: q, ts: Date.now(), category: (meta && meta.category) || 'General', register: (meta && meta.register) || '—', sources: (meta && meta.sources) || 0 };
      d.enquiries.push(e); persist(); return e;
    },
    clearEnquiries: function () { var d = load(); d.enquiries = []; d.saved = []; persist(); },

    // ---- saved answers ----
    saved: function () { return load().saved; },
    toggleSaved: function (id) {
      var d = load(), i = d.saved.indexOf(id);
      if (i >= 0) d.saved.splice(i, 1); else d.saved.push(id);
      persist(); return i < 0;
    },

    // ---- derived ----
    stats: function () { var d = load(); return { enquiries: d.enquiries.length, saved: d.saved.length, sources: 36 }; },

    // export everything (for Settings → Export)
    dump: function () { return JSON.stringify(load(), null, 2); },
    reset: function () { mem = JSON.parse(JSON.stringify(DEFAULTS)); persist(); }
  };

  window.MMStore = API;
  // apply reading-size + motion prefs as early as possible to avoid a flash
  try { API.applySettings(); } catch (e) {}
})();
