import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
from database.connection import get_db

# Import the professional billing logic we unified earlier
from billing.service import debit_credits_for_job
from billing.exceptions import BillingError

# --- CONFIGURATION ---
# Prevents one user from saturating all workers
MAX_CONCURRENT_PER_TENANT = 3

def create_job(tenant_id: str, input_path: str, priority: int = 1):
    """
    1. Validates and DEDUCTS credits using the Billing Service.
    2. Inserts job into the queue only if payment/credits are successful.
    """
    job_id = str(uuid.uuid4())

    # 🔒 PHASE 1: BILLING ENFORCEMENT
    # This calls your billing.service which locks the row and updates the ledger
    try:
        debit_credits_for_job(tenant_id, job_id)
    except BillingError as e:
        # Catch specific billing issues (Expired sub, No credits, etc.)
        raise Exception(f"Billing Validation Failed: {str(e)}")
    except Exception as e:
        # Catch unexpected database errors
        raise Exception(f"System error during billing: {str(e)}")

    # 🛠️ PHASE 2: JOB CREATION
    # Only runs if the code above didn't raise an exception
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO jobs (id, tenant_id, status, input_path, priority, created_at)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """, (job_id, tenant_id, "PENDING", input_path, priority))
            conn.commit()

    return job_id

def claim_next_job():
    """
    High-Performance Fair Scheduler:
    - CTE finds candidates that aren't blocked by concurrency limits.
    - 'FOR UPDATE SKIP LOCKED' allows multiple workers to run without crashing into each other.
    """
    
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                cur.execute("""
                    UPDATE jobs
                    SET status = 'PROCESSING', 
                        started_at = CURRENT_TIMESTAMP
                    WHERE id = (
                        SELECT j.id
                        FROM jobs j
                        WHERE j.status IN ('PENDING', 'RETRY')
                          AND (j.next_retry_at IS NULL OR j.next_retry_at <= CURRENT_TIMESTAMP)
                          AND (
                              SELECT COUNT(*) 
                              FROM jobs j2 
                              WHERE j2.tenant_id = j.tenant_id AND j2.status = 'PROCESSING'
                          ) < %s
                        ORDER BY j.priority DESC, j.created_at ASC
                        LIMIT 1
                        FOR UPDATE SKIP LOCKED
                    )
                    RETURNING id, input_path, tenant_id
                """, (MAX_CONCURRENT_PER_TENANT,))
                
                claimed = cur.fetchone()
                conn.commit()
                
                if claimed:
                    return (str(claimed['id']), claimed['input_path'], claimed['tenant_id'])
                return None

            except Exception as e:
                conn.rollback()
                print(f"❌ Scheduler error: {e}")
                return None

def update_job_status(job_id: str, status: str, output_path: str = None, error: str = None):
    """Updates the final results or failure state of a job."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE jobs
                SET status = %s, 
                    output_path = %s, 
                    error = %s, 
                    finished_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (status, output_path, error, job_id))
            conn.commit()

def get_job(job_id: str):
    """Retrieves the full record for a specific job."""
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
            return cur.fetchone()