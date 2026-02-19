import json
from pathlib import Path
from collections import Counter
from tenants.manager import BASE_DIR

def generate_health_report():
    print("=== 🧠 AI BRAIN HEALTH REPORT ===")
    # Ensures we are looking at the unified tenant storage
    memory_root = BASE_DIR / "memory" / "tenants"
    
    if not memory_root.exists():
        print("❌ No memory root found.")
        return

    tenants = [d for d in memory_root.iterdir() if d.is_dir()]

    for tenant_dir in tenants:
        tenant_id = tenant_dir.name
        memory_file = tenant_dir / "correction_memory.json"
        print(f"\n🏢 TENANT: {tenant_id.upper()}")
        
        if not memory_file.exists():
            continue

        with open(memory_file, "r") as f:
            memory = json.load(f)

        meta = memory.get("meta", {})
        print(f"   📈 Version: v{meta.get('version', 0)}")
        print(f"   🕒 Last Updated: {meta.get('last_updated', 'Never')}")
        
        counts = {
            "Names": len(memory.get("name_fixes", {})),
            "Services": len(memory.get("service_normalization", {})),
            "Amounts": len(memory.get("amount_fixes", {}))
        }
        for label, count in counts.items():
            print(f"   ✅ {label}: {count} patterns learned")

if __name__ == "__main__":
    generate_health_report()