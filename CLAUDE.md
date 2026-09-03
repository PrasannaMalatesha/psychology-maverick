# Psychology Maverick

Repo-level guidance for Claude Code. Product truth lives in `PRODUCT.md` / `project.md` /
`CONTEXT.md` (glossary); architectural decisions in `docs/adr/`; written specs in `docs/specs/`.

**Start here to see where the project stands:** [`docs/ROADMAP.md`](docs/ROADMAP.md) — the living
tracker of the 9 build milestones (M1–M9), each milestone's spec + issue + status.

## Agent skills

### Issue tracker

Issues and specs are tracked as **GitHub issues** at `PrasannaMalatesha/psychology-maverick`,
via the `gh` CLI. See `docs/agents/issue-tracker.md`. Written specs are also kept under `docs/specs/`.

### Triage labels

The five canonical triage roles, each label string equal to its name
(`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
