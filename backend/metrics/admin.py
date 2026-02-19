#metrics/admin.py
from database.connection import get_db
from psycopg2.extras import RealDictCursor

def get_system_admin_metrics():
    """Aggregates all system-wide health and performance data."""
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 1. Total jobs today & Queue Backlog & Stuck Workers
            cur.execute("""
                SELECT 
                    COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE) as total_today,
                    COUNT(*) FILTER (WHERE status IN ('PENDING', 'RETRY')) as backlog,
                    COUNT(*) FILTER (WHERE status = 'PROCESSING' 
                                     AND started_at < CURRENT_TIMESTAMP - INTERVAL '10 minutes') as stuck_jobs
                FROM jobs
            """)
            counts = cur.fetchone()

            # 2. Jobs by status
            cur.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")
            status_dist = cur.fetchall()

            # 3. Avg processing time per tenant
            cur.execute("""
                SELECT tenant_id, AVG(finished_at - started_at) AS avg_processing_time
                FROM jobs 
                WHERE status IN ('COMPLETED', 'REVIEW_REQUIRED')
                GROUP BY tenant_id
            """)
            processing_times = cur.fetchall()

            # 4. Failure rate per tenant
            cur.execute("""
                SELECT tenant_id,
                       COUNT(*) FILTER (WHERE status = 'FAILED')::float / 
                       NULLIF(COUNT(*), 0) AS failure_rate
                FROM jobs GROUP BY tenant_id
            """)
            failure_rates = cur.fetchall()

            return {
                "summary": counts,
                "status_distribution": status_dist,
                "tenant_performance": processing_times,
                "tenant_failure_rates": failure_rates
            }