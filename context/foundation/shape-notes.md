---
project: "Analizator Wydatkow"
context_type: greenfield
created: 2026-05-26
updated: 2026-05-26
checkpoint:
  current_phase: 8
  phases_completed: [1, 2, 3, 4, 5, 6, 7]
  gray_areas_resolved:
    - topic: "auth strategy"
      decision: "login-based (email/password or OAuth); flat user model, no roles"
    - topic: "MVP timeline"
      decision: "3 weeks work hours"
    - topic: "charts in MVP"
      decision: "no — table summary only; not a firm non-goal"
    - topic: "CSV format"
      decision: "ING Poland only; README fallback for format changes"
    - topic: "scale model"
      decision: "per-user learning, no shared patterns"
  frs_drafted: 14
  quality_check_status: accepted
---

# Shape Notes: Expense Analyzer

Seed idea (from my_idea.md):

> **Problem**: Bank app categorization is insufficient and doesn't allow custom categories needed for effective household budget management.
>
> **MVP scope**:
> - Read transaction history from CSV
> - Categorize individual transactions
> - Edit transaction categories
> - CRUD on categories
> - Summary table with totals per category
>
> **Out of scope**: Bank API integration, charts
>
> **Success criterion**: 80% of transactions have a category instead of landing in "Unknown"

---

## Vision & Problem Statement

**Pain**: Bank categories don't match the real spending categories I care about. Every month I export my bank statement as CSV, open it in Excel, and spend about an hour manually fixing categories before I can see how much I actually spent across different areas.

**Pain category**: Workflow friction — the task is doable today but tedious and slow.

**Insight**: Polish bank apps lack category flexibility; you cannot add custom categories or assign them to specific transactions. Global tools (YNAB, Mint) require direct bank connection — a security concern — and treat CSV import as an afterthought, not tuned for Polish bank formats.

## User & Persona

**Primary persona**: Myself — a single user managing a household budget, reviewing spending monthly via exported CSV.

**Context**: After exporting a monthly CSV from my Polish bank, I want to quickly see spending breakdown by my own categories (not the bank's generic ones) without an hour of manual Excel work.

## Access Control

**Auth model**: Login-based (email + password or OAuth) — enables multi-device sync.

**Role model**: Flat — single user, no roles. Every authenticated user sees only their own data; no admin/viewer distinction in MVP.

## Success Criteria

### Primary
- 80% of transactions have a real category instead of landing in "Unknown"

### Secondary
- User can compare spending month-over-month (multiple CSV imports persisted)

### Guardrails
- Transaction data must never leave the user's account or be visible to others

## MVP Flow

1. User logs in
2. User uploads a CSV file (exported from Polish bank)
3. User sees transactions with auto-proposed categories
4. User refines/corrects the assigned categories
5. User sees the summary table with totals per category

**Timeline**: ~3 weeks of after-hours work

## Functional Requirements

### Authentication
- FR-001: User can register a new account. Priority: must-have
  > Socrates: Counter-argument considered: "registration friction causes abandonment." Resolution: kept; login system is a certification requirement, and enables multi-device sync.
- FR-002: User can log in to their account. Priority: must-have

### Transaction Import
- FR-003: User can upload a CSV file with bank transactions. Priority: must-have
  > Socrates: Counter-argument considered: "CSV format might change or vary across banks." Resolution: kept; MVP targets ING Poland CSV format only. README will document manual CSV preparation as fallback.
- FR-004: User can view transactions with auto-proposed categories. Priority: must-have
  > Socrates: Counter-argument considered: "auto-categorization is hard; manual-only might be safer." Resolution: kept; auto-categorization is the core value proposition that differentiates from Excel.

### Categorization
- FR-005: User can edit the category assignment for a single transaction. Priority: must-have
  > Socrates: Counter-argument considered: "single-transaction editing is tedious for bulk errors." Resolution: kept; bulk edit added as FR-012 (nice-to-have).
- FR-006: User can create a custom category. Priority: must-have
  > Socrates: Counter-argument considered: "predefined categories might be enough." Resolution: kept; predefined categories will be provided, but user can add new ones.
- FR-007: User can edit a custom category. Priority: must-have
- FR-008: User can delete a custom category. Priority: must-have
- FR-012: User can bulk-edit category assignments for multiple transactions. Priority: nice-to-have

### Reporting
- FR-009: User can view a summary table with spending totals per category. Priority: must-have
  > Socrates: Counter-argument considered: "summary hides outliers." Resolution: kept; drilldown achieved via filtering transaction list by category + sorting.
- FR-010: User can define a budget cycle (custom date range, e.g., paycheck to paycheck). Priority: must-have
  > Socrates: Counter-argument considered: "calendar months would be simpler." Resolution: kept; paycheck-aligned cycles are essential for user's workflow.
- FR-011: User can filter transactions by budget cycle. Priority: must-have
- FR-013: User can filter transactions by category. Priority: must-have
- FR-014: User can sort the transaction list by any column. Priority: must-have

## User Stories

### US-01: User categorizes monthly transactions

- **Given** a logged-in user with a CSV file from their Polish bank
- **When** they upload the CSV
- **Then** they see transactions with auto-proposed categories, can refine them, and view a summary table showing spending totals per category

#### Acceptance Criteria
- Auto-proposed categories appear immediately after CSV upload
- User can change any transaction's category with a single action
- Summary table updates in real-time as categories are refined
- 80% of transactions should have a non-"Unknown" category after auto-categorization

## Business Logic

**The app assigns a category to each transaction based on merchant name and transaction description, using learned patterns from the user's previous corrections.**

**Inputs**: Merchant name and transaction description fields from the CSV. Amount and date are irrelevant for categorization.

**Output**: A single category per transaction. If no pattern matches, the category defaults to "Unknown" for later manual assignment.

**Learning mechanism**: When the user corrects a transaction's category, the app remembers the merchant-to-category mapping. Future transactions from the same merchant are auto-categorized using this learned rule.

**Predefined categories**: A starter set of common categories (e.g., Groceries, Transport, Entertainment, Bills, Health) ships with the app. Users can edit these or add new custom categories.

## Non-Functional Requirements

- CSV upload and auto-categorization must complete within 30 seconds for a typical monthly statement (~100-300 transactions)
- Transaction data must be stored securely in the database; no data leakage between user accounts
- The app must work on Chromium-based browsers (Chrome, Edge, Brave)
- Data retention policy: not defined for MVP (indefinite retention)

## Product Framing

- **Product type**: web-app
- **Target scale**: small (just me, or a handful of users)
- **Timeline**: ~3 weeks (work hours, not after-hours)
- **Hard deadline**: none
- **Scale insight**: At 100x scale, learning would remain per-user (no shared patterns across users)

## Non-Goals

- **No direct bank API connection** — Security concern; CSV import is the only data ingestion path. This avoids storing bank credentials and reduces attack surface.
- **No multi-bank support** — MVP targets ING Poland CSV format only. Other banks can be added post-MVP.
- **No mobile app** — Web-only for MVP. Responsive design for mobile browsers is acceptable, but no native app.
- **No shared/family accounts** — Single-user model only. Each account is isolated; no sharing or delegation of access.

