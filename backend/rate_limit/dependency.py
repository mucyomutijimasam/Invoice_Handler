from fastapi import HTTPException, Depends
from auth.middleware import get_current_user
from rate_limit.limiter import check_rate_limit


def rate_limit_dependency(user=Depends(get_current_user)):
    tenant_id = user["tenant_id"]
    plan = user.get("plan", "free")

    allowed, limit = check_rate_limit(tenant_id, plan)

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded ({limit}/minute). Upgrade your plan."
        )

    return True
