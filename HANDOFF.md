# HANDOFF — Psychology Maverick

Read this first to resume. It captures exactly where the project stands, how to run/view what
exists, every decision made, and the ordered next steps. **Last updated after a senior-designer
UI/UX pass** that (a) chose a direction — **"calm & credible" evolution** of MindMarket — over the
prior "elevate the warm world" framing, (b) found and fixed **three corruption-class bugs** that were
the bulk of the "messy" (a double-rendered rail on all 4 manage screens; `icons.js` source leaking as
visible page text on 7 pages; landing reveal animations never firing so the hero rendered invisible),
and (c) applied targeted calm-credible polish (assistant state-badge, coral discipline, semantic hub
tiles). Plan of record: **[docs/ux/redesign-plan.md](docs/ux/redesign-plan.md)**. See §9A for this
session's full delta; §10–§11 keep the earlier logs. e2e **46/46** throughout.

---

## 1. What this is (in one paragraph)

**Psychology Maverick** is a retrieval-grounded AI assistant that answers questions about
**psychology, psychiatry, and mental health** strictly from a curated, openly-licensed corpus,
**citing every claim**. Dual purpose: a *learning* tool and a *clarity* tool for mental health.
**Informational only, never diagnosis**, and **crisis-first** (a query signalling crisis gets
support resources, never a corpus answer). Built as a portfolio-grade production system: the LLM is
a small part; the engineering around it is the point.

- **App name:** Psychology Maverick (earlier working name "Casebook" is fully removed).
- **Design system:** **MindMarket — "warm storybook, grounded receipts."** Warm cream canvas +
  grass-green structural accent + coral action + 50px pills + surface-stack elevation (no shadows),
  a real **3-font system** (**Bricolage Grotesque** display / **Inter** body / **JetBrains Mono**
  for citations & labels — the "receipts"), a dedicated **stroke icon set**, and hand-authored
  paper-cut SVG illustrations. **`DESIGN.md` is now CURRENT** (rewritten this session to match the
  3-font + icon reality; `design-system/tokens.css` is the machine-readable source of truth).
- **Chosen design direction (this session):** **elevate the current warm world** — keep the
  storybook identity, push craft (spacing rhythm, illustration warmth, motion polish, depth). The
  earlier "keep-mascot vs pivot-to-dark-editorial" question is **RESOLVED: keep + elevate.**

---

## 2. Current phase & status

**Phase: design + CONNECTED interactive prototype. Real app (Next.js/FastAPI) NOT scaffolded yet.**

| Area | Status |
|------|--------|
| Product spec, PRD, glossary, ADRs | ✅ done ([project.md](project.md), [docs/PRD.md](docs/PRD.md), [CONTEXT.md](CONTEXT.md), [docs/adr/](docs/adr/)) |
| Corpus (30 openly-licensed PDFs) | ✅ ingested + reproducible ([data/](data/)) |
| **Design system (single source of truth)** | ✅ [design-system/](design-system/) — `tokens.css` `app.css` `icons.js` `store.js` `shell.js` `build.mjs`; [DESIGN.md](DESIGN.md) now current |
| Prototype: index / hub | ✅ [design/prototype/index.html](design/prototype/index.html) — front door, maps all 11 screens, paper-cut hero, staggered reveal (NEW) |
| Prototype: landing | ✅ [landing.html](design/prototype/landing.html) — illustrations, glass nav, marquee, parallax |
| Prototype: experience (Three.js 3D) | ✅ [experience.html](design/prototype/experience.html) — interactive corpus constellation |
| Prototype: auth | ✅ [auth.html](design/prototype/auth.html) |
| Prototype: onboarding | ✅ [onboarding.html](design/prototype/onboarding.html) — 3-step first run (NEW) |
| Prototype: assistant (INTERACTIVE) | ✅ [assistant.html](design/prototype/assistant.html) — canned matcher; now writes to shared store |
| Prototype: library | ✅ [library.html](design/prototype/library.html) — corpus browser, filter + search (NEW) |
| Prototype: history | ✅ [history.html](design/prototype/history.html) — real enquiry log from the store (NEW) |
| Prototype: account | ✅ [account.html](design/prototype/account.html) — profile + live stats from the store (NEW) |
| Prototype: settings | ✅ [settings.html](design/prototype/settings.html) — prefs that actually take effect (NEW) |
| Prototype: styleguide (living system) | ✅ [styleguide.html](design/prototype/styleguide.html) — colour, type scale, icon grid, components (NEW) |
| **Shared state layer** (real-app behaviour) | ✅ `design-system/store.js` — one profile/settings/enquiry log across all screens |
| E2E tests (Playwright) | ✅ **46/46 pass** desktop + mobile ([e2e/](e2e/)) |
| **Next.js frontend/** | ❌ not scaffolded |
| **FastAPI backend/** | ❌ not scaffolded (no real RAG/LLM yet) |
| Cloud accounts (Neon/Upstash/Langfuse/Render/Vercel) | ❌ not provisioned (user task) |

**Prototypes are HTML/CSS/vanilla-JS in `design/prototype/`. The assistant's answers come from a
small CANNED matcher (`answerFor()`), not a real LLM/RAG.** That boundary is where prototype ends
and build begins.

---

## 3. How to run / view what exists

**Easiest view (no terminal):** double-click **`view-prototype.command`** at the repo root — it
serves the folder and opens the hub in your browser.

```bash
# Or serve manually. NOTE: serve from design/prototype/ ; the shared design-system/
# is reachable inside it via a symlink (design/prototype/design-system → ../../design-system).
cd design/prototype && python3 -m http.server 8777
# then open http://localhost:8777/index.html   (the hub → every screen)
```

> **Every page is now SELF-CONTAINED** (styles + icons + store inlined), so opening any `.html`
> directly in a real browser (double-click, `file://`) also works — no server needed. Two caveats:
> (1) the in-app preview **pane** renders `file://` as a static `data:` snapshot that **strips
> JavaScript** (icons/cards/store won't run there) — use HTTP in the pane, or a real browser for
> `file://`; (2) Google Fonts need a network connection (falls back to the stack offline).

```bash
# Rebuild self-contained pages after editing any design-system/*.css or *.js (single source → pages)
node design-system/build.mjs

# End-to-end tests (auto-starts its own static server on :8752 via playwright.config webServer)
cd e2e && npx playwright test                      # 46 checks, desktop + mobile chromium
cd e2e && npx playwright test --update-snapshots    # only if the landing visual changed on purpose
```

**Try the connected app:** in **Settings** set Reading size → L, then open the **Assistant** (answer
text scales). Ask **"cognitive dissonance"**, **"anxiety"**, **"memory consolidation"**, **"classical
vs operant conditioning"** (cited answers) — the enquiry then appears in **History** and bumps
**Account**'s count. Change your name in **Account** → it syncs to the rail + Assistant instantly. A
crisis phrase shows the crisis card (and is deliberately NOT logged).

---

## 4. Locked decisions (do not re-litigate)

**Design (this session):**
- **Aesthetic = elevate the warm storybook world** (keep identity + illustrations, push craft). Not a
  pivot to dark editorial. Crisis/clinical states stay sober within the playful system (hard constraint).
- **`design-system/tokens.css` is the single source of truth** (colour, 3-font type scale w/ sizes +
  weights, spacing, radii, motion, surfaces). `app.css` = shell + components; `icons.js` = 24×24 stroke
  icon set; `store.js` = shared state; `shell.js` = shared rail; `build.mjs` = inliner. `DESIGN.md`
  documents intent and defers to `tokens.css` on any conflict.
- **Pages are self-contained via `build.mjs`** (inlines the design-system assets into each page,
  escaping `</script>`/`</style>`). Edit `design-system/*`, then `node design-system/build.mjs`.
- The old scraped `design-system/variables.css`, `theme.css`, `tokens.json` are **stale** (single-font
  Inter, some invalid values). `tokens.css` supersedes them; they remain only for a possible future
  Tailwind/token pipeline. Reconcile or delete before the React port (see §6).

**Product / engineering (unchanged, from the design interview; detail in [project.md §1](project.md) + ADRs):**
- **Domain/corpus:** grounded RAG over OpenStax *Psychology 2e* + PLOS ONE + NIMH. 30 PDFs, all
  openly licensed ([data/corpus/SOURCES.md](data/corpus/SOURCES.md)).
- **Agent:** RAG **+ tool-calling**, multi-turn, LangGraph + Postgres checkpointer. Flow: crisis-check →
  retrieve → grade → tool? → synthesize → faithfulness judge → (HITL on low-confidence clinical).
- **Storage:** Postgres + pgvector (HNSW) + Redis. — [ADR-0001](docs/adr/0001-single-postgres-pgvector.md)
- **Models:** config-driven **LiteLLM** gateway, role-based routing + fallback. Embeddings default local
  `bge-small-en-v1.5` (384-dim). — [ADR-0002](docs/adr/0002-config-driven-model-gateway.md)
- **Safety:** informational-only, crisis-first, faithfulness judge, HITL, disclaimers. —
  [ADR-0004](docs/adr/0004-informational-safety-posture.md) **(non-negotiable)**
- **Auth/security:** email+password JWT (argon2, refresh rotation, Redis revocation), `user`/`admin` RBAC.
- **Frontend:** Next.js (App Router) + TS + Tailwind + shadcn/ui + Vercel AI SDK, MindMarket theme.
- **Architecture:** modular monolith, feature-based vertical slices, `import-linter` in CI. —
  [ADR-0005](docs/adr/0005-modular-monolith-vertical-slices.md)
- **Deployment (hybrid):** Vercel → Render (FastAPI) → Neon (Postgres) + Upstash (Redis) + Langfuse
  Cloud. — [ADR-0003](docs/adr/0003-hybrid-deployment.md)

---

## 5. Key constraints & gotchas (easy to trip on)

**Design-system / prototype (NEW this session — read before editing prototypes):**
- **After editing `design-system/*.css` or `*.js`, run `node design-system/build.mjs`** or the pages
  won't pick up the change (they hold inlined copies). The inliner is idempotent (marker blocks).
- **Never put a literal `</script>` (or `</style>`) in a design-system source file's comments/strings.**
  It closes the inlined block early and silently breaks the page (this exact bug wiped all icons once).
  `build.mjs` now escapes them defensively, but keep sources clean.
- **The preview pane can't run `file://` JS** (static `data:` snapshot). Verify with the HTTP server or a
  real browser. Reliable pane verification = serve on `:8777` and use `javascript_tool` to assert DOM.
- **Serve from `design/prototype/`**, not the repo root and not a deeper dir — pages reach the shared
  assets via the `design/prototype/design-system` symlink; a wrong server root 404s the design system.
- **zsh does not word-split unquoted `$vars`** in `for` loops — use literal lists or `${=var}` in scripts.
- **`store.js` state is per-browser-origin `localStorage`** — it persists across pages on the same origin
  and survives reload, but is empty in a fresh browser (seeds 6 demo enquiries + a default profile then).
  `MMStore.reset()` restores defaults.

**Product (unchanged):**
- **Claude Pro ≠ Anthropic API.** Only a **Gemini API key** is actually available; LiteLLM slots others in.
- **Assistant answers are a canned matcher** (`answerFor()` in assistant.html), not real RAG.
- **All illustrations are hand-authored inline SVG** (paper-cut: organic paths, ink outlines, brand fills,
  offset paper-layers, gentle sway/twinkle). No image generator. Keep as SVG components in React.
- **`experience.html`** loads Three.js from CDN (needs network; static SVG fallback offline). Point-size /
  bloom math is delicate — don't crank bloom without shrinking points (see §11).
- **Glassmorphism only on floating chrome** (nav, account menu), never content cards; crisis/clinical sober.
- **OpenStax Psychology 2e is CC BY-NC-SA** → project is non-commercial/education.
- **Not a git repo yet** — `git init` is part of scaffolding (wayfinder 0009).
- **Some MCP servers** (Neon, GitHub, etc.) need OAuth before use in a session.

---

## 6. NEXT STEPS (ordered — start here)

**Design is DONE and the prototype behaves like a real app.** Three tracks remain — pick one:

**A. Figma work** (the prototype is now editable native Figma layers — see §9A).
1. **Modify in Figma** — file **Psychology Maverick Prototype**, fileKey `qgcyCk36GoKvr1BirjtiJo`,
   page "Prototype", 8 screens. Owned by the user (Malatesha, `prasannamalatesh6@gmail.com`, Full seat).
2. **Re-sync either direction** via the Figma MCP (`use_figma` + `figma-generate-design` skills):
   prototype code → Figma (update the frames with `get_metadata` + targeted `use_figma`, do NOT rebuild),
   or Figma edits → prototype code (read frames, port the deltas into `design/prototype/*` + `design-system/*`).
3. **Optional Figma polish** — replace the approximated vector mascot with the real paper-cut art;
   build the rail as a proper Figma component with variants; add the remaining states (crisis/insufficient
   answer, empty states) as frames.

**B. Small design follow-ups on the HTML prototype** (optional, from `docs/ux/redesign-plan.md`):
soften the yellow footer band; recede the mascot further on marketing; a `.stack` rhythm utility; e2e
coverage for the manage screens + the assistant state-badge.

**C. Scaffold the real app** (the prototype is the spec; the state layer + tokens carry over):
4. **Scaffold Next.js `frontend/`**, port the prototypes as components, wire `design-system/tokens.css`
   as the Tailwind v4 token source (retire/regenerate the stale `variables.css`/`theme.css`/`tokens.json`
   from `tokens.css`). Replace `store.js` localStorage with real API state. Point Playwright at the dev server.
5. **Scaffold FastAPI `backend/`** as the modular monolith ([ADR-0005](docs/adr/0005-modular-monolith-vertical-slices.md));
   `git init`; `uv` + `ruff` + `import-linter` in CI.
6. **Build the M1 vertical slice** (project.md §15): ingest a corpus subset → real `/chat` (retrieve →
   synthesize) → one Langfuse trace. Replace the canned matcher with real RAG.
7. **Resolve remaining wayfinder decisions** as reached (chunking/parser, crisis detection, eval rubric,
   Answer/citation contract, LiteLLM config — §7).
8. **Provision accounts** (Neon, Upstash, Langfuse, Render, Vercel) — **your task**; agent scaffolds
   `.env.example`, never enters real secrets.

**Recommended resume phrases:**
- "continue in Figma" / "re-sync Figma with the prototype" → Track A.
- "polish the prototype" → Track B (see `docs/ux/redesign-plan.md`).
- "scaffold the Next.js frontend and port the prototypes" → Track C (`/feature-dev` + `ponytail`).

---

## 7. Open decisions — the wayfinder map

Planning map at [.wayfinder/MAP.md](.wayfinder/MAP.md); tickets in [.wayfinder/tickets/](.wayfinder/tickets/).

- `0001` PDF parsing + chunking landscape — **open**
- `0002` chunking strategy (blocked on 0001) — **open**
- `0003` crisis-detection mechanism — **open** (highest-stakes; prototype uses a keyword regex placeholder)
- `0004` eval rubric + dataset — **open**
- `0005` frontend design system — **resolved** (MindMarket built as a single source of truth + applied;
  aesthetic direction now also settled: elevate the warm world). Close it.
- `0006` Answer + citation contract — **open** (prototype shows the intended shape)
- `0007` LiteLLM role→model config — **open**
- `0008` provision accounts — **open** (user task)
- `0009` repo scaffolding + CI — **open** (next-steps #6)

---

## 8. Full file map

```
HANDOFF.md                      ← you are here
view-prototype.command          double-click launcher (serves + opens the hub)
project.md · PRODUCT.md · CONTEXT.md · DESIGN.md   spec / product / glossary / design (DESIGN.md current)
design-system/                  SINGLE SOURCE OF TRUTH
  tokens.css                    colour, 3-font type scale (sizes+weights), spacing, radii, motion, surfaces
  app.css                       shell + component classes (buttons, cards, inputs, switch, segmented, rail…)
  icons.js                      24×24 stroke icon set (injected sprite; heart + settings redrawn correctly)
  store.js                      shared app state: profile · settings · enquiries (localStorage) — MMStore.*
  shell.js                      shared signed-in rail (brand → index, nav, account menu) — reads MMStore
  build.mjs                     inliner: folds the above into each page so every page is self-contained
  variables.css · theme.css · tokens.json   STALE (old single-font scrape) — superseded by tokens.css
docs/  PRD.md · adr/0001..0005 · ux/sitemap.md · ux/ux-audit-and-usability-plan.md
design/prototype/
  index.html        hub / front door — maps all 11 screens, paper-cut hero, staggered reveal
  landing.html      marketing — illustrations, glass nav, marquee, parallax
  experience.html   Three.js corpus constellation (bloom/vignette/FXAA, OrbitControls, CDN + fallbacks)
  auth.html         sign in / create account (wired → assistant)
  onboarding.html   3-step first run
  assistant.html    INTERACTIVE app (canned matcher); writes enquiries to MMStore; honors settings
  library.html      corpus browser (filter + search)
  history.html      real enquiry log from MMStore, grouped by day
  account.html      profile + live stats from MMStore (editable, syncs everywhere)
  settings.html     preferences that take effect (reading size, reduce motion, answer length…) via MMStore
  styleguide.html   living design system (colour, type scale, icon grid, components)
  design-system → ../../design-system   (symlink so the server root can reach the shared assets)
data/  fetch_corpus.sh · corpus/SOURCES.md · corpus/{textbooks,articles,mental_health}/
.wayfinder/MAP.md + tickets/    open design decisions
e2e/   Playwright: playwright.config.ts (serves design/prototype on :8752), tests/prototypes.spec.ts (46), snapshots
```

Fonts (Google Fonts, `display=swap`): **Bricolage Grotesque** (display) · **Inter** (body/UI) ·
**JetBrains Mono** (citations, source codes, taxonomic labels — the "receipts"). Via `--font-display` /
`--font-sans` / `--font-mono` in `tokens.css`.

---

## 9. One-line status

Design + a **connected** interactive prototype (self-contained pages, shared state so it behaves like a
real web app), current DESIGN.md + single-source design system, green (46/46). This session: (1) a
senior-designer **"calm & credible" UI/UX pass** — three corruption-class bugs fixed (double-rail,
icons-source leak, reveal-never-fires) + polish (assistant state-badge, coral discipline, semantic
tiles); (2) **front door restructured** — `index.html` now redirects to the real landing (app opens
like a product, not a "choose a flow" navigator), hub moved to dev-only `map.html`, rail brand →
`assistant.html`; (3) **whole prototype exported to Figma** as native editable layers (8 screens,
fileKey `qgcyCk36GoKvr1BirjtiJo`). Full detail: §9A + [docs/ux/redesign-plan.md](docs/ux/redesign-plan.md).
Next (§6): continue/re-sync in Figma (Track A), small prototype polish (B), or scaffold Next.js
`frontend/` + FastAPI `backend/` and replace the canned matcher with real RAG (C).

**Skills / tools used this session (all still available next session):** Figma MCP authoring
(`use_figma` + `figma-generate-design` + `figma-use` skills) — this is how the prototype was pushed to
Figma; gstack `design-review` / `devex-review` (invoked, but adapted — NOT a git repo, so the gstack
`browse` binary + per-fix-commit flow don't apply; used the built-in in-app Browser + a throwaway
Playwright script for reliable full-page screenshots instead); `caveman` default prose style. The
in-app browser **pane reports `innerHeight:0`** and can't scroll tall pages — use Playwright for
full-page truth (see the cache gotcha + verification notes in §9A).

---

## 9A. Session log — calm-credible UI/UX redesign pass (MOST RECENT)

A senior-designer engagement in response to "the prototype looks messy — do proper UI/UX research, a
better sitemap/flows, and an overall better, great-looking design; go page by page." Plan of record:
**[docs/ux/redesign-plan.md](docs/ux/redesign-plan.md)** (audit, direction, refined sitemap, user
flows, calm-credible design decisions, per-page status).

**Direction chosen (by the user):** **"calm & credible" evolution** of MindMarket — keep the cream
canvas, the three-font identity, and citation-as-receipts soul, but dial the playful loudness down to
match a safety-critical, citation-first mental-health tool. This *refines* the prior "elevate the warm
world" decision rather than reversing it; it does **not** pivot to dark editorial.

**Root-cause finding — most of "messy" was three corruption-class bugs, now fixed:**
1. **Double rail (S1).** A stale, unmarked inline `shell.js` copy survived next to the build-inlined
   one on Account/Library/History/Settings, so the shell ran twice → `.app` = `[rail, rail, main]`,
   content squeezed into the 288px column and a full-bleed coral bar. Stripped the stale region from
   all 4 (a scripted, guarded excision), and **added an idempotency guard to `shell.js`** so it can
   never mount twice again. Fixing this also killed the "full-bleed coral" (it was rail #2).
2. **Icons source leak (S1b).** `icons.js`'s top comment contained a literal `</script>` that closed
   the inlined block early, dumping the rest of the icon source as visible page text (worst on
   onboarding). Removed the literal tag from the **source**, and replaced each of 7 pages' corrupt
   icons region with a clean, properly-escaped block.
3. **Reveal never fires (S2).** Landing used `[data-reveal]{opacity:0}` revealed only by an
   IntersectionObserver that didn't fire for above-the-fold content on load → the hero rendered
   invisible. Rewrote it so in-view elements reveal synchronously on load with a late safety sweep;
   the hero is now bold on first paint. (auth's `.reveal` is the password toggle, unaffected; the hub
   uses a self-resolving CSS animation.)

**Calm-credible polish (targeted, per-page):**
- **Assistant state badge** now reflects the actual answer condition — *Grounded, cited* / *Outside
  corpus* / *Safety* (coral edge) — instead of a static "Grounded, cited". Verified across all three
  states via Playwright.
- **Coral discipline:** History's topbar "New enquiry" demoted to neutral so the rail's is the single
  coral primary per screen ("Clear all" was already danger-red).
- **Semantic hub tiles:** the green accent tile is now reserved for the one CORE surface (Assistant);
  Landing / Onboarding / Design-system tiles neutralised (green & coral are meaning, not decoration).

**Verification method:** the in-app browser pane reports `innerHeight:0` and can't scroll tall pages
(a known limitation), so full-page truth came from a **Playwright screenshot script**
(`scratchpad/shots.mjs`, 1440px, fullPage) — the dependable path noted in §11. All 9 main screens
reviewed full-length; all clean.

**Front door restructured (real-app entry, not a prototype navigator).** The old `index.html` was a
"choose a flow / 11 screens / Design system" navigator — no real app opens like that. Now:
`index.html` **redirects to `landing.html`** (the product front door → Open Maverick → auth → assistant);
the navigator is preserved as **`map.html`** (developer aid, never in the user path); the signed-in
**rail brand/logo now links to `assistant.html`** (app home) instead of the hub, and the assistant
topbar's "All screens" grid button was removed. e2e still 46/46 (it never depended on the hub).

**Figma export (this session).** The prototype was rebuilt as native, editable Figma layers via the
Figma MCP (`use_figma` + `figma-generate-design` skills). File: **Psychology Maverick Prototype**,
fileKey `qgcyCk36GoKvr1BirjtiJo`, page "Prototype" — 8 screens (Settings, Account, Library, History,
Assistant, Landing, Auth, Onboarding), built on the real MindMarket tokens (Bricolage/Inter/JetBrains
Mono, cream canvas, exact palette). The shared rail was cloned + active-state-swapped across app
screens. Illustrations (paper-cut mascot) are approximated as simple vector faces, not the hand-drawn
SVGs. Text nodes must be `layoutSizingHorizontal='FILL'` + `textAutoResize='HEIGHT'` or they overlap
(fixed on the built screens). To re-sync after prototype changes: use `get_metadata` on the file, then
targeted `use_figma` edits — do not rebuild from scratch.

**Cache gotcha (important).** Prototype HTML is cached hard by real browsers, so a stale broken page
can persist AFTER a fix lands on disk (this bit us: the user saw the old double-rail/code-leak Settings
even though the file was clean). Mitigation: serve `design/prototype/` with **no-cache headers**
(`scratchpad/nocache_server.py` on :8777, or add the headers to any server), and hard-reload
(Cmd+Shift+R) once after any fix. Verify disk truth with grep before assuming a page is broken.

**State:** every screen clean, cohesive, calm-credible. Design system was already well-built — this
pass **repaired execution and tightened color/state discipline**, it did not rebuild the system.
`tokens.css` needed no structural change. e2e **46/46**. **Next (optional):** soften the yellow footer
band; recede the mascot further on marketing; add a `.stack` rhythm utility; e2e coverage for the
manage screens + the new state-badge. Otherwise → Phase B build (scaffold Next.js `frontend/`, §6B).

---

## 10. Session log — design-system rebuild + real-app state + elevation (previous)

Delta since the "4 surfaces, visual-elevation" session (§11). Everything below is DONE unless marked.

### 10.1 `caveman` skill installed as a global default
- `npx skills add JuliusBrussee/caveman` (installed to `~/.claude/skills/` global). Kept the local
  token-savers (`caveman`, `cavecrew`, `caveman-commit`, `-review`, `-compress`, `-explore`, `-help`,
  `-stats`); **removed the 6 "Caveman Cloud" gateway skills** (`-setup/-discover/-evidence-review/
  -manage/-optimize/-learn`) — they ship repo/LLM data off-machine and `-setup` was High-Risk-flagged.
- Declared default in **`~/.claude/CLAUDE.md` §2.12**: caveman is the default *prose-style* compressor
  (chat only; code, commits, docs, memory files stay full English; `not/no/only`, numbers, error strings
  exact). Off with `/caveman off` or "normal mode".

### 10.2 Design system rebuilt into a single source of truth
- Wrote `design-system/tokens.css` (real 3-font scale + all tokens), `app.css` (shell/components),
  `icons.js` (48-icon stroke sprite — **fixed the distorted heart + settings/gear** with correct
  on-grid geometry), `shell.js` (shared rail). **Rewrote `DESIGN.md`** to match reality (it had falsely
  claimed a single-font Inter system and "no icon set").

### 10.3 Every page made self-contained
- `design-system/build.mjs` inlines the design-system assets into each page (idempotent marker blocks;
  escapes `</script>`/`</style>`). So any page opens standalone (`file://`, no server, no symlink needed).
- Fixed a real bug found along the way: a literal `</script>` inside `icons.js`'s comment was closing the
  inlined block early and wiping every icon — now escaped by `build.mjs`. Verified 48/48 icons render.

### 10.4 New screens (fills the "hollow options")
- Added **index (hub)**, **account**, **settings**, **library**, **history**, **onboarding**,
  **styleguide** — 11 screens total, all cross-linked (rail + hub + a "home/all-screens" affordance).
  Wired the assistant's previously-dead Account/Settings menu items to the real pages.

### 10.5 Shared state layer — the prototype now behaves like a real web app
- `design-system/store.js` (`window.MMStore`): one **profile**, one **settings** object, one **enquiry
  log** in `localStorage`, read/written by every screen. Verified end-to-end:
  - **Settings take effect:** reading-size L scaled the Assistant answer to 18.24px (16×1.14);
    reduce-motion forces app-wide (new `app.css` rule + `--read-scale`).
  - **Asking flows through the product:** a question typed in the Assistant persisted → appeared in
    **History ("Today")** → bumped **Account** to 7 enquiries.
  - **One profile everywhere:** renaming in Account synced the rail avatar/name, header, and Assistant
    chip instantly and persisted. Settings **Export** now downloads real JSON; **Clear** clears the log.
  - Assistant seeds its case-file rail from the shared log and honors the "Answer length" setting.

### 10.6 Elevation pass — started at the front door (direction: elevate the warm world)
- **index hero**: two-column desktop composition with a signature hand-authored paper-cut "mind bloom"
  illustration (calm face, sprout, floating heart + star — warm, sober, not toy-like), sway/twinkle
  motion, and a **staggered card reveal**. All motion respects the (now working) reduce-motion setting.
- **Remaining elevation is §6A** (Library/History/Account empty states, Assistant depth, restrained
  app-screen motion, rhythm audit). This is the exact point to resume the design work.

### 10.7 Tests
- **e2e still 46/46** (desktop + mobile). Changes to the assistant seeding/ask flow and the new state
  layer did not regress the suite. New pages aren't in e2e yet (add coverage when convenient).

---

## 11. Previous session log — visual elevation (4 surfaces, 3-font, Three.js)

(Kept for context; superseded where §10 differs — e.g. DESIGN.md is now current, pages are self-contained.)

- Installed **`threejs-*` (11)** and **`refero-design`** as global defaults (`~/.agents/skills/` →
  `~/.claude/skills/`), added to `~/.claude/CLAUDE.md` §2.10–2.11 (routing: refero direction → impeccable
  execution → Three.js only when WebGL is truly needed). **Refero MCP not yet connected** (needs
  interactive `claude mcp add --transport http refero https://api.refero.design/mcp` then `/mcp` sign-in).
- Introduced the **3-font system** and **hand-authored paper-cut illustrations** across landing/auth/
  assistant; **glassmorphism** on floating chrome; **sliding marquee**; **hero parallax**.
- Built **`experience.html`** — the Three.js corpus constellation (additive points + twinkle shader,
  bloom + vignette + FXAA, OrbitControls, reduced-motion + WebGL/CDN fallbacks, 6.5s safety timeout).
- The in-app browser pane was unreliable while backgrounded that session; the dependable path was a
  throwaway Playwright script against `http://localhost:8752` (WebGL via `--use-angle=swiftshader`).
- Left an open aesthetic question (keep mascot vs pivot to dark editorial) — **now RESOLVED in §1/§10:
  keep and elevate the warm world.**
