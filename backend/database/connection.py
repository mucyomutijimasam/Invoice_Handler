#database/connection
import os
import psycopg2
from urllib.parse import quote_plus  # <--- Add this import
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# --- THE FIX ---
# This turns "Passcode@250$$15" into "Passcode%40250%24%2415"
# Now the @ in the password won't be confused with the @ for the host.
safe_password = quote_plus(DB_PASS) if DB_PASS else ""

DATABASE_URL = f"postgresql://{DB_USER}:{safe_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# -----------------

def get_db():
    """Returns a connection to the Postgres database."""
    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )