import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from tenants.manager import get_tenant_paths

# --- GLOBAL DASHBOARD CONFIG ---
# These remain global as they track the overall system UI state
DASHBOARD_FILE = Path("dashboard/dashboard_report.json")
HISTORY_FILE = Path("dashboard/accuracy_history.json")

def get_lifetime_metrics(tenant_id):
    """Counts files across tenant-specific folders provided by Manager."""
    paths = get_tenant_paths(tenant_id)
    clean_dir = paths["clean"]
    review_dir = paths["review"]
    archive_dir = review_dir / "archive"
    
    clean_files = list(clean_dir.glob("*.xlsx"))
    pending_files = list(review_dir.glob("*.xlsx"))
    # Check for original images in the tenant's archive
    archived_files = list((archive_dir / "originals").glob("*.*")) if archive_dir.exists() else []
    
    total = len(clean_files) + len(pending_files) + len(archived_files)
    accuracy = len(clean_files) / total if total > 0 else 0
    
    return {
        "total": total,
        "clean": len(clean_files),
        "pending": len(pending_files),
        "archived": len(archived_files),
        "accuracy": round(accuracy, 3)
    }

def calculate_financial_impact(tenant_id):
    """Sums the 'Amount' column from tenant-specific Clean and Corrected folders."""
    paths = get_tenant_paths(tenant_id)
    total_value = 0.0
    
    # We look in the Clean folder and the Corrected Archive
    target_folders = [
        paths["clean"], 
        paths["review"] / "archive" / "corrected"
    ]
    
    for folder in target_folders:
        if folder.exists():
            for file in folder.glob("*.xlsx"):
                try:
                    df = pd.read_excel(file)
                    if "Amount" in df.columns:
                        # Convert to numeric, turning errors to NaN, then sum
                        total_value += pd.to_numeric(df["Amount"], errors='coerce').sum()
                except Exception:
                    continue
    return round(total_value, 2)

def update_trend_history(current_accuracy):
    """Saves the current accuracy to a history file to track improvement over time."""
    history = []
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r") as f:
            try:
                history = json.load(f)
            except Exception:
                history = []
    
    history.append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "accuracy": current_accuracy
    })
    
    # Keep only the last 30 snapshots
    history = history[-30:]
    
    HISTORY_FILE.parent.mkdir(exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)
    return history

def get_system_sentiment(accuracy):
    """Human-readable feedback based on accuracy percentage."""
    if accuracy >= 0.90:
        return "🚀 EXCELLENT: The AI is masterfully handling your invoices."
    elif accuracy >= 0.75:
        return "📈 GOOD: AI is learning well. Keep providing corrections."
    elif accuracy >= 0.50:
        return "⚖️ AVERAGE: Some invoices are tricky. Ensure scans are straight."
    else:
        return "⚠️ ATTENTION: High error rate. Check scan DPI or glass cleanliness."

def generate_dashboard(tenant_id="default_tenant"):
    """Orchestrates data gathering and saves the final JSON report."""
    # 1. Gather Data (Tenant Aware)
    lifetime = get_lifetime_metrics(tenant_id)
    money_handled = calculate_financial_impact(tenant_id)
    history = update_trend_history(lifetime["accuracy"])
    
    # 2. Analyze Trend
    avg_past_accuracy = sum(h["accuracy"] for h in history) / len(history) if history else 0
    trend_status = "Improving" if lifetime["accuracy"] >= avg_past_accuracy else "Struggling"

    # 3. Build Final Report Object
    dashboard = {
        "tenant_id": tenant_id,
        "report_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "performance_summary": {
            "status_message": get_system_sentiment(lifetime["accuracy"]),
            "accuracy_score": f"{round(lifetime['accuracy'] * 100, 1)}%",
            "trend": trend_status,
            "total_financial_volume": f"${money_handled:,.2f}"
        },
        "file_stats": lifetime,
        "learning_progress": history
    }

    # 4. Save and Print
    DASHBOARD_FILE.parent.mkdir(exist_ok=True)
    with open(DASHBOARD_FILE, "w") as f:
        json.dump(dashboard, f, indent=2)

    print(f"\n=== 📊 SYSTEM DASHBOARD: {tenant_id.upper()} ===")
    print(dashboard["performance_summary"]["status_message"])
    print(f"💰 Total Money Audited: {dashboard['performance_summary']['total_financial_volume']}")
    print(f"🎯 Current Accuracy: {dashboard['performance_summary']['accuracy_score']}")
    print(f"📂 Total Invoices (Lifetime): {lifetime['total']}")
    print("===========================\n")

if __name__ == "__main__":
    # Can be called with a specific tenant_id from the command line
    import sys
    tid = sys.argv[1] if len(sys.argv) > 1 else "default_tenant"
    generate_dashboard(tid)