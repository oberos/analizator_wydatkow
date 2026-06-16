# Test plan tooling and E2E smoke boundaries refresh — Plan Brief

> Full plan: `context/changes/test-plan-refresh-2026-06-03/plan.md`
> Research: `context/changes/test-plan-refresh-2026-06-03/research.md`

## What & Why

We are refreshing `context/foundation/test-plan.md` so e2e/tooling language matches current project reality: local Playwright CLI smoke is available, while formal runner/CI wiring semantics must remain explicit and coherent. The motivation is to remove section-level contradictions without changing strategy or evidence-led risk discipline.

## Starting Point

The current plan mixes inconsistent statements across `§4`, `§5`, and `§6.3`: e2e is described as unwired, but also required after Phase 1. Research confirms the local CLI signal exists while CI wiring remains absent, creating routing ambiguity if left unchanged.

## Desired End State

The refreshed test plan has one coherent e2e story: local CLI smoke is documented with clear boundaries, required-gate language is internally consistent, and exclusions/freshness metadata are updated. Strategy (`§1`) and risk map discipline (`§2`) remain unchanged.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) | Source |
| --- | --- | --- | --- |
| E2E gate posture | Keep e2e gate required | Matches your explicit instruction to keep requiredness with configured Playwright CLI usage. | Plan |
| Smoke boundary | Limited critical-flow smoke wording | Preserves honest signal strength without overclaiming deterministic CI guarantees. | Plan |
| Stack representation | Separate local CLI capability from runner/CI wiring status | Prevents future contradictions between tooling signal and enforcement layer. | Research |
| Negative space | Explicitly exclude broad low-signal UI snapshots | Keeps cost×signal discipline and avoids low-value snapshot sprawl. | Plan |
| Frozen scope | Keep §1 and §2 semantics intact | Maintains strategy and evidence-only risk discipline as non-negotiable. | Research |

## Scope

**In scope:**
- `test-plan.md` wording refresh in `§4`, `§5`, `§6.3`, `§7`, and `§8`.
- Cross-section coherence pass for phase routing and anxiety alignment.
- Plan artifacts synchronization for downstream implementation.

**Out of scope:**
- CI/workflow bootstrap or Playwright infrastructure implementation.
- New unit/integration/e2e test code.
- Any change to `§1 Strategy` or `§2 Risk Map` semantics.

## Architecture / Approach

Use a constrained, phase-based documentation refresh: synchronize e2e wording first, then exclusions/ledger metadata, then run final coherence verification against risk routing. Treat local Playwright CLI as a capability layer and keep gate semantics explicit at the policy layer.

## Phases at a Glance

| Phase | What it delivers | Key risk |
| --- | --- | --- |
| 1. Align e2e tooling and gate language | Coherent `§4`/`§5`/`§6.3` wording | Overstating local smoke as CI-equivalent |
| 2. Refresh exclusions and ledger metadata | Explicit snapshot exclusion + updated freshness cues | Under-specifying negative space for future contributors |
| 3. Final coherence and routing verification | Stable cross-section narrative and execution-ready artifacts | Hidden drift in phase/risk routing after edits |

**Prerequisites:** Existing research artifact is complete and accepted (`context/changes/test-plan-refresh-2026-06-03/research.md`).
**Estimated effort:** ~1-2 sessions across 3 phases.

## Open Risks & Assumptions

- Assumes required e2e gate wording can remain strict while still differentiating local smoke vs formal CI-grade enforcement.
- Assumes no concurrent refresh modifies `test-plan.md` sections in parallel.
- Assumes future e2e bootstrap change will operationalize any remaining formal wiring details.

## Success Criteria (Summary)

- `test-plan.md` sections `§4`, `§5`, `§6.3`, `§7`, `§8` are coherent and accurate with current tooling state.
- `§1` and `§2` remain unchanged in strategy and evidence discipline.
- Plan is implementation-ready for `/10x-implement test-plan-refresh-2026-06-03 phase 1`.
