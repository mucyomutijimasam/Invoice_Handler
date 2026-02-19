#auth/repository.py
import uuid
import psycopg2
from database.connection import get_db
from psycopg2.extras import RealDictCursor

def create_user(username, password_hash, tenant_id, role="member"):
    """
    Matches your 'initial_setup' migration:
    Columns: id (UUID), username, hashed_password, tenant_id, role
    """
    query = """
    INSERT INTO users (id, username, hashed_password, tenant_id, role)
    VALUES (%s, %s, %s, %s, %s);
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            # We generate a UUID here because the migration doesn't do it automatically for 'users'
            user_id = str(uuid.uuid4())
            cur.execute(query, (user_id, username, password_hash, tenant_id, role))
            conn.commit()

def get_user_by_username(username):
    """
    Retrieves user using the correct column 'hashed_password'.
    """
    query = """
    SELECT id, username, hashed_password, tenant_id, role
    FROM users
    WHERE username = %s;
    """
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (username,))
            return cur.fetchone()