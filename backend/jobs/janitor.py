#jobs/janitor
import logging
from database.connection import get_db

logger = logging.getLogger("Janitor")

def cleanup_stuck_jobs(timeout_minutes=10):
    """
    Finds jobs stuck in 'PROCESSING' for too long and moves them to 'RETRY'.
    This handles cases where a worker crashed mid-job.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                UPDATE jobs
                SET status = 'RETRY',
                    next_retry_at = CURRENT_TIMESTAMP,
                    error = 'Worker timeout: Job reset by Janitor'
                WHERE status = 'PROCESSING'
                AND started_at <= CURRENT_TIMESTAMP - INTERVAL '{timeout_minutes} minutes'
            """)
            count = cur.rowcount
            if count > 0:
                logger.info(f"🧹 Janitor: Successfully reset {count} stuck jobs.")
            conn.commit() 