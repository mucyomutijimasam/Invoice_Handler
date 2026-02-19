from database.connection import get_db

def apply_sla_result(tenant_id: str, evaluation: dict):
    """
    Persists SLA status + enables downstream effects
    """
    new_status = "VIOLATED" if evaluation["violated"] else "OK"

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE tenants
                SET sla_status = %s,
                    last_sla_check = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (new_status, tenant_id))
            conn.commit()

    # Return actions for logging / alerting
    return {
        "tenant_id": tenant_id,
        "sla_status": new_status,
        "violations": evaluation["violations"],
        "severity": evaluation["severity"]
    }
