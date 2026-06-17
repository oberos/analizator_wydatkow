---
date: 2026-06-03T21:23:37.6633858+02:00
researcher: GitHub Copilot (GPT-5.3-Codex)
git_commit: c618ff8c2a889c16109f9aa841921a1bf751e2af
branch: master
repository: oberos/analizator_wydatkow
topic: "test-plan-refresh-2026-06-03"
tags: [research, codebase, test-plan, e2e, quality-gates]
status: complete
last_updated: 2026-06-03
last_updated_by: GitHub Copilot (GPT-5.3-Codex)
---

# Research: test-plan-refresh-2026-06-03

**Date**: 2026-06-03T21:23:37.6633858+02:00  
**Researcher**: GitHub Copilot (GPT-5.3-Codex)  
**Git Commit**: c618ff8c2a889c16109f9aa841921a1bf751e2af  
**Branch**: master  
**Repository**: oberos/analizator_wydatkow

## Research Question

Refresh `context/foundation/test-plan.md` so tooling/e2e state is accurate, while preserving strategy and evidence discipline and keeping downstream phase routing coherent.

## Summary

The refresh scope is valid: strategy and evidence-led risk mapping can remain unchanged, while stack/cookbook language should be updated to acknowledge **local Playwright CLI smoke availability**. The current mismatch is that the plan still states no e2e runner while also marking CI e2e as required after Phase 1, even though there is no project-level Playwright config or CI workflow wired.

## Detailed Findings

### Tooling reality (local signal vs wired gate)

- Local Playwright CLI usage is documented in repository guidance: [`agents.md#L21`](https://github.com/oberos/analizator_wydatkow/blob/c618ff8c2a889c16109f9aa841921a1bf751e2af/agents.md#L21).
- `test-plan.md` still states e2e is "none yet" and "no dedicated e2e runner is wired": [`context/foundation/test-plan.md#L84`](https://github.com/oberos/analizator_wydatkow/blob/c618ff8c2a889c16109f9aa841921a1bf751e2af/context/foundation/test-plan.md#L84), [`#L131`](https://github.com/oberos/analizator_wydatkow/blob/c618ff8c2a889c16109f9aa841921a1bf751e2af/context/foundation/test-plan.md#L131).
- No Playwright dependency signal in Python project manifest: [`pyproject.toml`](https://github.com/oberos/analizator_wydatkow/blob/c618ff8c2a889c16109f9aa841921a1bf751e2af/pyproject.toml).
- No GitHub Actions workflow files are present under `.github/workflows/` at this commit.

### Gate and rollout coherence

- Phase table still routes critical-flow quality through integration + minimal smoke in Phase 1: [`context/foundation/test-plan.md#L68`](https://github.com/oberos/analizator_wydatkow/blob/c618ff8c2a889c16109f9aa841921a1bf751e2af/context/foundation/test-plan.md#L68).
- Quality gates currently claim e2e on critical flows is required after Phase 1: [`context/foundation/test-plan.md#L104`](https://github.com/oberos/analizator_wydatkow/blob/c618ff8c2a889c16109f9aa841921a1bf751e2af/context/foundation/test-plan.md#L104).
- Roadmap confirms CI wiring is still absent, matching the gap: [`context/foundation/roadmap.md#L61`](https://github.com/oberos/analizator_wydatkow/blob/c618ff8c2a889c16109f9aa841921a1bf751e2af/context/foundation/roadmap.md#L61).

### Strategy and risk-discipline preservation

- Strategy principles are explicit and should remain frozen: cost×signal, user concerns as evidence, risks as scenarios not code anchors: [`context/foundation/test-plan.md#L15-L28`](https://github.com/oberos/analizator_wydatkow/blob/c618ff8c2a889c16109f9aa841921a1bf751e2af/context/foundation/test-plan.md#L15-L28).
- Risk map is already evidence-led and non-anchor-based: [`context/foundation/test-plan.md#L40-L48`](https://github.com/oberos/analizator_wydatkow/blob/c618ff8c2a889c16109f9aa841921a1bf751e2af/context/foundation/test-plan.md#L40-L48).
- Refresh concerns keep priority anxieties unchanged (auth/ownership, budget boundaries, critical-flow e2e): [`context/changes/test-plan-refresh-2026-06-03/change.md#L21-L23`](https://github.com/oberos/analizator_wydatkow/blob/c618ff8c2a889c16109f9aa841921a1bf751e2af/context/changes/test-plan-refresh-2026-06-03/change.md#L21-L23).

## Code References

- `agents.md:21` - local `playwright-cli open` command documented.
- `context/foundation/test-plan.md:84` - e2e row says "none yet."
- `context/foundation/test-plan.md:104` - e2e gate marked required after Phase 1.
- `context/foundation/test-plan.md:131-133` - cookbook states no dedicated runner and fallback path.
- `context/foundation/test-plan.md:168-169` - static pages and Django internals excluded.
- `context/foundation/roadmap.md:61` - CI workflow absence.
- `context/changes/testing-critical-path-data-correctness/research.md:32-35` - prior phase: core protections implemented, remaining gaps mostly coverage.

## Architecture Insights

- The plan's architecture is risk-first and phase-routed; wording updates must avoid changing risk ownership between phases.
- Local CLI smoke is a **tooling signal**, not equivalent to a deterministic, CI-enforced e2e runner.
- Cookbook §6.3 should separate:
  - what manual/local smoke can prove (basic critical-flow operability),
  - what remains unwired (formal runner config, reproducible CI gate).

## Historical Context (from prior changes)

- `context/changes/testing-critical-path-data-correctness/research.md` established integration-first protection for isolation/import/summary before stronger e2e wiring.
- `context/changes/testing-critical-path-data-correctness/plan.md` aligned with minimal-cost, high-signal progression rather than infra-first expansion.
- This supports a refresh that updates wording and routing clarity without altering §1 strategy or §2 evidence discipline.

## Related Research

- `context/changes/testing-critical-path-data-correctness/research.md`

## Open Questions

- Should §5 mark critical-flow e2e as "required once runner+CI wiring lands" to remove the present contradiction?
- Should §7 explicitly add "broad low-signal UI snapshots" to exclusions alongside static pages and Django internals?
