import psycopg2

from postgres_driver import PostgresDriver


def seed_data(db):
    """Заполняет базу тестовыми пользователями и заказами одной транзакцией, если она пустая."""
    if db.has_users():
        return

    with db.transaction() as cur:
        alice_id = db.add_user("Alice", 28, cur=cur)
        bob_id = db.add_user("Bob", 34, cur=cur)
        db.add_user("Charlie", 22, cur=cur)  # без заказов — для проверки LEFT JOIN

        db.add_order(alice_id, 499.90, cur=cur)
        db.add_order(alice_id, 150.00, cur=cur)
        db.add_order(bob_id, 320.50, cur=cur)


def main():
    try:
        with PostgresDriver() as db:
            db.create_tables()
            seed_data(db)

            print("=== Базовый уровень: пользователи ===")
            for row in db.get_all_users():
                print(row)

            print("\n=== Средний уровень: сумма заказов по пользователю ===")
            for name, total in db.get_user_totals():
                print(f"{name} — {total}")
    except psycopg2.Error as e:
        print(f"Ошибка работы с PostgreSQL: {e}")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")


if __name__ == "__main__":
    main()
