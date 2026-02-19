#memory/rollback.py
import sys
from tenants.manager import get_tenant_paths
import shutil

def list_versions(tenant_id):
    paths = get_tenant_paths(tenant_id)
    # This looks inside memory/tenants/tenant_id/versions/
    version_dir = paths["memory"].parent / "versions"
    
    if not version_dir.exists():
        print(f"📍 No version history found for {tenant_id}")
        return None

    backups = sorted(version_dir.glob("*.json"), key=lambda x: x.stat().st_mtime)
    if not backups:
        print(f"📍 Version folder is empty for {tenant_id}")
        return None

    print(f"\n--- 🕒 Version History for {tenant_id} ---")
    for i, b in enumerate(backups):
        print(f"[{i}] {b.name}")
    return backups

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 memory/rollback.py <tenant_id>")
        sys.exit(1)

    tid = sys.argv[1]
    backups = list_versions(tid)
    
    if backups:
        choice = input("\nEnter version number to restore (or 'q' to quit): ")
        if choice.isdigit() and int(choice) < len(backups):
            target = backups[int(choice)]
            current_path = get_tenant_paths(tid)["memory"]
            
            # Perform the rollback
            shutil.copy2(target, current_path)
            print(f"✅ SUCCESS: Rolled back to {target.name}")
        else:
            print("Operation cancelled.")