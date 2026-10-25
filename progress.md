# Finance Tracker — project notes

Personal finance tracker for daily use (Django REST Framework + React/Vite), inspired by Fold, Monarch and YNAB. Built incrementally: plan small → design → build → test → refine → plan next. Prefers learning by building, with reasoning explained before the code.

## Setup (handoff notes)
- Backend: Django + DRF in `financetracker/` (project package `config`, app `finance`), Windows / PowerShell, virtualenv in `venv/`
- Frontend: Vite + React (JavaScript) in a sibling folder `financetracker-frontend/`, axios instance with a request interceptor that attaches the JWT
- Auth: simplejwt access + refresh tokens, stored in localStorage; automatic token refresh is not built yet
- Models: Account (stored `current_balance`, updated by Transaction save/delete), Category, Transaction, Budget
- Key decisions: INR only; a transfer is two linked Transaction rows (both `type='transfer'`, `transfer_direction` out/in); balance logic lives in the model; budget stats are computed live in the serializer; ownership of related objects is validated in the serializers

## Full feature spec (from the Excalidraw flowchart)
1. Auth: Intro/onboarding, Signup (username/email/password), Login, first-login welcome, possible Google login
2. Global UI: Sidebar (Dashboard, Transactions, Accounts, Reports, Budget, Categories, Recurring, Profile, Logout), light/dark mode, global "Add Transaction" button
3. Dashboard: total balance, total income, total expenses, net cash flow (income − expenses), recent 5-10 transactions, upcoming recurring payments, GitHub-style activity calendar (days with activity), transaction/activity counter
4. Transactions: full history, add income/expense/transfer, search/filter/sort, CSV export, possible CSV import
5. Accounts: bank/cash/wallet/credit card/investment, add/edit/deactivate (not delete), balance + per-account transaction history
6. Reports: income/expenses/net cash flow/total balance, spending & income by category/account/time period, income-vs-expense charts, trend charts, cash-flow analysis, savings/money retained, filters+sorting — analysis-focused, not duplicating the dashboard
7. Budget: total budget/spent/remaining/% used, category-based weekly/monthly budgets, create/edit, budget history, threshold/over-budget alerts, optional rollover of unused budget
8. Categories: categories + subcategories, add/edit, icons/colors, show spending/usage, unused categories can be deleted, used categories become inactive instead of being deleted
9. Recurring: recurring expenses + income, amount/category/account/frequency/next date, monthly/yearly/lifetime cost, upcoming payments, add/edit/pause/delete, future automatic transaction generation
10. Profile: account settings, theme + notification preferences, password/logout

## Build status

### Done (backend + frontend working and tested)
- Django + DRF backend, JWT auth (register/login/logout), per-user data isolation; ownership validation on Transaction (account, category, to_account), Budget (category) and Category (parent) serializers
- Accounts: model, CRUD API, UI (add, list, deactivate/reactivate with a collapsible "Deactivated" section)
- Categories: model, CRUD API, UI (add, list); backend blocks delete when transactions reference the category; UI shows Delete only when unused, Deactivate/Reactivate always
- Transactions: income/expense/transfer with balance sync on create/update/delete; two bugs diagnosed and fixed (cascade-delete bypass, stale-object double-save)
- Transactions UI: add, list, edit (income/expense only — transfers are edit-locked because editing would desync the linked pair), delete, filtering via django-filter (account/category/type/date range)
- React Router + sidebar shell (Dashboard/Transactions/Accounts/Categories/Budget); App.jsx owns shared state, split into `transactions` (full set, used by Dashboard) and `filteredTransactions` (Transactions page only)
- Dashboard: total balance, this-month income/expenses/net cash flow, recent 10 transactions
- Budget: one row = one category + one period instance (start_date/end_date, weekly or monthly); spent/remaining/percent_used/effective_amount computed live (cached once per budget per request); rollover compounds across periods; date validation (end after start, no overlaps for the same category + period type)
- Budget UI: add/edit form (category and period type locked while editing), list grouped monthly/weekly with progress bars and 80%/100% colour thresholds, weekly date-range label, rollover text, delete

### Not started
- Budget history view: month dropdown (pick October → all October monthly and weekly budgets), possibly alongside current/past; undecided which month a weekly budget crossing a month boundary belongs to
- Dashboard activity calendar (GitHub-style) + transaction counter
- Recent Transactions still shows both legs of a transfer separately (future polish: show only the 'out' leg)
- Accounts as its own page with per-account transaction history
- Reports page (charts — needs a charting library + aggregation queries)
- Recurring feature (incl. future automatic transaction generation)
- Categories: subcategory UI (parent field exists on the model, unused), icons/colors
- CSV import/export
- Profile page (settings, theme/notification prefs)
- Signup page UI, intro page, first-login welcome popup, dark mode toggle
- Real styling — everything is unstyled HTML currently

## Agreed roadmap for what's left
Budget history (month dropdown) → Accounts page → Recurring → Reports/charts → Categories polish (subcategories, icons/colors) → CSV import/export → Profile, signup/intro/onboarding, dark mode, styling pass