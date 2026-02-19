import sys
from pathlib import Path

def check_setup():
    print("🔍 Starting System Connectivity Check...\n")

    # 1. Check Root Path
    root = Path(__file__).resolve().parent
    print(f"📍 Root Directory: {root}")

    # 2. Check if Manager is in the right place
    manager_path = root / "tenants" / "manager.py"
    if manager_path.exists():
        print("✅ Found: tenants/manager.py")
    else:
        print("❌ Missing: tenants/manager.py (Did you move it to root?)")

    # 3. Test the Import
    try:
        from tenants.manager import get_tenant_paths
        print("✅ Import Success: tenants.manager")
    except ImportError as e:
        print(f"❌ Import Failed: {e}")
        return

    # 4. Test Path Generation
    try:
        paths = get_tenant_paths("default_tenant")
        print(f"✅ Path Logic: Verified")
        print(f"   📂 Target Clean Folder: {paths['clean']}")
        
        if paths['clean'].exists():
            print("   ✅ Directory exists on disk.")
        else:
            print("   ⚠️ Directory missing, but manager should create it on first run.")
    except Exception as e:
        print(f"❌ Path Logic Error: {e}")

    # 5. Check Runtime Data
    existing_data = root / "runtime" / "tenants" / "default_tenant" / "clean"
    if existing_data.exists():
        print(f"✅ Existing Data found in: {existing_data.relative_to(root)}")
    else:
        print("⚠️ No existing data found in the new tenant path yet.")

    # 6. NEW: Check Versioned Memory Capability
    print("\n🧠 Checking Versioned Memory...")
    try:
        from memory.corrections import load_memory, save_memory
        paths = get_tenant_paths("default_tenant")
        mem_path = paths['memory']
        
        # Test Load
        mem = load_memory(mem_path)
        current_v = mem.get('meta', {}).get('version', 0)
        print(f"   ✅ Memory Loaded (Current Version: {current_v})")
        
        # Test Snapshot Ability (This triggers a backup creation)
        save_memory(mem, mem_path)
        version_dir = mem_path.parent / "versions"
        
        if version_dir.exists() and any(version_dir.iterdir()):
            count = len(list(version_dir.glob('*.json')))
            print(f"   ✅ Versioning System: ACTIVE (Found {count} snapshots)")
        else:
            print("   ℹ️ Versioning System: INITIALIZED (Snapshots will appear after first learning)")
            
    except Exception as e:
        print(f"   ❌ Memory System Error: {e}")

    # Final Conclusion Logic
    print("\n" + "="*40)
    ready = manager_path.exists() and 'paths' in locals()
    print("🚀 Conclusion: " + ("READY TO RUN" if ready else "FIX PATHS FIRST"))
    print("="*40)

if __name__ == "__main__":
    check_setup()