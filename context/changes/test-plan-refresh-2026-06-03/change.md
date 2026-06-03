---
change_id: test-plan-refresh-2026-06-03
title: Refresh test plan tooling and E2E smoke boundaries
status: implemented
created: 2026-06-03
updated: 2026-06-03
archived_at: null
---

## Notes

Open a refresh change for context/foundation/test-plan.md (refresh mode).

Refresh scope summary:
- Keep strategy rules (§1) and evidence-only risk discipline (§2) intact.
- Update stack/tooling representation for newly added e2e tool signal (playwright-cli documented in agents.md).
- Reconcile guide language that currently says "no dedicated e2e runner" with reality: local Playwright CLI is available, but project-level Playwright config/CI gate may still be unwired.
- Update cookbook §6.3 to describe the correct e2e smoke usage path and boundaries (what CLI can prove vs what still requires formal runner/CI wiring).
- Preserve negative space exclusions: static pages, Django internals, broad low-signal UI snapshots.

User-stated refresh concerns (unchanged vs prior interview):
- Highest anxiety remains around auth/ownership negative paths, budget-cycle boundary correctness, and critical-flow e2e regressions.

Expected output of this refresh change:
- A concrete plan to refresh context/foundation/test-plan.md (without in-place ad hoc edits) so tooling/state is accurate and downstream phase routing remains coherent.
- Follow the downstream continuation rule after opening the folder.
