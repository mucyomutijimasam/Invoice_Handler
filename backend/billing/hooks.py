from database.connection import get_db
def charge_job(tenant_id: str, job_id: str):
    with get_db() as conn:
        with conn.cursor() as cur:
            # Lock tenant row
            cur.execute(""" 
                SELECT credits
                FROM billing_accounts
                WHERE tenant_id = %s
                FOR UPDATE
            """, (tenant_id,))
            
            credits = cur.fetchone()[0]

            if credits < 50:
                raise Exception("Insufficient credits")

            # Deduct credits
            cur.execute("""
                UPDATE billing_accounts
                SET credits = credits - 50
                WHERE tenant_id = %s
            """, (tenant_id,))

            # Log billing event
            cur.execute("""
                INSERT INTO billing_events (tenant_id, job_id, amount)
                VALUES (%s, %s, 50)
            """, (tenant_id, job_id))

            conn.commit()
