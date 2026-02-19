from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Header
from database.connection import get_db
from billing.manager import reconcile_payment_by_reference
import logging

router = APIRouter()
logger = logging.getLogger("BillingWebhook")

# Dummy function: Replace with actual MTN Signature logic
def verify_mtn_signature(payload_bytes: bytes, signature: str):
    # HMAC verification logic here
    # return hmac.compare_digest(calculated_sig, signature)
    return True 

@router.post("/webhook/mtn_momo")
async def mtn_momo_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    x_signature: str = Header(None) # MTN usually sends a signature header
):
    # 1. Get raw body for signature verification
    body = await request.body()
    payload = await request.json()

    # 2. SECURITY: Verify the request is actually from MTN
    if not verify_mtn_signature(body, x_signature):
        logger.warning(f"❌ Unauthorized webhook attempt! Ref: {payload.get('externalId')}")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 3. Extract Reference
    ref = payload.get("externalId") or payload.get("reference")
    if not ref:
        raise HTTPException(status_code=400, detail="Missing reference")

    # 4. Normalize Status (MTN specific mapping)
    # Ensure provider status is mapped to what your manager expects
    status = payload.get("status", "").upper()
    if status in ["SUCCESSFUL", "SUCCESS", "COMPLETED"]:
        payload["status"] = "SUCCESS"
    elif status in ["FAILED", "REJECTED"]:
        payload["status"] = "FAILED"

    # 5. ASYNCHRONOUS PROCESSING
    # We respond 'ok' immediately and process the DB update in the background
    try:
        background_tasks.add_task(reconcile_payment_by_reference, ref, payload)
    except Exception as e:
        logger.error(f"🔥 Webhook Queue Error: {str(e)}")
        # We still return 200/202 so the provider stops retrying, 
        # but we've logged the error to fix it manually.
        return {"status": "accepted_for_manual_review"}

    return {"status": "received"}