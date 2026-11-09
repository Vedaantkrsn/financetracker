# Finance Tracker — project progress

Personal finance tracker built with Django REST Framework and React/Vite. The user prefers to learn by implementing changes themselves, so explain code and share it in chat unless they ask for direct edits.

## Project layout
- Backend: `financetracker/` (Django project package `config`, app `finance`, virtualenv `venv/`).
- Frontend: sibling `financetracker-frontend/` (React, Vite, JavaScript).
- API client: frontend `src/api/axios.js`; attaches the JWT access token from localStorage.
- Currency: INR (₹).
- Transfers are represented by two linked transaction rows with `transfer_direction` set to `out`/`in`; transaction model logic adjusts account balances.
- Per-user data is scoped in API querysets and related-object ownership is validated by serializers.

## Current implementation

### Backend
- Django REST Framework API with JWT authentication, registration endpoint (`POST /api/register/`), token obtain and refresh endpoints.
- Finance models/API for accounts, categories, transactions, budgets, and recurring transactions.
- User ownership on finance records; API viewsets filter querysets by `request.user` and assign owner on create.
- Related-object ownership validation for transaction account/category/transfer destination, budget category, recurring account/category, and category parent.
- Transactions support income, expense, and transfers; account balances update on create/update/delete. Filtering supports account, category, transaction type, date range, and min/max amount.
- Budgets support weekly/monthly periods, date/overlap validation, live spend/remaining/percent/effective amount calculations, and rollover.
- Recurring transactions support weekly/monthly/yearly frequency, due date advancement, manual post, skip, pause/resume, and computed monthly/yearly/lifetime totals.
- Reports endpoint aggregates summary metrics, trends, categories, and accounts for the authenticated user's transactions.

### Frontend
- Login screen with JWT token storage and dark organic/orbital styling. Registration UI is not yet connected to the existing backend endpoint.
- Sidebar navigation and responsive app shell for Dashboard, Transactions, Accounts, Categories, Budgets, Recurring, and Reports; logout clears stored tokens.
- Dashboard: total active balance, current-month income/expenses/net, latest 10 transactions, and in-app list of recurring items due within 30 days (including overdue items).
- Transactions: add/edit/delete income and expense rows, transfer creation (transfer rows are not editable), account/category/type/date filters, dark responsive list and form styling.
- Accounts: add/list/deactivate/reactivate, active balance summary, account type/institution/balance cards, paused-account section.
- Categories: add/list, income/expense counts, deactivate/reactivate, delete when unused, archived category section.
- Budgets: add/edit/delete, monthly/weekly grouping, period selector, usage progress, near-limit/over-budget status, rollover display.
- Recurring: add/edit/delete, post/skip, pause/resume, due-state labels, monthly inflow/outflow summary, paused section.
- Reports: date/account/category filters, summary metrics, income-vs-expense and net cash-flow charts, category and account tables.
- Dark organic visual system (rounded panels, orbital/circular accents, responsive layouts) applied to the main pages and login.

## V1 scope and status
V1 is considered complete after the following remaining items are implemented and the main flows are manually checked:

- [ ] Add frontend sign-up mode/form using existing `POST /api/register/`, then sign in through the existing JWT token endpoint. Backend registration and per-user data ownership already exist.
- [ ] Add transaction search (description, account, category, amount, date, type) and quick filters (for example: income, expenses, transfers, this month). Existing account/category/type/date filters already work.
- [ ] Add dashboard budget alerts for active budgets at 80% usage and over budget. Example implementation was shared in chat but has not been added to the project.
- [ ] Manually verify sign-up, login, ownership isolation across two users, transaction filtering/search, budget thresholds, recurring post/skip, and responsive layouts.

Recurring due reminders are already shown in-app on the dashboard. Scheduled email/browser/push notifications while the app is closed are not implemented and are outside the current V1 scope.

## Possible post-V1 work
- CSV import/export.
- Dashboard activity calendar and transaction count.
- Per-account transaction history.
- Category subcategory UI and icon/color customization.
- Profile/settings and light/dark theme toggle.
- Automated recurring transaction generation or external notifications.
- Refresh-token renewal UX and broader deployment/security review.

## Working preference
Explain the implementation in small, understandable pieces and provide code in chat for the user to apply, unless the user explicitly asks for direct project edits.
