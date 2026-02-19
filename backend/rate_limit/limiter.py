import time
from collections import defaultdict

# In-memory store (safe for MVP, Redis later)
_REQUEST_LOG = defaultdict(list)

PLAN_LIMITS = {
    "free": 5,
    "pro": 30,
    "enterprise": 120
}

WINDOW_SECONDS = 60


def check_rate_limit(tenant_id: str, plan: str):
    now = time.time()
    window_start = now - WINDOW_SECONDS

    requests = _REQUEST_LOG[tenant_id]

    # Remove old requests
    _REQUEST_LOG[tenant_id] = [
        ts for ts in requests if ts > window_start
    ]

    limit = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])

    if len(_REQUEST_LOG[tenant_id]) >= limit:
        return False, limit

    _REQUEST_LOG[tenant_id].append(now)
    return True, limit
