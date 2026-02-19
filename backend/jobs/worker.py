import time
import logging
import sys
import multiprocessing
import os
from datetime import datetime, timedelta
from database.connection import get_db
from jobs.manager import claim_next_job, update_job_status
# Updated to use your new dynamic deduction function
from billing.manager import deduct_credits_for_job  
from main import run_pipeline as process_invoice  

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("InvoiceWorker")

# -----------------------------
# DATABASE MAINTENANCE LOGIC
# -----------------------------

def reset_stuck_jobs(timeout_minutes=10):
    """
    Finds jobs stuck in 'PROCESSING' for too long and resets them to 'RETRY'.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                UPDATE jobs
                SET status = 'RETRY',
                    next_retry_at = CURRENT_TIMESTAMP
                WHERE status = 'PROCESSING'
                AND started_at <= CURRENT_TIMESTAMP - INTERVAL '{timeout_minutes} minutes'
            """)
            count = cur.rowcount
            if count > 0:
                logger.info(f"🧹 Janitor: Reset {count} stuck jobs back to the queue.")
            conn.commit()

def handle_failure(job_id, error_message, worker_name):
    """
    Manages job lifecycle on error using Exponential Backoff.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT retry_count, max_retries FROM jobs WHERE id = %s", (job_id,))
            row = cur.fetchone()
            
            if not row:
                return
                
            retry_count, max_retries = row
            retry_count += 1

            if retry_count >= max_retries:
                logger.error(f"❌ {worker_name}: Job {job_id} failed permanently.")
                cur.execute("""
                    UPDATE jobs 
                    SET status = 'FAILED', 
                        retry_count = %s, 
                        finished_at = CURRENT_TIMESTAMP, 
                        error = %s 
                    WHERE id = %s
                """, (retry_count, error_message, job_id))
            else:
                delay = 2 ** retry_count
                cur.execute(f"""
                    UPDATE jobs 
                    SET status = 'RETRY', 
                        retry_count = %s, 
                        next_retry_at = CURRENT_TIMESTAMP + INTERVAL '{delay} minutes', 
                        error = %s 
                    WHERE id = %s
                """, (retry_count, error_message, job_id))

            conn.commit()

# -----------------------------
# WORKER EXECUTION LOGIC
# -----------------------------

def run_worker(worker_name="worker-1"):
    """
    Continuous loop to claim and process jobs from Postgres.
    """
    logger.info(f"🚀 {worker_name} active. Monitoring Postgres Queue...")
    reset_stuck_jobs(timeout_minutes=10)

    while True:
        job = claim_next_job()

        if job:
            job_id, input_path, tenant_id = job
            logger.info(f"📦 {worker_name} claimed job {job_id} (Tenant: {tenant_id})")

            try:
                # 1. Run the OCR Engine
                status, _, final_excel_path = process_invoice(input_path, tenant_id=tenant_id)

                # 2. Determine final status
                # Only charge if the OCR was successful
                if status in ["OK", "AUTO_FIXED"]:
                    
                    # 3. Dynamic Billing Integration
                    # This automatically fetches the cost (30, 50, etc.) from the plan
                    charged = deduct_credits_for_job(tenant_id, job_id)
                    
                    if charged:
                        logger.info(f"💰 {worker_name}: Successfully deducted credits for {job_id}")
                        update_job_status(job_id, "COMPLETED", output_path=str(final_excel_path))
                    else:
                        # Fail job if the tenant ran out of credits during processing
                        logger.warning(f"⚠️ {worker_name}: Insufficient credits for {tenant_id}")
                        update_job_status(job_id, "FAILED", error="Insufficient credits to complete job.")
                
                else:
                    # Job finished but needs review (No charge yet, or per your policy)
                    update_job_status(job_id, "REVIEW_REQUIRED", output_path=str(final_excel_path))
                    logger.info(f"🔍 {worker_name}: Job {job_id} requires manual review.")

            except Exception as e:
                logger.error(f"⚠️ {worker_name}: Pipeline error on job {job_id}: {str(e)}")
                handle_failure(job_id, str(e), worker_name)
        else:
            time.sleep(1)

# -----------------------------
# MULTIPROCESSING ORCHESTRATION
# -----------------------------

def start_worker_pool():
    worker_count = max(1, multiprocessing.cpu_count() - 1)
    logger.info(f"🏗️ Starting {worker_count} concurrent Postgres workers...")

    processes = []
    for i in range(worker_count):
        name = f"worker-{i+1}"
        p = multiprocessing.Process(target=run_worker, args=(name,))
        p.daemon = True
        p.start()
        processes.append(p)

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down worker pool...")

if __name__ == "__main__":
    start_worker_pool()