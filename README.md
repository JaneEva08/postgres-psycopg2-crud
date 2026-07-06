[🇷🇺 Русский](README.ru.md) | 🇬🇧 English

# PostgreSQL CRUD Driver on psycopg2

A lightweight PostgreSQL driver built on top of `psycopg2` — no ORM, just
plain SQL, parameterized queries, and explicit transactions. Useful when you
need to connect to a database, run CRUD operations, and get an aggregated
result without pulling a heavy ORM into the project for a couple of queries.

Using two related tables (`users` and `orders`) as an example, it shows how
to: connect via `.env`, insert data safely, atomically group several
operations into one transaction, and calculate per-user order totals with a
`LEFT JOIN`.

## Prerequisites

- PostgreSQL installed and running (local or remote).
- A `test` database created in pgAdmin (or psql) — the default `public`
  schema is used, no need to create one separately.

## Installation

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and fill in your values:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=test
DB_USER=postgres
DB_PASSWORD=...
```

## Running

```powershell
python main.py
```

On first run the script creates the `users` and `orders` tables
(`CREATE TABLE IF NOT EXISTS`) and, if `users` is empty, seeds it with test
users and orders in a single transaction. Data won't be duplicated on
subsequent runs.

## What main.py does

1. Reads and prints all users (`SELECT * FROM users`).
2. Calculates per-user order totals via `LEFT JOIN` + `SUM` + `GROUP BY`,
   sorted by total descending, printed as `Name — Total`.
3. Both `psycopg2.Error` and any unexpected exceptions are caught, and the
   connection is always closed (via the `with PostgresDriver() as db`
   context manager).

## Cyrillic output in the Windows console

If the console shows garbled characters instead of Russian text, it's a
console/UTF-8 encoding mismatch — it doesn't affect the data. Fix the
display by running this before launching the script:

```powershell
chcp 65001
```

## Verifying ON DELETE CASCADE

To confirm that the `orders.user_id → users.id` relationship cascades on
delete: remove a user with existing orders in pgAdmin and check that their
orders disappear automatically.

## Structure

- `main.py` — entry point, demonstrates how the driver is used.
- `postgres_driver.py` — the driver: `create_tables`, `add_user`,
  `add_order`, `has_users`, `get_all_users`, `get_user_totals`,
  `transaction` (a context manager for grouping several operations into one
  atomic transaction).
- `requirements.txt` — dependencies (`psycopg2-binary`, `python-dotenv`).
- `.env.example` — sample environment variables (no secrets).
