from sla.policies import TENANT_SLA

def evaluate_sla(plan: str, metrics: dict):
    """
    metrics = {
        "failure_rate": float,
        "avg_processing_seconds": float,
        "avg_retries": float
    }
    """
    policy = TENANT_SLA.get(plan, TENANT_SLA["free"])

    violations = []

    if metrics["failure_rate"] > policy["max_failure_rate"]:
        violations.append("failure_rate")

    if metrics["avg_processing_seconds"] > policy["max_avg_processing_seconds"]:
        violations.append("latency")

    if metrics["avg_retries"] > policy["max_avg_retries"]:
        violations.append("retry_pressure")

    return {
        "violated": len(violations) > 0,
        "violations": violations,
        "severity": "HIGH" if len(violations) >= 2 else "LOW"
    }
