# Spend Tracker API

A small Django + Django REST Framework service for logging expenses and getting a spend summary, with JWT auth, filtering, pagination, and a minimal HTML/JS frontend.

**Live demo:** _add your Render URL here after deploying_
**API docs (Swagger):** `<your-url>/api/docs/`

---

## Tech stack

| Layer | Choice |
|---|---|
| Backend | Django 5 + Django REST Framework |
| Auth | JWT (`djangorestframework-simplejwt`) |
| Database | SQLite (local) / PostgreSQL (production, via `DATABASE_URL`) |
| Filtering | `django-filter` |
| API docs | `drf-spectacular` (OpenAPI + Swagger UI) |
| Frontend | Plain HTML/CSS/JS (no build step) |
| Deployment | Render, static files via WhiteNoise |

---

## API Endpoints

All `/api/*` endpoints except `auth/signup` and `auth/login` require `Authorization: Bearer <access_token>`.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/signup` | Register a new user |
| POST | `/api/auth/login` | Get access + refresh tokens |
| POST | `/api/auth/refresh` | Get a new access token |
| GET | `/api/categories` | List the current user's categories |
| POST | `/api/categories` | Create a category |
| GET | `/api/expenses` | List expenses (filterable, paginated) |
| POST | `/api/expenses` | Create an expense |
| GET | `/api/summary` | Total spend, by-category breakdown, month-over-month change, insights |

Every response follows the same shape:
```json
{ "success": true, "message": "...", "data": { ... } }
{ "success": false, "message": "...", "errors": { "field": ["..."] } }
```

### `POST /api/expenses`
```json
// Request
{ "amount": "450.00", "category": 1, "note": "Groceries", "date": "2026-09-15" }
```
Validation: `amount` must be > 0, `date` cannot be in the future (an expense is money already spent), `category` must belong to the requesting user.

### `GET /api/expenses?category=1&start_date=2026-09-01&end_date=2026-09-30&page=1`
Filter params are all optional and combinable. Paginated (`page_size`, default 10, max 100).

### `GET /api/summary?month=2026-09`
`month` defaults to the current calendar month. Returns `total_spend`, `by_category`, `previous_month_total`, `mom_change_percent` (`null` with `mom_change_note` if there's no data from the previous month), and `insights` — categories whose spend rose more than 20% vs. the previous month.

Full request/response examples for every endpoint are in the Swagger UI at `/api/docs/`.

---

## Running locally

```bash
git clone <your-repo-url>
cd spend_tracker
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env            # fill in SECRET_KEY at minimum

python manage.py migrate
python manage.py seed_demo_data # optional: creates demo user + sample data
python manage.py runserver
```

Open `http://localhost:8000/` for the frontend, or `http://localhost:8000/api/docs/` for interactive API docs.

**Demo login:** `demo` / `Demo@1234` (after running `seed_demo_data`)

### Running tests
```bash
python manage.py test
```
51 tests covering models, auth (signup/login/refresh), categories, expenses (validation, ownership, filtering, pagination), and the summary calculation (including the divide-by-zero and first-month edge cases).

---

## Design decisions

- **Category is its own model, not a hardcoded choices list.** Each category is owned by a user (`Category.owner`), so two users can both have "Food" without clashing, and categories can grow richer fields later (a budget limit, a color, an active flag) without touching `Expense` at all.
- **`amount` is a `DecimalField`, never a float.** Floats can't represent values like `0.10` exactly, and that error compounds across running totals — unacceptable for anything finance-adjacent.
- **`Expense.category` uses `on_delete=PROTECT`.** A category that already has real spend recorded against it shouldn't be silently deletable along with that history. There's no category-delete endpoint yet, but the constraint documents the intent for when one is added.
- **Expense dates can't be in the future.** An expense is a record of money already spent; a "planned" expense would be a different feature (e.g. a `Budget` entity), not a relaxed version of this field.
- **Summary calculation lives in `expenses/services.py`, not in the view.** `calculate_summary(user, year, month)` is a pure function the tests call directly — no HTTP roundtrip needed to test the divide-by-zero and empty-month edge cases.
- **One standardized response shape (`ResponseHandler`) and one global exception handler.** Every endpoint — success or failure — returns the same `{success, message, data/errors}` shape, so the frontend (or any client) never has to special-case a particular endpoint's error format.
- **JWT via `djangorestframework-simplejwt`, not hand-rolled.** Token expiry, signature verification and refresh-rotation are exactly the kind of thing not worth re-implementing — a battle-tested library removes a whole class of possible bugs.
- **SQLite locally, PostgreSQL in production, same codebase.** `DATABASE_URL` (absent locally, auto-injected by Render's Postgres add-on) is the only thing that changes — a standard 12-factor pattern, not a rewrite per environment.
- **Login is throttled separately (`5/min`) from the general API rate limit (`100/hour` authenticated, `20/hour` anonymous).** Slows down credential-guessing without affecting normal API usage.
- **Login/refresh error messages never reveal which field was wrong.** "No active account found with the given credentials" is deliberately the same whether the username or the password was incorrect.

## Deployment (Render)

1. Push this repo to GitHub.
2. On Render: **New → Web Service**, connect the repo.
3. **Build Command:**
   ```
   pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
   ```
4. **Start Command:**
   ```
   gunicorn spend_tracker.wsgi:application --bind 0.0.0.0:$PORT
   ```
5. Environment variables: `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS=<your-app>.onrender.com`, and `DATABASE_URL` (auto-filled if you attach Render's free PostgreSQL add-on — recommended, since Render's free web service disk is ephemeral and a SQLite file would be wiped on every restart).
6. Optionally run `python manage.py seed_demo_data` from Render's shell once deployed, so the live demo isn't empty on first look.

Note: Render's free tier spins the service down after 15 minutes of inactivity — the first request after idling can take 30–50 seconds to wake up. That's a platform limitation, not application slowness.

---

## What I'd do differently with more time

- **Object-level update/delete for expenses and categories.** Not asked for in the task, so left out to avoid scope creep, but a real product would need "edit/delete an expense" and probably "rename/merge a category."
- **httpOnly cookies instead of localStorage for JWTs** on the frontend, to reduce XSS exposure — kept as localStorage here for simplicity in a demo.
- **A `min_amount`/`max_amount` filter** on `/expenses` — trivial to add given the `django-filter` setup already in place.
- **Recurring/planned expenses as a separate `Budget` or `PlannedExpense` model**, rather than relaxing the "no future dates" rule on `Expense`.
- **Structured logging + request IDs** for production observability, and a generic 500 message (already done) paired with proper error tracking (Sentry or similar) rather than just server logs.
- **Rate limiting backed by Redis** instead of Django's default local-memory cache, so throttle counts are consistent across multiple server processes/instances in production.
