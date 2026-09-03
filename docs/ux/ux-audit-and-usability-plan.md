# UX Audit & Usability-Test Plan — Psychology Maverick

Two parts: a heuristic audit of the current prototypes against established UI/UX laws (with the
fixes already applied), and a usability-test plan to validate the experience with real users. Laws
tell you where to look; only real users confirm the design works.

Surfaces audited: [landing.html](../../design/prototype/landing.html),
[assistant.html](../../design/prototype/assistant.html). Automated coverage:
[e2e/tests/prototypes.spec.ts](../../e2e/tests/prototypes.spec.ts) (22 checks, incl. an "UX laws &
accessibility" block).

---

## Part 1 — Heuristic audit (laws applied)

| Law / heuristic | What it asks | Status | What was done |
|---|---|---|---|
| **WCAG 1.4.3 Contrast** | Body text ≥ 4.5:1 | **Fixed** | Secondary text used stone-gray `#80827f` (~3.9:1 on cream/white → fail). Darkened to `#5f605b` (~6:1) in both surfaces. |
| **Fitts's Law / WCAG 2.5.8 Target size** | Interactive targets big enough to hit | **Fixed** | Citation chips were ~16px. Added a `::after` hit area (`inset:-8px`) to exceed 24px without growing the visual chip; icon buttons bumped 38→40px. |
| **Jakob's Law / Nielsen #7 Efficiency** | Match chat conventions; keyboard-friendly | **Fixed** | Enter sends, Shift+Enter newlines; composer focuses on load (desktop only, to avoid forcing the mobile keyboard). |
| **Nielsen #5 Error prevention** | Stop invalid actions | **Fixed** | Send is `aria-disabled` and visually muted while the composer is empty; enables on input. |
| **Nielsen #3 User control & freedom** | Easy exits | **Fixed** | Esc closes the mobile drawer (returns focus to the menu button), else collapses an open citation. |
| **Screen-reader state** | Expandable controls announce state | **Fixed** | `aria-expanded` on citation source toggles, synced on open/close and on marker click. |
| **Keyboard access / bypass blocks (WCAG 2.4.1)** | Skip repetitive nav | **Fixed** | Skip link on both surfaces; landing content wrapped in a `<main>` landmark. |
| **Von Restorff (isolation)** | The critical thing stands out | **Pass** | Crisis card is the only coral-framed surface; it reads as distinct and serious. |
| **Doherty threshold (< 400ms)** | Responsive feedback | **Pass** | All motion 120–550ms, transform/opacity only, `prefers-reduced-motion` honored. |
| **Hick's / Miller's Law** | Don't overload choices | **Pass** | Nav is 3 links + one CTA; the thread shows one answer at a time. |
| **Jakob's Law (layout)** | Familiar patterns | **Pass** | Conventional sidebar + thread + composer; conventional marketing scroll. |
| **Aesthetic-Usability Effect** | Polished feels usable | **Pass** | Coherent MindMarket system across both surfaces. |
| **Nielsen #1 Visibility of status** | Show what's happening | **Open (real app)** | The prototype pre-renders answers. The real app must show a streaming/typing state and a send→pending transition. Tracked for the build. |

**Residual items for the real build (not prototype-fixable):** streaming status indicator (#1),
full focus-trap in the mobile drawer, and a "stop generating" affordance once answers stream.

---

## Part 2 — Usability-test plan

### Objective
Determine whether people can (a) get a grounded, cited answer and trust it, (b) recognize when the
assistant declines (out-of-corpus, crisis), and (c) navigate multi-turn history — without
assistance. Surface the top friction points before the Next.js build.

### Method
Moderated usability test (remote or in-person), think-aloud, 45 minutes per session. Usability
testing is the right method here because we are evaluating a specific flow, not exploring open needs.

### Participants — 6 (2 per persona)
- **The Learner** — student or curious person exploring psychology/psychiatry.
- **The Clarity-Seeker** — someone trying to understand a mental-health topic for themselves or a
  loved one. *(Screen out anyone currently in acute distress; the crisis task is evaluated with a
  neutral, hypothetical framing only, and the session includes real support resources up front.)*
- **The Skeptic** — a reviewer who distrusts AI answers (tests whether citations earn trust).

### Tasks (success criteria in brackets)
1. "Find out the difference between two ideas you're curious about." *(Reaches an answer; opens at
   least one citation.)*
2. "Decide whether you'd trust this answer, and say why." *(Uses the citation/source to judge, not
   just the prose.)*
3. "Ask a follow-up." *(Finds/uses multi-turn; understands the conversation persists.)*
4. "Ask it something it can't know." *(Recognizes the `insufficient_context` state as honesty, not
   failure.)*
5. Hypothetical-framed crisis prompt. *(Notices the response surfaces help and does not "answer";
   can find the 988 resource.)*
6. Return to a previous conversation from the sidebar. *(Locates and switches case files.)*

### Metrics
- **Task success rate** (binary + assisted) per task.
- **Time on task** and **error count** (wrong path, dead ends).
- **Trust rating** (1–5) after task 2, with the reason.
- **SUS** (System Usability Scale) at the end; target ≥ 75.
- Qualitative: confusion moments, quotes, "what did you expect to happen?"

### Session guide (per the research method structure)
Warm-up (5) → current habits with AI answers (10) → the 6 tasks, think-aloud (20) → reactions and
the trust/safety framing (7) → wrap-up and SUS (3).

### Analysis
Affinity-map observations into themes; place findings on an impact/effort matrix; a short journey
map of the "ask → judge → follow-up" arc. Deliver a synthesis report (themes, insights, ranked
recommendations) plus a highlight reel of key quotes.

### Timeline
1–2 weeks: recruit + screen (days 1–4), sessions (days 5–8), synthesis (days 9–10).

### Safety note
Because tasks touch mental-health content, the screener excludes anyone in current crisis, the
moderator has support resources on hand, and participants can skip task 5. This is an ethics
requirement, not a nicety.
