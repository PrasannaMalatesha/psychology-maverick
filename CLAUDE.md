# Psychology Maverick

Repo-level guidance for Claude Code. Product truth lives in `PRODUCT.md` / `project.md` /
`CONTEXT.md` (glossary); architectural decisions in `docs/adr/`; written specs in `docs/specs/`.

## Agent skills

### Issue tracker

Issues and specs are tracked as **GitHub issues**, via the `gh` CLI. See `docs/agents/issue-tracker.md`.
_(Prerequisite: this repo is not on GitHub yet — `git init`, create the remote, and authenticate `gh`
before the skills can publish. Until then, specs live as files under `docs/specs/`.)_

### Triage labels

The five canonical triage roles, each label string equal to its name
(`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
