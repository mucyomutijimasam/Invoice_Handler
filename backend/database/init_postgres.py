#database/init_postgres.py
from database.connection import get_db

def init_db():
    """
    Only ensures required Postgres extensions exist.
    Table creation is handled by Alembic migrations.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')
            conn.commit()

    print("✅ Postgres extensions verified.")

if __name__ == "__main__":
    init_db()
