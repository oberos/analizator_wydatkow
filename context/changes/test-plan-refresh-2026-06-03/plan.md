# Test plan tooling and E2E smoke boundaries refresh Implementation Plan

## Overview

Refresh `context/foundation/test-plan.md` so tooling and e2e guidance reflect current reality (local Playwright CLI availability) while preserving frozen strategy/risk discipline and keeping downstream phase routing coherent.

## Current State Analysis

The plan currently contains a wording contradiction: it states no dedicated e2e runner is wired while also marking e2e on critical flows as required after Phase 1. Repository guidance now documents local `playwright-cli` smoke usage, but formal runner/config/CI wiring remains separate from that local signal.

## Desired End State

`test-plan.md` clearly distinguishes local CLI smoke capability from formal gate wiring, keeps e2e gate semantics internally consistent, updates cookbook boundaries for what smoke can/cannot prove, and preserves all strategy/risk foundations unchanged.

Verification is complete when section-to-section wording is coherent (`§4`, `§5`, `§6.3`, `§7`, `§8`), priority anxieties remain intact, and downstream routing to implementation stays unambiguous.

### Key Discoveries:

- Local Playwright CLI smoke is documented in repo guidance (`agents.md:21`).
- Current contradiction exists between stack/cookbook vs gate timing (`context/foundation/test-plan.md:84`, `context/foundation/test-plan.md:104`, `context/foundation/test-plan.md:131-133`).
- CI workflow wiring is currently absent (`context/foundation/roadmap.md:61`).
- Strategy/risk discipline that must remain frozen is explicit in `test-plan.md` (`context/foundation/test-plan.md:15-48`).

## What We're NOT Doing

- No edits to `§1 Strategy` or `§2 Risk Map` content and ordering.
- No Playwright infrastructure bootstrap, CI workflow authoring, or new test code implementation in this change.
- No expansion into static-page, Django-internals, or broad low-signal UI snapshot testing.

## Implementation Approach

Apply a constrained documentation refresh in `test-plan.md` only: first align e2e tooling and gate wording, then codify exclusions and freshness metadata, then run coherence checks against risk routing and phase language. Keep all changes traceable to the research artifact and selected planning decisions.

## Phase 1: Align e2e tooling and gate language

### Overview

Update the stack, quality-gate, and cookbook sections so they describe the same e2e state and do not contradict each other.

### Changes Required:

#### 1. Stack row and gate row synchronization

**File**: `context/foundation/test-plan.md`

**Intent**: Refresh `§4 Stack` and `§5 Quality Gates` so local Playwright CLI availability is explicit and e2e requiredness wording stays coherent with current phase semantics.

**Contract**: `§4` e2e row states local Playwright CLI smoke availability and tracks formal runner/CI status separately; `§5` keeps e2e as required with wording that no longer conflicts with cookbook boundaries.

#### 2. Cookbook §6.3 boundary update

**File**: `context/foundation/test-plan.md`

**Intent**: Replace outdated “no dedicated runner” framing with precise smoke boundaries for local CLI usage.

**Contract**: `§6.3` explicitly states what local smoke can prove (limited critical-flow early warning) vs what still requires formal runner/CI-grade enforcement.

### Success Criteria:

#### Automated Verification:

- Targeted wording checks pass: `rg "playwright-cli|e2e on critical flows|Adding an e2e test" context/foundation/test-plan.md`
- Django sanity checks pass: `$env:DEBUG="True" ; pdm run python manage.py check`

#### Manual Verification:

- Human review confirms `§4`, `§5`, and `§6.3` are internally consistent and no longer contradictory.
- Human review confirms wording does not overclaim local smoke as equivalent to deterministic CI e2e infrastructure.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase. Phase blocks use plain bullets — the corresponding `- [ ]` checkboxes for these items live in the `## Progress` section at the bottom of the plan.

---

## Phase 2: Refresh exclusions and ledger metadata

### Overview

Update negative-space and freshness sections so the refreshed policy remains explicit and maintainable.

### Changes Required:

#### 1. Negative-space exclusions expansion

**File**: `context/foundation/test-plan.md`

**Intent**: Add explicit exclusion for broad low-signal UI snapshots while preserving existing exclusions.

**Contract**: `§7` retains static pages and Django internals exclusions and adds snapshot exclusion language consistent with cost×signal principles.

#### 2. Freshness ledger synchronization

**File**: `context/foundation/test-plan.md`

**Intent**: Ensure `§8` verification timestamps and refresh triggers remain accurate after the wording refresh.

**Contract**: `§8` dates reflect this refresh pass and refresh triggers remain unchanged unless explicitly required by current state.

### Success Criteria:

#### Automated Verification:

- Exclusion and ledger markers present: `rg "What We Deliberately Don't Test|low-signal UI snapshots|Freshness Ledger" context/foundation/test-plan.md`
- Repo tests still pass baseline command: `$env:DEBUG="True" ; pdm run python manage.py test transactions.tests`

#### Manual Verification:

- Human review confirms exclusions now explicitly include broad low-signal UI snapshots.
- Human review confirms freshness entries and triggers remain coherent with updated tooling wording.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase. Phase blocks use plain bullets — the corresponding `- [ ]` checkboxes for these items live in the `## Progress` section at the bottom of the plan.

---

## Phase 3: Final coherence and routing verification

### Overview

Validate full-document coherence after refresh and ensure downstream phase routing remains stable for future orchestration.

### Changes Required:

#### 1. Cross-section coherence pass

**File**: `context/foundation/test-plan.md`

**Intent**: Verify that updated sections preserve the original strategy/risk discipline and do not change risk ownership or phase intent.

**Contract**: `§1` and `§2` remain unchanged; references to priority anxieties (auth/ownership negatives, budget boundaries, critical-flow e2e regressions) remain aligned with `§3` and `§5`.

#### 2. Change artifact and references finalization

**File**: `context/changes/test-plan-refresh-2026-06-03/change.md`, `context/changes/test-plan-refresh-2026-06-03/plan-brief.md`

**Intent**: Keep planning artifacts synchronized with the finalized scope and ready for `/10x-implement`.

**Contract**: Change status/metadata and brief references match finalized `plan.md` scope and phase ordering.

### Success Criteria:

#### Automated Verification:

- Section guard checks pass: `rg "^## 1\\. Strategy|^## 2\\. Risk Map|^## 3\\. Phased Rollout|^## 5\\. Quality Gates" context/foundation/test-plan.md`
- Lint passes: `pdm run ruff check .`

#### Manual Verification:

- Human review confirms no unintended edits to `§1` or `§2`.
- Human review confirms downstream implementation routing is clear and executable from this plan.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before closing the change. Phase blocks use plain bullets — the corresponding `- [ ]` checkboxes for these items live in the `## Progress` section at the bottom of the plan.

---

## Testing Strategy

### Unit Tests:

- Not applicable for this documentation-only change.
- Preserve existing unit-test guidance semantics in `test-plan.md`; no unit test code additions.

### Integration Tests:

- Run targeted existing Django test command as baseline guard: `$env:DEBUG="True" ; pdm run python manage.py test transactions.tests`.
- Keep integration-first risk posture untouched in wording.

### Manual Testing Steps:

1. Read `§4`, `§5`, and `§6.3` in sequence and verify they describe one coherent e2e model.
2. Read `§7` and confirm broad low-signal snapshot exclusion is explicit.
3. Read `§1` and `§2` to confirm they are unchanged from pre-refresh semantics.
4. Re-check `§3`/`§5` routing against highest anxieties (auth ownership, budget boundary, critical-flow e2e).

## Performance Considerations

- Documentation-only refresh; no runtime performance impact expected.
- Keep wording concise to reduce maintenance drift and future refresh cost.

## Migration Notes

- No schema/data migrations.
- No rollout migration required beyond plan-document refresh.

## References

- Change notes: `context/changes/test-plan-refresh-2026-06-03/change.md`
- Related research: `context/changes/test-plan-refresh-2026-06-03/research.md`
- Primary target: `context/foundation/test-plan.md`
- Tooling signal: `agents.md:21`
- CI status context: `context/foundation/roadmap.md:61`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: Align e2e tooling and gate language

#### Automated

- [x] 1.1 Targeted wording checks pass — 64f96b8
- [x] 1.2 Django sanity checks pass — 64f96b8

#### Manual

- [x] 1.3 Sections §4, §5, §6.3 are internally consistent — 64f96b8
- [x] 1.4 Local smoke boundaries are not overstated as CI-grade guarantees — 64f96b8

### Phase 2: Refresh exclusions and ledger metadata

#### Automated

- [x] 2.1 Exclusion and ledger marker checks pass — 19e05de
- [x] 2.2 Baseline Django tests command passes — 19e05de

#### Manual

- [x] 2.3 Broad low-signal UI snapshot exclusion is explicitly present — 19e05de
- [x] 2.4 Freshness ledger entries remain coherent after refresh — 19e05de

### Phase 3: Final coherence and routing verification

#### Automated

- [x] 3.1 Section guard checks pass — 8a6b9d6
- [x] 3.2 Lint passes — 8a6b9d6

#### Manual

- [x] 3.3 Strategy and risk-map sections remain unchanged in intent — 8a6b9d6
- [x] 3.4 Downstream implementation routing is clear and executable — 8a6b9d6
