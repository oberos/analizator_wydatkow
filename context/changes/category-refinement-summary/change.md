# Change: category-refinement-summary

- **Status**: impl_reviewed
- **Created**: 2026-06-02
- **Updated**: 2026-06-02
- **Roadmap ref**: S-03
- **PRD refs**: FR-005, FR-009, US-01

## Summary

Add category refinement for individual transactions and expose category spending totals so the user can complete the "upload -> refine -> summary" flow in MVP.

## Key Decisions

| Decision | Choice |
|----------|--------|
| Edit location | Transactions page (single-action per row) |
| Summary location | Dashboard page |
| Learning behavior | Update mapping on correction; remove mapping when set to Unknown/empty |
| Summary strategy | On-demand ORM aggregation from Transaction rows |
| Scope cut policy | Keep edit + learning + basic totals; defer polish/extras |
| Performance target | MVP scale (hundreds to low-thousands per user), no caching |
