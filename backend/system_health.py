import json
from pathlib import Path
from collections import Counter
from tenants.manager import BASE_DIR

def generate_health_report():
    print("=== 📊 GLOBAL AI SYSTEM HEALTH REPORT ===")
    
    # Locate all tenants by looking at the memory folder
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
            print("   ⚠️ No memory file found yet.")
            continue

        with open(memory_file, "r") as f:
            try:
                memory = json.load(f)
            except:
                print("   ❌ Memory file corrupted.")
                continue

        # 1. Version & Metadata (The new stuff)
        meta = memory.get("meta", {})
        version = meta.get("version", 0)
        last_up = meta.get("last_updated", "Never")
        print(f"   📈 Brain Version: v{version}")
        print(f"   🕒 Last Updated: {last_up}")

        # 2. Learning Stats (Your original logic)
        sections = {
            "Names": "name_fixes",
            "Services": "service_normalization",
            "Amounts": "amount_fixes"
        }

        for label, key in sections.items():
            count = len(memory.get(key, {}))
            print(f"   ✅ {label}: {count} patterns")

        # 3. Hotspots (Your Counter logic)
        all_mistakes = []
        for key in sections.values():
            all_mistakes.extend(memory.get(key, {}).keys())

        if all_mistakes:
            common = Counter(all_mistakes).most_common(3)
            print("   🔍 Top OCR Hallucinations:")
            for orig, count in common:
                print(f"      • '{orig}'")

        # 4. Actionable Advice
        if len(memory.get("amount_fixes", {})) > 50:
            print("   💡 Advice: Check image DPI—lots of amount errors.")

    print("\n" + "="*40)

if __name__ == "__main__":
    generate_health_report()