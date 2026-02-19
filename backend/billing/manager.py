import json
import os
import logging
from decimal import Decimal
from datetime import date
from database.connection import get_db

# Custom exceptions from your billing/exceptions.py
from billing.exceptions import (
    InsufficientCredits,
    NoActiveSubscription,
    SubscriptionExpired,
    BillingError
)

# SETUP LOGGING: This ensures all billing events are tracked
logger = logging.getLogger("billing")

class BillingManager:
    def __init__(self, connection=None):
        self.connection = connection

    # --- 1. CORE DEBIT LOGIC (For Jobs) ---

    def _get_active_sub_details(self, cur, tenant_id: str):
        """Internal helper to get plan details using an existing cursor."""
        cur.execute("""
            SELECT s.id, s.status, s.current_period_end, p.credit_cost 
            FROM tenant_subscriptions s
            JOIN subscription_plans p ON s.plan_id = p.id
            WHERE s.tenant_id = %s AND s.status = 'active'
            LIMIT 1
        """, (tenant_id,))
        row = cur.fetchone()

        if not row:
            raise NoActiveSubscription(f"No active subscription found for tenant {tenant_id}")

        sub_id, status, period_end, credit_cost = row
        if period_end < date.today():
            raise SubscriptionExpired(f"Subscription for {tenant_id} expired on {period_end}")

        return {"credit_cost": credit_cost}

    def debit_credits_for_job(self, tenant_id: str, job_id: str):
        """
        Deducts credits for an OCR job using atomic locks.
        """
        with get_db() as conn:
            with conn.cursor() as cur:
                sub = self._get_active_sub_details(cur, tenant_id)
                cost = sub["credit_cost"]

                cur.execute("""
                    SELECT credits FROM billing_accounts 
                    WHERE tenant_id = %s FOR UPDATE
                """, (tenant_id,))
                row = cur.fetchone()

                if not row or row[0] < cost:
                    current = row[0] if row else 0
                    raise InsufficientCredits(f"Required {cost}, but only have {current}")

                cur.execute("""
                    UPDATE billing_accounts 
                    SET credits = credits - %s, updated_at = CURRENT_TIMESTAMP 
                    WHERE tenant_id = %s
                """, (cost, tenant_id))

                cur.execute("""
                    INSERT INTO billing_ledger (tenant_id, job_id, event_type, amount, description)
                    VALUES (%s, %s, 'JOB_DEBIT', %s, %s)
                """, (tenant_id, job_id, -cost, f"OCR Processing: Job {job_id}"))

                conn.commit()
                return True

    # --- 2. CORE CREDIT LOGIC (For Webhooks) ---

    def reconcile_payment(self, reference: str, payload: dict):
        """
        Fraud-Guard: Idempotent payment reconciliation for MoMo.
        """
        tenant_id = payload.get("externalId") or payload.get("tenant_id")
        amount_raw = Decimal(str(payload.get("amount", "0.00")))
        provider = payload.get("provider", os.getenv("MOMO_PROVIDER_NAME", "mtn_momo"))
        currency = payload.get("currency", "RWF")
        raw_status = str(payload.get("status", "pending")).upper()

        # Fraud Guard: Conversion Rate (100 RWF = 1 Credit)
        CREDIT_CONVERSION_RATE = 100 
        credits_to_add = int(amount_raw / CREDIT_CONVERSION_RATE)

        if credits_to_add <= 0 and raw_status == "SUCCESSFUL":
            raise BillingError("Transaction amount too low for credits.")

        with get_db() as conn:
            with conn.cursor() as cur:
                # 1. Idempotency Check
                cur.execute("""
                    INSERT INTO payment_transactions (
                        tenant_id, provider, external_reference, amount, currency, status, metadata
                    )
                    VALUES (%s, %s, %s, %s, %s, 'pending', %s)
                    ON CONFLICT (provider, external_reference) DO NOTHING
                    RETURNING id, status;
                """, (tenant_id, provider, reference, amount_raw, currency, json.dumps(payload)))
                
                row = cur.fetchone()
                if not row:
                    cur.execute("""
                        SELECT id, status FROM payment_transactions 
                        WHERE provider = %s AND external_reference = %s
                    """, (provider, reference))
                    row = cur.fetchone()

                payment_id, current_db_status = row

                if current_db_status == 'success':
                    return {"status": "already_processed"}

                # 2. Handle Success
                if raw_status in ("SUCCESSFUL", "SUCCESS", "COMPLETED"):
                    cur.execute("SELECT credits FROM billing_accounts WHERE tenant_id = %s FOR UPDATE", (tenant_id,))
                    exists = cur.fetchone()

                    if not exists:
                        cur.execute("INSERT INTO billing_accounts (tenant_id, credits) VALUES (%s, %s)", (tenant_id, credits_to_add))
                    else:
                        cur.execute("UPDATE billing_accounts SET credits = credits + %s WHERE tenant_id = %s", (credits_to_add, tenant_id))

                    cur.execute("UPDATE payment_transactions SET status = 'success' WHERE id = %s", (payment_id,))

                    cur.execute("""
                        INSERT INTO billing_ledger (tenant_id, event_type, amount, description)
                        VALUES (%s, 'CREDIT_TOPUP', %s, %s)
                    """, (tenant_id, credits_to_add, f"Top-up ref: {reference} via {provider}"))

                    # 3. STRUCTURED PRODUCTION LOGGING
                    logger.info("MoMo payment credited", extra={
                        "tenant_id": tenant_id,
                        "reference": reference,
                        "amount": str(amount_raw),
                        "credits_added": credits_to_add,
                        "provider": provider
                    })

                    conn.commit()
                    return {"status": "reconciled", "credits_added": credits_to_add}

                elif raw_status in ("FAILED", "REJECTED"):
                    cur.execute("UPDATE payment_transactions SET status = 'failed' WHERE id = %s", (payment_id,))
                    conn.commit()
                    return {"status": "failed"}

        return {"status": "pending"}
    def record_pending_payment(self, tenant_id: str, reference: str, amount: float, provider: str):
        """
        Stores an 'initiated' payment in the DB so we can match it 
        when the webhook arrives later.
        """
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO payment_transactions (
                        tenant_id, provider, external_reference, amount, status
                    ) VALUES (%s, %s, %s, %s, 'pending')
                    ON CONFLICT (provider, external_reference) DO NOTHING
                """, (tenant_id, provider, reference, amount))
                conn.commit()

def get_billing_manager():
    return BillingManager()

def record_pending_payment(self, tenant_id: str, reference: str, amount: float, provider: str):
        """
    Stores an 'initiated' payment in the DB so we can match it 
    when the webhook arrives later.
        """
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO payment_transactions (
                        tenant_id, provider, external_reference, amount, status
                    ) VALUES (%s, %s, %s, %s, 'pending')
                    ON CONFLICT (provider, external_reference) DO NOTHING
                """, (tenant_id, provider, reference, amount))
                conn.commit()


