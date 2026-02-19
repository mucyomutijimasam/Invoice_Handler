#jobs/sla_worker.py
import time
import logging
from database.connection import get_db
from metrics.tenant import get_tenant_metrics
from sla.evaluator import evaluate_sla
from sla.enforcer import apply_sla_result

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SLAWorker")

CHECK_INTERVAL_SECONDS = 300  # every 5 minutes

def run_sla_worker():
    logger.info("🚨 SLA Worker started")

    while True:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, plan FROM tenants")
                tenants = cur.fetchall()

        for tenant_id, plan in tenants:
            try:
                metrics = get_tenant_metrics(tenant_id)
                evaluation = evaluate_sla(plan, metrics)
                result = apply_sla_result(tenant_id, evaluation)

                if result["sla_status"] == "VIOLATED":
                    logger.warning(f"⚠️ SLA VIOLATION [{tenant_id}] → {result['violations']}")

            except Exception as e:
                logger.error(f"❌ SLA check failed for tenant {tenant_id}: {e}")

        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    run_sla_worker()
