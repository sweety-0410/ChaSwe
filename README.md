# ChaSwe Cookie Store

A runnable full-stack cookie shop starter with an original responsive storefront, FastAPI backend, SQL database, customer accounts, database-backed cart, Cash on Delivery checkout, order history, and admin product/order APIs.

## Run on Windows
1. Install Python 3.11+.
2. Extract this ZIP and open the `ChaSwe` folder in VS Code.
3. In the VS Code terminal:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

If activation is blocked, run:
` .\.venv\Scripts\python.exe -m pip install -r requirements.txt `
then
` .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload `

4. Open http://127.0.0.1:8000. API docs: http://127.0.0.1:8000/docs.
5. Change `SECRET_KEY`, `ADMIN_EMAIL`, and `ADMIN_PASSWORD` in `.env` before using it beyond local testing.

SQLite is the default for a simple first run. For PostgreSQL, create a `chaswe` database and set:
`DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/chaswe`

## Included
- Original ChaSwe storefront, product grid, category filters and search
- Registration/login with hashed passwords and JWT authentication
- SQL-persisted cart, server-side stock and price checks
- COD order placement, stock deduction and customer order history
- Admin-only product and order APIs (use `/docs` while signed in)
- Initial sample products and admin account created at first startup

## Important before launch
This is a runnable full-stack foundation, not a certified production deployment. Before taking public orders, configure HTTPS, production secrets, PostgreSQL backups, rate limiting, monitoring, email/SMS notifications, delivery zones, accurate tax/shipping rules, privacy/terms/refund policies, food/allergen/shelf-life disclosures, and operational fulfilment. COD is implemented; no online card/UPI payment is represented as integrated. Add a verified payment provider only after obtaining merchant credentials. Replace sample imagery, products and prices with your own licensed business assets.

The Canva website is used only as visual inspiration. This project has original code and content.
