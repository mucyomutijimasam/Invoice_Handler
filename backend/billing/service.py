# billing/service.py
from decimal import Decimal
from database.connection import get_db
from billing.manager import BillingManager

def process_momo_payment(tenant_id, provider, reference, amount, currency, payload):
    with get_db() as conn:
        with conn.cursor() as cur:
            # 1. Idempotency check
            cur.execute("""
                SELECT status FROM payment_transactions
                WHERE provider = %s AND external_reference = %s
            """, (provider, reference))
            existing = cur.fetchone()

            if existing and existing[0] == "successful":
                return {"status": "already_processed"}

            # 2. Update or Insert transaction
            if existing:
                cur.execute("""
                    UPDATE payment_transactions SET status='successful'
                    WHERE provider=%s AND external_reference=%s
                """, (provider, reference))
            else:
                cur.execute("""
                    INSERT INTO payment_transactions 
                    (tenant_id, provider, external_reference, amount, currency, status, metadata)
                    VALUES (%s, %s, %s, %s, %s, 'successful', %s)
                """, (tenant_id, provider, reference, amount, currency, payload))

            # 3. Credit the account
            BillingManager(conn).credit_tenant(
                tenant_id=tenant_id,
                amount=Decimal(amount),
                reference=reference,
                provider=provider
            )
            conn.commit()
            return {"status": "success"}

def debit_credits_for_job(tenant_id: str, cost: int = 50):
    """
    Charged when an OCR job starts. 
    Costs 50 credits per invoice by default.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            # 1. Check current balance
            cur.execute("SELECT credits FROM billing_accounts WHERE tenant_id = %s", (tenant_id,))
            row = cur.fetchone()
            
            if not row or row[0] < cost:
                raise Exception(f"Insufficient credits. Required: {cost}, Available: {row[0] if row else 0}")

            # 2. Subtract the credits
            cur.execute("""
                UPDATE billing_accounts 
                SET credits = credits - %s 
                WHERE tenant_id = %s
            """, (cost, tenant_id))
            
            # 3. Log the transaction (Optional but professional)
            cur.execute("""
                INSERT INTO payment_transactions (tenant_id, provider, status, amount, currency)
                VALUES (%s, 'internal', 'debit', %s, 'CREDIT')
            """, (tenant_id, cost))
            
            conn.commit()
            print(f"💰 Debited {cost} credits from {tenant_id}")
    return True