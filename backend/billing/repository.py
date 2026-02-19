from database.connection import get_db


def get_active_subscription(tenant_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT ts.id, ts.status, ts.current_period_end, sp.credit_cost
                FROM tenant_subscriptions ts
                JOIN subscription_plans sp ON ts.plan_id = sp.id
                WHERE ts.tenant_id = %s
                AND ts.status = 'active'
                LIMIT 1
            """, (tenant_id,))
            return cur.fetchone()


def get_credits(tenant_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT credits
                FROM billing_accounts
                WHERE tenant_id = %s
            """, (tenant_id,))
            row = cur.fetchone()
            return row[0] if row else 0


def update_credits(cur, tenant_id, new_balance):
    cur.execute("""
        UPDATE billing_accounts
        SET credits = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE tenant_id = %s
    """, (new_balance, tenant_id))


def insert_ledger_entry(cur, tenant_id, job_id, event_type, amount, description):
    cur.execute("""
        INSERT INTO billing_ledger (tenant_id, job_id, event_type, amount, description)
        VALUES (%s, %s, %s, %s, %s)
    """, (tenant_id, job_id, event_type, amount, description))
