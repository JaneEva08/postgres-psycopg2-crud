import os
from contextlib import contextmanager

import psycopg2
from dotenv import load_dotenv


class PostgresDriver:
    """Драйвер для работы с базой users/orders в PostgreSQL."""

    def __init__(self, config=None):
        load_dotenv()
        defaults = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432"),
            "dbname": os.getenv("DB_NAME", "test"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", ""),
            # без этого сообщения сервера на русской локали Windows приходят в
            # cp1251, а psycopg2 падает с UnicodeDecodeError вместо реальной ошибки
            "options": "-c lc_messages=C",
        }
        self.config = {**defaults, **(config or {})}
        self.connection = None

    def connect(self):
        self.connection = psycopg2.connect(**self.config)
        return self.connection

    def close(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @contextmanager
    def transaction(self):
        """Курсор для нескольких операций в одной атомарной транзакции."""
        with self.connection, self.connection.cursor() as cur:
            yield cur

    def create_tables(self):
        with self.transaction() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    age INT CHECK (age >= 0)
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    amount NUMERIC(10,2) NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)

    def add_user(self, name, age, cur=None):
        if cur is not None:
            cur.execute(
                "INSERT INTO users (name, age) VALUES (%s, %s) RETURNING id;",
                (name, age),
            )
            return cur.fetchone()[0]
        with self.transaction() as cur:
            return self.add_user(name, age, cur=cur)

    def add_order(self, user_id, amount, cur=None):
        if cur is not None:
            cur.execute(
                "INSERT INTO orders (user_id, amount) VALUES (%s, %s) RETURNING id;",
                (user_id, amount),
            )
            return cur.fetchone()[0]
        with self.transaction() as cur:
            return self.add_order(user_id, amount, cur=cur)

    def has_users(self):
        with self.transaction() as cur:
            cur.execute("SELECT EXISTS(SELECT 1 FROM users);")
            return cur.fetchone()[0]

    def get_all_users(self):
        with self.transaction() as cur:
            cur.execute("SELECT id, name, age FROM users ORDER BY id;")
            return cur.fetchall()

    def get_user_totals(self):
        with self.transaction() as cur:
            cur.execute("""
                SELECT u.name,
                       COALESCE(SUM(o.amount), 0) AS total_amount
                FROM users u
                LEFT JOIN orders o ON o.user_id = u.id
                GROUP BY u.id, u.name
                ORDER BY total_amount DESC;
            """)
            return cur.fetchall()
