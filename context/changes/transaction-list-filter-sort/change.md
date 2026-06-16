# Transaction List Filtering & Sorting

**Status**: implementing  
**Created**: 2026-06-04  
**Updated**: 2026-06-16  
**Roadmap**: S-05 (depends on S-02, S-03, S-04)

## Summary

Add filtering by category and sorting by Date/Amount to the transaction list UI. Users can filter to a single category (or view all), sort ascending/descending by column, and navigate through paginated results. Filter and sort state persists in URL query parameters for shareability and bookmarkability.

## Why

Roadmap S-05 depends on completed CSV import (S-02) and category correction (S-03). Users need visibility and control over transaction volumes, especially as their transaction history grows into hundreds or thousands of entries. Filtering by category and sorting by date/amount are FR-013 and FR-014 (must-have requirements from PRD).

## Scope

**In scope:**
- Category filtering (one category at a time, or "All")
- Sorting by Date or Amount (ascending/descending toggle)
- Pagination (Django paginator)
- URL query parameter persistence (filter, sort_by, sort_order, page)
- Empty result messaging with clear-filters option
- "All Categories" dropdown entry and separate "Clear Filters" button

**Out of scope:**
- Multi-select filtering (keep to one category per view)
- Search/full-text transaction lookup
- Custom date-range filtering (beyond dashboard date ranges, if any)
- Merchant or Description column sorting
- Category sorting (already primary filter; sorting by it is redundant)
- Client-side state (localStorage); URL params are the single source of truth

## Key Decisions

| Decision | Choice | Why |
| --- | --- | --- |
| Filter/sort control placement | Next to title with quick-access dropdowns | Inline and visible without scrolling |
| Sortable columns | Date and Amount only | Most useful for transaction review; Category is filter-only |
| Sort direction control | Click column header to toggle up/down | Familiar UI pattern; easier than cycle-through |
| State persistence | URL query parameters | Shareable, bookmarkable, survives page reload, SEO-safe |
| Form submission | Auto-submit on dropdown/sort change | Instant feedback; URL updates automatically |
| Empty results UI | Context message ("No transactions in X") + clear option | Helpful, not confusing; easy recovery |
| Reset mechanism | "All Categories" in dropdown + "Clear Filters" button | Two paths: quick in dropdown, explicit in header |
