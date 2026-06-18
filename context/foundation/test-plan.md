# Test Plan

> Phased test rollout for this project. Strategy is frozen at the top
> (§1–§5); cookbook patterns at the bottom (§6) fill in as phases ship.
> Read before writing any new test.
>
> Refresh: re-run `/10x-test-plan --refresh` when stale (see §8).
>
> Last updated: 2026-06-03

## 1. Strategy

Tests follow three non-negotiable principles for this project:

1. **Cost × signal.** The cheapest test that gives a real signal for the
   risk wins. Do not promote to e2e because e2e "feels safer." Do not put a
   vision model on top of a deterministic visual diff that already catches
   the regression.
2. **User concerns are first-class evidence.** Risks anchored in "<the
   team is worried about X, and the failure would surface somewhere in
   <area>>" carry the same weight as PRD lines or hot-spot data.
3. **Risks are scenarios, not code locations.** This plan documents *what
   could fail* and *why we believe it's likely* - drawn from documents,
   interview, and codebase *signal* (churn, structure, test base). It does
   NOT claim to know which line owns the failure. That knowledge is
   produced by `/10x-research` during each rollout phase. If the plan and
   research disagree about where the failure lives, research is the
   ground truth.

Hot-spot scope used for likelihood weighting: `accounts`, `categories`, `transactions`, `analizator_wydatkow`, `templates`.

## 2. Risk Map

The top failure scenarios this project must protect against, ordered by
risk = impact × likelihood. Risks are failure scenarios in user / business
terms, not test names. The Source column cites the *evidence that surfaced
this risk* - never a specific file as "where the failure lives" (that is
research's job, see §1 principle #3).

| # | Risk (failure scenario) | Impact | Likelihood | Source (evidence - not anchor) |
|---|---|---|---|---|
| 1 | Logged-in user can view or modify another user's transactions or categories. | High | High | PRD guardrail + Access Control; roadmap F-01 risk note; interview Q1; hot-spot dir `accounts` (15 commits/30d) |
| 2 | CSV import appears successful but silently drops or duplicates transactions. | High | High | PRD FR-003 + US-01; roadmap S-02 risk note; interview Q1; hot-spot dir `transactions` (36 commits/30d) |
| 3 | Merchant-to-category mapping quality regresses and manual corrections do not reliably improve future auto-categorization. | High | High | PRD business logic; roadmap S-07 risk note; interview Q2/Q3/Q4; hot-spot dir `transactions/mappings` (14 commits/30d) |
| 4 | Summary table shows wrong totals (including income as spending, or wrong totals after filtering/sorting). | High | High | PRD FR-009 + FR-013 + FR-014; interview Q1/Q2/Q3/Q4; hot-spot dirs `transactions` + `templates/transactions` |
| 5 | Authenticated user bypasses ownership checks (IDOR-style read/update on foreign resources). | High | Medium | PRD Access Control; PRD guardrail on isolation; interview Q1; roadmap auth foundation risk |
| 6 | Budget-cycle boundaries are computed incorrectly, distorting paycheck-to-paycheck reporting. | Medium | Medium | PRD FR-010 + FR-011; roadmap S-05 (ready); interview Q3/Q4 |

### Risk Response Guidance

| Risk | What would prove protection | Must challenge | Context `/10x-research` must ground | Likely cheapest layer | Anti-pattern to avoid |
|------|-----------------------------|----------------|--------------------------------------|-----------------------|-----------------------|
| #1 | Access to user-owned data is restricted by ownership on both read and write paths. | "Authenticated" means "authorized for this resource." | Auth/session shape, ownership persistence model, error translation for forbidden access. | Integration | Role-only happy-path tests without foreign-resource negatives. |
| #2 | Import output preserves statement integrity (no silent loss/duplication) and surfaces parse failures explicitly. | "Upload succeeded" implies complete ingest. | CSV ingestion boundary, normalization/parsing stages, persistence expectations, failure handling. | Integration + contract-style fixtures | Asserting only success status/UI without count/integrity checks. |
| #3 | Manual correction deterministically updates future categorization for matching merchant patterns. | Mapping match implies categorization correctness. | Mapping persistence and update rule, correction workflow boundary, fallback rule for unknowns. | Integration | Implementation-mirror assertions copied from categorization internals. |
| #4 | Report totals exclude income and remain correct under active filter/sort combinations. | Rendered totals are inherently correct. | Aggregation source of truth, transaction type semantics, filter/sort interaction behavior. | Integration + targeted e2e smoke | Recomputing expected totals with copied production aggregation logic. |
| #5 | Foreign-resource requests are rejected even with a valid session. | Session presence is sufficient ownership proof. | Resource lookup path, ownership validation boundary, negative-path response behavior. | Integration/security negatives | Testing only anonymous-vs-authenticated paths and skipping ownership abuse cases. |
| #6 | Cycle boundaries include/exclude transactions exactly as paycheck-cycle rules require. | Calendar-like ranges are acceptable for paycheck cycles. | Date boundary semantics, timezone/date normalization behavior, filtering boundary logic. | Integration | Boundary-free happy paths that skip edge dates. |

## 3. Phased Rollout

Each row is a discrete rollout phase that will open its own change folder
via `/10x-new`. Status moves left-to-right through the values below; the
orchestrator updates Status as artifacts appear on disk.

| # | Phase name | Goal (one line) | Risks covered | Test types | Status | Change folder |
|---|---|---|---|---|---|---|
| 1 | Critical-path data correctness | Defend isolation, import integrity, and summary correctness at the cheapest useful layer. | #1, #2, #4 | integration (+ minimal critical-flow e2e smoke) | complete | context/changes/testing-critical-path-data-correctness/ |
| 2 | Categorization reliability | Protect mapping precision and correction-to-learning behavior. | #3 | integration + contract fixtures | complete | context/changes/testing-categorization-reliability/ |
| 3 | Abuse and boundary hardening | Catch ownership abuse and paycheck-cycle boundary regressions before release. | #5, #6, #4 | integration/security negatives | complete | context/changes/testing-abuse-and-boundary-hardening/ |
| 4 | Quality-gates floor + selective AI-native checks | Lock CI floor and add only selective AI-native checks where deterministic tests are insufficient. | cross-cutting | gates + optional local post-edit hook + selective multimodal review | not started | — |

## 4. Stack

The classic test base for this project. AI-native tools (if any) carry a
`checked:` date so future readers can see which lines need re-verification.
Recommendations in this section are grounded in local manifests/configs plus
the tools exposed in the current session.

| Layer | Tool | Version | Notes |
|---|---|---|---|
| unit + integration | Django test runner (`manage.py test`) | Django 6.x | Existing suite is sparse (3 app-level test files). |
| API/request mocking | Django `RequestFactory` / built-in test utilities | Django 6.x | Prefer framework-native request/DB testing before extra libraries. |
| e2e | Playwright CLI smoke (`playwright-cli open ...`) | local CLI (manual) | Use limited critical-flow smoke as an early warning layer; keep deterministic CI e2e runner wiring tracked separately. |
| accessibility | none yet - see Phase 4 | n/a | Evaluate only if UI regressions become a recurring risk. |
| (optional) AI-native | none yet - checked: 2026-06-03 | n/a | When NOT to use: do not use for deterministic logic assertions or broad snapshot replacement. |

**Stack grounding tools (current session):**
- Docs: none - no docs MCP exposed in this session; checked: 2026-06-03
- Search: web_fetch - available, not required for Phase 1 evidence synthesis; checked: 2026-06-03
- Runtime/browser: Playwright CLI available locally (`playwright-cli open ...` in `agents.md`); no Playwright/browser MCP exposed; checked: 2026-06-03
- Provider/platform: GitHub MCP - available for quality-gate observability and CI status checks; checked: 2026-06-03

## 5. Quality Gates

The full set of gates that must pass before a change reaches production.
"Required for §3 Phase <N>" means the gate is enforced once that rollout
phase lands; before that, the gate is `planned`.

| Gate | Where | Required? | Catches |
|---|---|---|---|
| lint + typecheck | local + CI | required | syntactic and basic type drift |
| unit + integration | local + CI | required after §3 Phase 1 | logic/data regressions in critical paths |
| e2e on critical flows | local + CI on PR | required after §3 Phase 1 | broken end-to-end user-critical paths (local CLI smoke now; CI enforcement once runner wiring is in place) |
| post-edit hook | local (agent loop) | recommended after §3 Phase 4 | regressions introduced during edit cycles |
| visual diff (deterministic) | CI on PR | optional | rendering regressions in critical screens |
| multimodal visual review | CI on PR | optional after §3 Phase 4 | visual issues deterministic checks miss |
| pre-prod smoke | between merge + prod | optional | environment-specific failures |

## 6. Cookbook Patterns

How to add new tests in this project. Each sub-section is filled in once
the relevant rollout phase ships; before that, the sub-section reads
"TBD - see §3 Phase <N>."

### 6.1 Adding a unit test

- TBD - see §3 Phase 1 for critical-path correctness patterns (isolation/import/summary).

### 6.2 Adding an integration test

- **Location**: `transactions/tests.py` and `accounts/tests.py` (app-level integration `TestCase` classes).
- **Pattern**: Drive behavior through HTTP endpoints (`client.get`/`client.post`) and assert DB + response invariants for user-scoped data.
- **Reference tests**:
  - `transactions/tests.py::TransactionCategoryCorrectionTests.test_transaction_list_hides_other_users_transactions`
  - `accounts/tests.py::DashboardSummaryTests.test_dashboard_summary_uses_net_category_amount_when_income_exists`
- **Run locally**: `$env:DEBUG="True" ; pdm run python manage.py test transactions.tests accounts.tests`

### 6.3 Adding an e2e test

- **Current state**: local Playwright CLI smoke is available (`playwright-cli open ...`) for targeted critical-flow checks; formal project-level Playwright runner/CI wiring remains a separate infrastructure track.
- **What local smoke can prove**: limited critical-flow operability (auth entry, core navigation, and selected high-risk happy/negative paths) as an early warning layer.
- **What local smoke cannot prove**: deterministic, repeatable PR-gated e2e enforcement; keep integration tests as the primary deterministic guard until formal runner/CI wiring is complete.
- **Immediate follow-up**: keep `testing-e2e-runner-bootstrap` as the wiring change for minimal project-level runner configuration and CI gate integration.

### 6.4 Adding a test for a new API endpoint

- **Test type**: Django integration test in the owning app's `tests.py`.
- **Required negatives**:
  - foreign-resource access/edit URL returns denial (404-style for queryset-scoped CBVs),
  - invalid payload path preserves existing records.
- **Reference tests**:
  - `categories/tests.py::CategoryOwnershipURLTests.test_edit_url_returns_404_for_foreign_category`
  - `categories/tests.py::CategoryOwnershipURLTests.test_delete_url_returns_404_for_foreign_category`
- **Run locally**: `$env:DEBUG="True" ; pdm run python manage.py test categories.tests`

### 6.5 Adding a test for a new categorization rule

- **Location**: `transactions/tests.py` in `TransactionCategoryCorrectionTests`.
- **Pattern**: Drive correction via `transactions:set_category`, then upload ING CSV and assert categorized outcome for future transactions using merchant variants.
- **Contract guardrails**:
  - assert business outcome (`imported_tx.category`) and mapping presence/removal where needed,
  - avoid implementation-mirror assertions against regex internals or fallback ordering code.
- **Reference tests**:
  - `transactions/tests.py::TransactionCategoryCorrectionTests.test_category_correction_learning_applies_to_normalized_merchant_variants`
  - `transactions/tests.py::TransactionCategoryCorrectionTests.test_overlapping_learned_mapping_prefers_more_specific_merchant_key`
- **Run locally**: `$env:DEBUG="True" ; pdm run python manage.py test transactions.tests`

### 6.6 Per-rollout-phase notes

- Phase 1 shipped risk-first guards for ownership isolation, import integrity, and summary correctness using integration-heavy tests.
- Summary contract was tightened to **net per category** (expenses minus income) while preserving `transaction_count` over all transactions.

## 7. What We Deliberately Don't Test

Exclusions agreed during the rollout (Phase 2 interview, Q5). Future
contributors should respect these unless the underlying assumption changes.

- **Static pages** - low business impact for current risk profile. Re-evaluate if marketing/content pages become conversion-critical. (Source: Phase 2 interview Q5.)
- **Django internals** - framework behavior is already upstream-tested; focus budget on domain/business risks. Re-evaluate if custom framework extensions are introduced. (Source: Phase 2 interview Q5.)
- **Broad low-signal UI snapshots** - avoid suite-wide snapshot sweeps that add maintenance noise without risk-weighted signal. Re-evaluate if deterministic visual diffs become a recurring critical-path requirement.

## 8. Freshness Ledger

- Strategy (§1–§5) last reviewed: 2026-06-03
- Stack versions last verified: 2026-06-03 (includes local Playwright CLI smoke signal)
- AI-native tool references last verified: 2026-06-03

Refresh (`/10x-test-plan --refresh`) when:

- a new top-3 risk surfaces from the roadmap or archive,
- a recommended tool's `checked:` date is older than three months,
- the project's tech stack changes (new framework, new test runner),
- §7 negative-space no longer matches what the team believes.
