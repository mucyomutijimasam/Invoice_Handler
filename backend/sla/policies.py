TENANT_SLA = {
    "free": {
        "max_failure_rate": 0.15,
        "max_avg_processing_seconds": 300,
        "max_avg_retries": 2,
        "actions": ["warn"]
    },
    "pro": {
        "max_failure_rate": 0.08,
        "max_avg_processing_seconds": 180,
        "max_avg_retries": 1.5,
        "actions": ["warn", "throttle"]
    },
    "enterprise": {
        "max_failure_rate": 0.03,
        "max_avg_processing_seconds": 120,
        "max_avg_retries": 1,
        "actions": ["alert_admin"]
    }
}
