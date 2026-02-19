#metrics/tenants.py
from database.connection import get_db
from psycopg2.extras import RealDictCursor

def get_tenant_dashboard_metrics(tenant_id: str):
    """Calculates usage and quality signals for a specific tenant."""
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    # Jobs summary by status
                    (SELECT json_object_agg(status, count) FROM (
                        SELECT status, COUNT(*) as count FROM jobs 
                        WHERE tenant_id = %s GROUP BY status
                    ) s) as status_summary,
                    
                    # Avg processing time
                    AVG(finished_at - started_at) FILTER (
                        WHERE status IN ('COMPLETED', 'REVIEW_REQUIRED')
                    ) as avg_processing_time,
                    
                    # Jobs this month
                    COUNT(*) FILTER (
                        WHERE created_at >= date_trunc('month', CURRENT_DATE)
                    ) as jobs_this_month,
                    
                    # Retry pressure
                    AVG(retry_count) as avg_retry_pressure
                FROM jobs
                WHERE tenant_id = %s
            """, (tenant_id, tenant_id))
            
            return cur.fetchone()