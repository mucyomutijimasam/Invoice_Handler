import sys
import os
from pathlib import Path

# Ensure the root directory is in the path so imports work correctly
sys.path.append(str(Path(__file__).parent))

try:
    from dashboard.generate_dashboard import generate_dashboard
    from dashboard.health_report import generate_health_report
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Ensure this file is in the root directory and dashboard/ folder exists.")
    sys.exit(1)

def run_full_diagnostic(tenant_id="default_tenant"):
    """
    Runs both the Brain Health Report and the Performance Dashboard
    to give a 360-degree view of the system.
    """
    # Visual Separator
    header = f" 🔍 SYSTEM DIAGNOSTIC: {tenant_id.upper()} "
    print("\n" + "=" * len(header))
    print(header)
    print("=" * len(header))

    # 1. BRAIN HEALTH (Knowledge/Memory Status)
    # This checks what the AI has learned
    print("\n--- PART 1: AI BRAIN STATUS ---")
    try:
        generate_health_report()
    except Exception as e:
        print(f"❌ Error in Health Report: {e}")

    # 2. PERFORMANCE DASHBOARD (Results/Accuracy Status)
    # This checks how many files were processed and the money audited
    print("\n--- PART 2: PROCESSING PERFORMANCE ---")
    try:
        generate_dashboard(tenant_id)
    except Exception as e:
        print(f"❌ Error in Performance Dashboard: {e}")

    print("\n" + "=" * len(header))
    print("DIAGNOSTIC COMPLETE")
    print("=" * len(header) + "\n")

if __name__ == "__main__":
    # Usage: python check_all.py [optional_tenant_id]
    target_tenant = sys.argv[1] if len(sys.argv) > 1 else "default_tenant"
    run_full_diagnostic(target_tenant)