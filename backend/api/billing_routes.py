import os
import hmac
import hashlib
import json
import uuid
from fastapi import APIRouter, Request, Header, HTTPException, Depends
from auth.middleware import get_current_user
from billing.mtn_client import MTNMoMoClient  # The client we discussed!
from billing.manager import get_billing_manager, record_pending_payment

router = APIRouter(prefix="/billing", tags=["Billing"])

# --------------------------------------------------------------------------
# 1. INITIATE PAYMENT (Called by your User)
# --------------------------------------------------------------------------
@router.post("/request-payment")
def request_payment(phone: str, amount: float, user=Depends(get_current_user)):
    tenant_id = user["tenant_id"]
    client = MTNMoMoClient()
    
    # 1. Get the manager instance
    manager = get_billing_manager() # Use the helper you already imported

    external_id = f"{tenant_id}-{uuid.uuid4().hex[:8]}"
    
    reference_id, status = client.request_to_pay(phone, amount, external_id)

    if status not in [200, 202]:
        raise HTTPException(status_code=400, detail="MTN could not initiate payment")

    # 2. Call the method through the manager instance
    manager.record_pending_payment(  # Use manager. instead of calling it directly
        tenant_id=tenant_id,
        reference=reference_id,
        amount=amount,
        provider="mtn_momo"
    )

    return {
        "message": "Payment request sent to phone",
        "reference": reference_id,
        "external_id": external_id
    }

# --------------------------------------------------------------------------
# 2. WEBHOOK (Called by MTN)
# --------------------------------------------------------------------------
def verify_signature(raw_body: bytes, signature: str) -> bool:
    secret = os.getenv("MOMO_WEBHOOK_SECRET", "").encode()
    if not secret: return False
    computed = hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, signature)

@router.post("/momo/webhook")
async def momo_webhook(
    request: Request, 
    x_signature: str = Header(None, alias="X-Signature")
):
    """
    MTN calls this automatically when the user enters their PIN.
    """
    raw_body = await request.body()

    # 1. Security Check
    if not x_signature or not verify_signature(raw_body, x_signature):
        # Log this! It could be a hacker trying to fake a payment.
        print("⚠️ Unauthorized Webhook Attempt blocked.")
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = json.loads(raw_body)
    
    # 2. Reconcile (Add credits to User's account)
    manager = get_billing_manager()
    try:
        # This function should find the pending payment and update status to 'SUCCESS'
        result = manager.reconcile_payment(
            reference=payload.get("financialTransactionId"), 
            payload=payload
        )
        return {"status": "success", "added": result.get("credits_added")}
    except Exception as e:
        print(f"❌ Webhook Error: {e}")
        return {"status": "error", "message": "Logged for manual review"}