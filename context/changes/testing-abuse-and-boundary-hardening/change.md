---
change_id: testing-abuse-and-boundary-hardening
title: Rollout phase 3: abuse and boundary hardening tests
status: implemented
created: 2026-06-18
updated: 2026-06-18
archived_at: null
---

## Notes

Open a change folder for rollout Phase 3 of context/foundation/test-plan.md: "Abuse and boundary hardening". Risks covered: #5 Authenticated user bypasses ownership checks (IDOR-style read/update on foreign resources); #6 Budget-cycle boundaries are computed incorrectly; #4 Summary table shows wrong totals under filtering/sorting. Test types planned: integration/security negatives. Risk response intent: - #5: prove foreign-resource requests are rejected even with a valid session. - #6: prove paycheck-cycle boundaries include/exclude transactions exactly per rules. - #4: prove report totals exclude income and remain correct under active filter/sort combinations. After creating the folder, follow the downstream continuation rule.