#metrics/tenant_advice
def generate_upgrade_advice(plan: str, metrics: dict):
    advice = []

    if plan == "free":
        if metrics["failure_rate"] > 0.1:
            advice.append(
                "Your failure rate is high on the Free tier. "
                "Upgrade to Pro or Enterprise for improved OCR accuracy and priority processing."
            )

        if metrics["avg_processing_seconds"] > 300:
            advice.append(
                "Your processing times exceed Free tier limits. "
                "Paid tiers guarantee faster turnaround."
            )

    if plan == "pro" and metrics["failure_rate"] > 0.05:
        advice.append(
            "Enterprise tier guarantees up to 97% success rate with dedicated resources."
        )

    return advice
