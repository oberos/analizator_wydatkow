# Local static assets restoration — Plan brief

> Full plan: `context/changes/fix-summary-table/plan.md`

## What & Why

We are fixing a local-development bug where CSS/JS do not load because static asset URLs resolve to `/app/...` and `/vendor/...` instead of `/static/...`. The goal is to restore reliable local UI rendering without changing behavior on Render, where deployment already works.

## Starting Point

Templates already use Django `{% static %}` for Bootstrap and app assets, and files exist under `accounts/static/...`. Current settings produce incorrect local static URL prefixes, which causes the observed 404s in dev logs.

## Desired End State

Running the project locally loads all expected CSS/JS from `/static/...` URLs, and dashboard/login screens render styled UI correctly. Production deployment path remains untouched. The change also includes a focused regression guard and a documented local recovery command.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) |
| --- | --- | --- |
| Scope boundary | Local static fix only | Production already works; we should avoid unrelated refactors. |
| Environment strategy | Separate local settings module | Keeps local overrides explicit and isolated from deployment defaults. |
| Failure handling | Keep failures visible + document deterministic recovery | Preserves signal for real misconfigurations while unblocking developers quickly. |
| Verification depth | Config + targeted automated tests + manual check | Adds durable regression coverage with low implementation overhead. |

## Scope

**In scope:**
- Local settings module for static behavior.
- Static URL generation fix to `/static/...` in local workflow.
- Targeted tests for static URL generation.
- Developer docs update with local command and recovery step.

**Out of scope:**
- Render production configuration changes.
- CDN/static fallback logic.
- Frontend pipeline or static folder restructuring.

## Architecture / Approach

Introduce a dedicated `settings_local` module layered on top of base settings, and route local command usage through it. Validate static URL generation through focused tests and preserve existing dashboard behavior by keeping current functional tests green.

## Phases at a Glance

| Phase | What it delivers | Key risk |
| --- | --- | --- |
| 1. Local settings split | Dedicated local settings path with correct static URL behavior | Miswiring settings module for local commands |
| 2. Regression tests | Automated guard for `/static/...` URL generation | Brittle assertions if tied to unrelated template output |
| 3. Docs and recovery | Clear local command path and deterministic static recovery step | Docs drifting from actual command behavior |

**Prerequisites:** Existing Django local environment with `pdm` workflow and static assets present under `accounts/static/`.
**Estimated effort:** ~2-3 sessions across 3 phases.

## Open Risks & Assumptions

- Assumes local workflow can safely rely on explicit local settings module selection.
- Assumes no hidden environment-level static rewrites outside Django settings affect local requests.

## Success Criteria (Summary)

- Local dev serves Bootstrap and app assets from `/static/...` with no 404s for `/app/*` or `/vendor/*`.
- Targeted tests catch regressions in static URL generation.
- Developers can recover from static misconfiguration using one documented command path.
