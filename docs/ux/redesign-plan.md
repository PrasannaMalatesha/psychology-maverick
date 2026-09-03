# Redesign Plan — Psychology Maverick ("Calm & Credible" evolution)

A senior-designer pass on the prototype. Direction chosen: **evolve the warm MindMarket world into a
calmer, more credible system** — keep the cream canvas, the three-font identity, and the
citation-as-receipts soul, but dial the playful loudness down to match a safety-critical,
citation-first mental-health tool whose own principles say *"calm, credible, never gamified."*

This document is the plan of record: the audit, the direction, the refined information architecture,
the user flows, the concrete design decisions (type / color / spacing / weight), and the page-by-page
execution order. It supersedes nothing in [DESIGN.md](../../DESIGN.md) except where it calibrates the
system; `design-system/tokens.css` remains the machine-readable source of truth.

---

## 1. Audit — why it read "messy" (evidence-based, from the live prototype)

Three **systemic** faults produced most of the mess; fixing them lifts every screen at once.

| # | Fault | Evidence | Blast radius |
|---|-------|----------|--------------|
| S1 | **Rail renders twice** — a stale, unmarked inline `shell.js` copy survived alongside the build-inlined one, so the shell IIFE runs twice. `.app` becomes `[rail, rail, main]`; rail #2 eats the `1fr` column and `main` wraps into the 288 px rail column. | `.app` children = `scrim, rail, scrim, rail, main`; `shellScripts: 2`; Account profile card clipped mid-word. | Library, History, Account, Settings (all 4 manage screens) |
| S2 | **Reveal-on-load leaves content invisible** — reveal wrappers start at low opacity and only animate in on an IntersectionObserver hit that never fires for above-the-fold content on direct load. | Landing hero + CTAs render washed-out; `h1` computed opacity `1` but 17 visible elements faded (parents); hub shows a large empty dead-band. | Landing, Hub, any reveal-animated surface |
| S3 | **Loudness miscalibration** — coral used as a full-bleed bar (was actually rail #2 spanning wide), giant 132 px display in-app, decorative yellow/blue/coral competing, no strict spacing rhythm. | Full-width coral "New enquiry"; oversized headings on utility screens; inconsistent section gaps. | Every screen's hierarchy |

**What is already good and must be preserved:**
- The **Assistant answer layout** — citation-first prose, a Sources panel, `CONFIDENCE ●●● High / REGISTER Textbook` mono "receipts." This is the product's soul; keep it, refine it.
- The **hub IA** — Arrive → Get in → Use it → Manage → Reference is a clean mental model.
- The **warm cream canvas + three-font system** — distinctive and appropriate once calmed.

---

## 2. Direction — "Calm & Credible"

The instinct of MindMarket is right (warmth, one accent, receipts). Its *calibration* is wrong for
this product. The evolution, in one line each:

- **Warmth stays, playfulness recedes.** Cream canvas and rounded forms remain; the mascot drops from
  hero-lead to a small, occasional spot illustration. Crisis and clinical states are sober by rule.
- **Color earns a job.** Every hue becomes semantic, not decorative:
  - **Grass green = grounded / confident / safe / active** (the trust signal).
  - **Coral = the single primary action + the crisis edge, and nothing else.** Never a large fill.
  - **Sky blue = information dots only. Yellow = marketing closing band only** (banished from app UI).
- **Type calms down.** Keep Bricolage / Inter / JetBrains Mono, but the shouting 132 px display is
  reserved for the marketing hero alone; app screens top out at a restrained heading scale.
- **Rhythm is strict.** One 8-pt vertical rhythm across every page; consistent card padding, section
  gaps, and reading measure.

Success test: a distressed clarity-seeker feels *met by something trustworthy*, and a skeptical
reviewer *trusts the citations* — without either being met by something toy-like or cluttered.

---

## 3. Information architecture — refined sitemap

Routes are unchanged in structure (the IA was sound); the refinement is **hierarchy and labelling
clarity**, not new destinations.

```
Public
  /                 Landing            — persuade: what it is, how grounding works, safety, sources
  /experience       Corpus experience  — optional immersive 3D way into the corpus (progressive)
  /auth             Sign in / Create   — one route, two modes

Signed-in  (shared rail: Assistant · Library · History  ·  Account · Settings)
  /app              Assistant          — CORE. ask → think → grounded, cited answer. Crisis-first.
    · first run →   Onboarding         — 3 steps: what it is, how grounding works, safety
  /library          Library            — browse the corpus every answer draws from (filter + search)
  /history          History            — every past enquiry, grouped by day, searchable
  /account          Account            — profile, usage, plan, security
  /settings         Settings           — appearance, answer style, safety region, notifications, privacy

Admin (future)
  /admin/corpus     Corpus stats       — ingest / refresh / stats
```

Nav model: **primary = the three doing-surfaces** (Assistant, Library, History); **secondary = the two
managing-surfaces** (Account, Settings), grouped under a "Your account" divider in the rail. Hick's
Law: never more than five destinations in the rail.

---

## 4. User flows (the order we build in)

### Flow A — Arrive → Enter  (`landing → auth → onboarding → app`)
1. **Land.** Hero states the one promise ("Grounded answers about the mind"), sub-line names the
   guardrail (sources + "informational, never a diagnosis"). One primary action: *Open Maverick*.
2. **Understand (scroll).** How it works (ask → retrieve → cite), Safety (crisis-first, informational),
   Sources (the three registers). Second CTA repeats.
3. **Enter.** `/auth` — sign in or create account (one toggle). Minimal fields, visible validation.
4. **First run.** Onboarding: 3 calm steps → lands in the Assistant empty state.

### Flow B — Use it (core)  (`app` empty → ask → answer → follow-up → cross-reference`)
1. **Empty state.** A calm invitation + example queries (grounded, out-of-corpus, crisis-safe framing).
2. **Ask.** Composer: Enter sends, Shift+Enter newline; send disabled while empty; focus on load (desktop).
3. **Think.** A visible, sober "retrieving → grounding" status (Nielsen #1). No fake personality.
4. **Answer.** Grounded prose with inline citation markers → Sources panel; `CATEGORY / CONFIDENCE /
   REGISTER` receipts. Four conditions: grounded+cited, insufficient-context, clinical-disclaimer,
   crisis-escalation (crisis pre-empts retrieval; sober coral-edged card with real resources).
5. **Follow up / branch.** Multi-turn thread; each enquiry logs to History and bumps Account.
6. **Cross-reference.** From a citation → open that source in Library.

### Flow C — Manage  (`account ↔ settings`, changes take effect live)
1. **Account.** See usage, edit profile (syncs to rail + assistant instantly), plan, security.
2. **Settings.** Appearance (reading size, reduce motion), answer style, safety region, notifications,
   privacy — every control has a real effect via the shared store. Nielsen #4 consistency.

---

## 5. Design decisions — the calibration (type · color · spacing · weight)

Authoritative values land in `design-system/tokens.css`; this section is the intent.

### 5.1 Typography
- **Families unchanged:** Bricolage Grotesque (display), Inter (body/UI), JetBrains Mono (receipts).
- **Restraint in-app:** the fluid hero (≤ ~104 px, lowered from 132) is **marketing-only**. App screens
  lead with a calmer heading (`h2`/`h3` scale). Authority now comes from *rhythm and restraint*, not size.
- **Weights disciplined:** display 600 (700 only for the marketing hero); body Inter 400; UI 500;
  emphasis 600. No 800 in-app. Mono 500, uppercase, tracked, receipts only — never prose.
- **Reading comfort:** prose measure 60–66 ch, body line-height 1.6, headings tighter (0.94–1.2).
- **Contrast:** muted text `#5f605b` (AA on cream) — keep; never the decorative `#80827f` for text.

### 5.2 Color — semantic roles (no more decorative multi-accent in app)
| Role | Token | Use |
|------|-------|-----|
| Canvas | `--bg` cream `#f5f1e4` | page ground (never pure white) |
| Surface | `--surface` white | elevated cards, floating chrome |
| Text / border | `--text` ink `#2c2e2a` | text, 1.5 px hairlines, icons |
| **Grounded / confident / safe / active** | `--accent` grass (bright for small marks, `grass-deep` for interactive/hover) | active-nav bar, confidence dots, "grounded" markers, success |
| **Primary action + crisis edge** | `--action` coral | the ONE prominent action (primary buttons, send) + crisis card edge. Never a large fill. |
| Info | `--info` sky | icon dots only |
| Danger | `--danger` | destructive text (sign out, delete, clear) |
| Marketing warmth | `--color-sunshine-pop` | closing band on landing **only** — absent from app UI |

Rule: **one chromatic accent per component.** Buttons are grass-structural, coral-action, or
light-ghost-with-one-dot — never multicolor.

### 5.3 Spacing — one strict 8-pt rhythm (values already in tokens: `--sp-1..11`)
- Page: top pad `--sp-8` (40), bottom `--sp-9`+; content max 900 px (wide 1120).
- Section stack gap `--sp-7` (32); card padding 24 px; intra-card element gap `--sp-4` (16); list-row
  padding `--sp-5` (20). A `.stack` utility enforces the gap so no screen free-hands its spacing.
- Radii unchanged: cards 26, pills 50, chips 10 — the soft identity stays.

### 5.4 Motion
- All motion is **enhancement over a visible baseline** — content is legible with zero JS/animation.
- Restrained: one subtle on-load settle for page content; 120–340 ms, transform/opacity only; honor the
  (working) reduce-motion setting and OS preference. No scroll-jank, no entrance gating above the fold.

---

## 6. Execution order & status

**Phase 1 — Foundation (systemic fixes + calibration).** Highest leverage; repairs many screens at once.
- [x] S1: stripped stale duplicate `shell.js` blocks from the 4 manage pages; added an idempotency
      guard to `shell.js`. Verified Account/Library/History/Settings render single-rail and clean.
- [x] S1b (found in pass): 6–7 pages leaked `icons.js` source as visible text via an unescaped
      `</script>` in the icons source comment. Removed the literal tag from the source; replaced each
      page's corrupt icons region with a clean escaped block. Verified onboarding + icons render.
- [x] S2: landing reveal now degrades to visible — in-view elements reveal synchronously on load, a
      late safety sweep guarantees nothing stays hidden if the observer never fires. Hero renders bold
      on first paint. (auth's `.reveal` is the password toggle, not affected; hub uses a self-resolving
      CSS animation — see Phase 2 rhythm.)
- [x] Regression gate: e2e **46/46** green after all foundation edits.
- [ ] S3: `tokens.css`/`app.css` calibration is lighter than expected — most loudness was the
      double-rail/coral-bar bug, now gone. Remaining: coral discipline nits, hub rhythm, a `.stack`
      utility — folded into the Phase 2 page passes where they're visible.

**Phase 2 — Page by page, one flow at a time** (each verified via reliable full-page Playwright
screenshots at 1440px — the in-app pane reports `innerHeight:0` and can't scroll tall pages, a known
limitation from HANDOFF; the pane is fine for above-the-fold checks):
- [x] Flow A — landing / auth / onboarding: **all clean and credible.** Landing already embodies the
      direction (type-led hero, sober mascot, Ask/Retrieve/Cite, sober crisis card + 988, source cards
      with license receipts, yellow closing band). Auth is a polished two-panel split, single coral
      primary. Onboarding fixed (was leaking icons source) — calm centered card.
- [x] Flow B — assistant / library / history: assistant is strong (citation-first, dual sources,
      confidence/register receipts) — **fixed the static state badge** so it now reflects the actual
      answer condition (Grounded, cited / Outside corpus / Safety-coral), verified across all three via
      Playwright. Library is a clean corpus browser. History **coral discipline** applied (topbar
      "New enquiry" demoted to neutral so the rail's is the single coral primary; "Clear all" already
      danger-red).
- [x] Flow C — account / settings: both render clean post-S1 (grouped cards, segmented controls,
      live-effect toggles, "Saved automatically").
- [x] Hub (index): the "dead-band" was a pane artifact, not a real gap — structure is sound.
      **Icon tiles made semantic** — green accent now reserved for the one CORE surface (Assistant);
      Landing/Onboarding/Design-system tiles neutralised (green/coral are meaning, not decoration).

**Outcome.** The "messy" was ~80% three corruption-class bugs (double-rail, icons-source leak,
reveal-never-fires), now fixed; the remaining calm-credible calibration was lighter than expected and
applied as targeted per-page polish. Every screen is clean, cohesive, and credible. e2e **46/46**
throughout. The design system was already well-built — this pass repaired execution and tightened
color/state discipline rather than rebuilding it.

**Optional further polish (diminishing returns, not done — flag if wanted):** soften the yellow
footer band's intensity; let the mascot recede further on marketing; a formal `.stack` rhythm utility;
add e2e coverage for the new manage screens and the state-badge.

**Guardrails carried from HANDOFF:** after editing any `design-system/*`, run `node design-system/build.mjs`.
Never put a literal `</script>`/`</style>` in a source file. Serve from `design/prototype/`. Keep e2e green
(update snapshots only on intentional visual change). Crisis/clinical states stay sober — hard constraint.
