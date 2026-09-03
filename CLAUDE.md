# Psychology Maverick

Repo-level guidance for Claude Code. Product truth lives in `PRODUCT.md` / `project.md` /
`CONTEXT.md` (glossary); architectural decisions in `docs/adr/`; written specs in `docs/specs/`.

**Start here to see where the project stands:** [`docs/ROADMAP.md`](docs/ROADMAP.md) — the living
tracker of the 9 build milestones (M1–M9), each milestone's spec + issue + status.

## Branching

Three long-lived branches, all on `origin`:

- **`dev`** — the integration branch. **All development lands here.** Feature work commits to `dev`.
- **`main`** — the stable trunk; `dev` is promoted into `main` when a slice is green and reviewed.
- **`prod`** — what is (or will be) deployed; `main` is promoted into `prod` for a release.

Flow: `dev` → `main` → `prod`. Never commit feature work directly to `main` or `prod`.

## Agent skills

### Issue tracker

Issues and specs are tracked as **GitHub issues** at `PrasannaMalatesha/psychology-maverick`,
via the `gh` CLI. See `docs/agents/issue-tracker.md`. Written specs are also kept under `docs/specs/`.

### Triage labels

The five canonical triage roles, each label string equal to its name
(`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
