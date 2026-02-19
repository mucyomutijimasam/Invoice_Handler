import os
import sys

# 1. Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 2. Import your database connection
from database.connection import get_db

def add_credits(username: str, amount: int):
    # Using your existing get_db() function
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # 1. Check if the user exists (using 'username' as per your repository.py)
            cur.execute("SELECT id FROM users WHERE username = %s;", (username,))
            user = cur.fetchone()
            
            if user:
                # 2. Update the credits (Ensure 'credits' column exists in your DB)
                cur.execute(
                    "UPDATE users SET credits = COALESCE(credits, 0) + %s WHERE username = %s;",
                    (amount, username)
                )
                conn.commit()
                print(f"✅ Success: Added {amount} credits to user '{username}'")
            else:
                print(f"❌ User '{username}' not found in the 'users' table.")
                
    except Exception as e:
        print(f"🔥 Database error: {e}")
        print("Note: If the error says 'column credits does not exist', you need to run your migrations.")
    finally:
        conn.close()

if __name__ == "__main__":
    # Change 'kight_admin' to the username you actually use to log in
    add_credits("kight_admin", 1000)