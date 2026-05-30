# Change: csv-import-autocategorize

- **Status**: impl_reviewed
- **Created**: 2026-05-30
- **Updated**: 2026-05-30
- **Roadmap ref**: S-02
- **PRD refs**: FR-003, FR-004, US-01

## Summary

CSV import with auto-categorization — the north star feature. Users upload ING Poland CSV files, transactions are parsed and auto-categorized using normalized merchant prefix matching with learned mappings.

## Key Decisions

| Decision | Choice |
|----------|--------|
| App structure | New `transactions` app |
| Amount storage | DecimalField (2 decimal places) |
| Matching algorithm | Normalized merchant prefix |
| Mapping storage | Separate MerchantCategoryMapping model |
| Duplicates | Skip silently (match on date+amount+merchant+tx_number) |
| Malformed CSV | Abort with clear error (line number + issue) |
| Upload UI | Modal from transaction list |
| Processing | Synchronous (no Celery) |
| Uncategorized display | Show with "Unknown" badge |
| Manual editing | Out of scope (S-03) |
| File persistence | Process in memory only |
| Testing | Skip for MVP (manual verification) |
| Predefined mappings | Seed ~60 Polish merchants (Biedronka, Lidl, Orlen, McDonald's, etc.) |
| Delete transactions | "Delete All" button for fresh start |
