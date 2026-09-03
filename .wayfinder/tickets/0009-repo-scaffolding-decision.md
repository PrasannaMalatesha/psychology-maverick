---
id: 0009
title: Repo scaffolding + CI decision
type: task
status: open
assignee:
blocked_by: []
---

## Question

(Task.) Establish the repo skeleton the build sits in: `git init`, confirm the `backend/` +
`frontend/` monorepo layout from [project.md §14](../../project.md), initialize the `uv` project +
`ruff` config, and choose the CI host (GitHub Actions is the default assumption — confirm, since
this is not yet a git repo). Resolution records the chosen layout, CI host, and any repo/remote
created. Unblocks the CI-pipeline-detail fog.
