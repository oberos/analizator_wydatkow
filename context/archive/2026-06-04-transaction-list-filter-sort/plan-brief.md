# Transaction List Filtering & Sorting — Plan Brief

> Full plan: `context/changes/transaction-list-filter-sort/plan.md`  
> Roadmap ref: `context/foundation/roadmap.md` (S-05, depends on S-02, S-03, S-04)

## What & Why

Add filtering by category and sorting by Date/Amount to the transaction list so users can find, organize, and understand their spending. As transaction history grows into hundreds of entries (especially post-CSV-import), a flat list becomes unusable. FR-013 (filter by category) and FR-014 (sort by column) are must-have requirements from the PRD.

## Starting Point

The transaction list currently displays all user transactions in a simple table with no filtering, sorting, or pagination. The backend enforces user isolation via `.filter(user=self.request.user)`, and the frontend has an inline category editor (dropdown per row) but no list-level controls. Roadmap S-05 depends on S-02 (CSV import, ✓ done) and S-03 (category correction, ✓ done), so this slice is ready to build.

## Desired End State

User lands on `/transactions/` and sees a filter dropdown ("All Transactions" or a category name) and two sort buttons (Date ↕, Amount ↕) next to the title. Clicking the dropdown filters to that category; clicking a sort button toggles ascending/descending. Both controls update the URL query params (e.g., `?category=Food&sort_by=date&sort_order=desc&page=2`), which persist across page reloads and are bookmarkable. If a filter returns zero results, a contextual message appears ("No transactions in Food found") with a "Clear Filters" option. Pagination shows at the bottom if results exceed 50 per page.

## Key Decisions Made

| Decision | Choice | Why | Source |
| --- | --- | --- | --- |
| Filter/sort control placement | Next to title with dropdowns/buttons | Inline and always visible — no modal, no above-table bar | Planning Q1 |
| Simultaneous filters/sorts | One category + one sort column at a time | Simpler UX and implementation than multi-select; covers 90% of use cases | Planning Q2 |
| Sortable columns | Date and Amount only (exclude Category) | Most useful for spending analysis; Category is already the primary filter | Planning Q3–Q4 |
| Sort direction control | Click button to toggle ascending ↔ descending | Familiar pattern; easier than three-state cycle | Planning Q5 |
| State persistence | URL query parameters | Shareable, bookmarkable, survives reload, survives context compression, SEO-safe — beats localStorage or session state | Planning Q8 |
| Form submission | Auto-submit (no "Apply" button) | Instant feedback; URL updates immediately; matches modern SPA expectations | Planning Q9 |
| Pagination | 50 rows per page with page nav controls | Balances UI clarity against initial load time; resets to page 1 when filter/sort changes to avoid "empty page 5" | Planning Q6 |
| Empty result state | Message with category name + inline Clear option | Helpful ("No transactions in Food") not confusing; easy recovery without leaving the page | Planning Q7 |
| Reset mechanism | "All Categories" in dropdown + "Clear Filters" button | Two convenient paths: quick in dropdown for category-only resets, explicit button in header for full reset | Planning Q10 |

## Scope

**In scope:**
- Category filtering (one category at a time, or "All")
- Sorting by Date or Amount (ascending/descending toggle)
- Pagination (50 rows per page, numbered page nav)
- URL query parameter persistence (`?category=X&sort_by=Y&sort_order=Z&page=N`)
- Empty result messaging with Clear Filters option
- Responsive design (mobile-friendly controls and pagination)
- Accessibility (aria-labels, keyboard navigation, color contrast)

**Out of scope:**
- Multi-select filtering (out of complexity budget; one category at a time)
- Merchant or Description column sorting (less actionable than Amount/Date)
- Full-text search or transaction lookup (separate feature; would require search infrastructure)
- Custom date-range filtering beyond what the dashboard provides
- Client-side state (localStorage) — URL params are the single source of truth
- CSV re-import or data refresh within the list view

## Architecture / Approach

**Backend** (`transactions/views.py`): Parse `category`, `sort_by`, `sort_order`, `page` from GET params. Chain querysets: `.filter(user=self.request.user).filter(category__name=category).order_by(sort_field)`. Use Django Paginator to split into 50-row pages. Pass filter/sort/page state to template context.

**Frontend** (`transaction_list.html` + JS): Render category dropdown and sort buttons next to the title. Wire auto-submit on change (no explicit Apply button). Pre-populate controls from URL params on load. Render page navigation links at the bottom, each preserving the current filter/sort.

**Data**: No schema changes. Index on `(user, category, transaction_date)` for query performance as volume grows.

## Phases at a Glance

| Phase | What it delivers | Key risk |
| --- | --- | --- |
| 1. Backend filtering & sorting | `TransactionListView` parses params, applies filters/sorts, paginates; passes state to template | Missing edge case (invalid param, category doesn't exist) — caught by integration tests |
| 2. Frontend UI & auto-submit | Category dropdown, sort buttons, Clear button in header; JavaScript form auto-submission and URL updates | JavaScript event binding bugs or URL param encoding issues — caught by manual testing |
| 3. Pagination & state persistence | Page reset on filter change, edge case handling (page > num_pages), URL bookmark/back-button restoration | Subtle off-by-one in page reset logic — caught by browser-based manual tests |
| 4. Empty state, polish & a11y | Empty result message, responsive design, keyboard navigation, sort direction indicators | Accessibility violations or mobile layout breaks — caught by responsive testing and axe-core scan |

**Prerequisites:** 
- CSV import (S-02) and category correction (S-03) complete ✓
- Dashboard (S-04) complete ✓
- Django project running with transaction data available

**Estimated effort:** ~2–3 sessions across 4 phases

## Open Risks & Assumptions

- **Risk**: Pagination performance if a single category grows to 10,000+ transactions. *Mitigation*: Database index on `(user, category, transaction_date)` from Phase 1; if pagination slows, can defer to infinite-scroll or server-side filtering optimization in a future slice.
- **Assumption**: URL param names are safe for query strings and don't collide with Django internals. *Verification*: Common names like `category`, `sort_by`, `sort_order`, `page` are standard; Django GET params are case-sensitive and isolated to request, so no collision risk.
- **Assumption**: Frontend framework is plain Django templates (no React/Vue). *Verification*: Confirmed — project uses Django templates; JavaScript is minimal and vanilla.

## Success Criteria (Summary)

- ✓ User can filter transactions by a single category via dropdown; URL reflects the filter state and persists across reload
- ✓ User can sort by Date or Amount ascending/descending with visual indicators; clicking toggles direction
- ✓ Filter + sort work simultaneously (one category + one sort column)
- ✓ Pagination shows at bottom if >50 transactions; page nav links preserve filter/sort state
- ✓ Empty result state displays helpful message when filter returns zero transactions
- ✓ Bookmarked/shared URLs restore exact filter/sort/page state
- ✓ All tests pass (unit, integration, accessibility); no regressions in existing features
