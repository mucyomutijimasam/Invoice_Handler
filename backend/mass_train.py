import os
import shutil
from pathlib import Path
from review.excel_diff import diff_and_learn
from tenants.manager import get_tenant_paths

def run_mass_training(tenant_id="default_tenant"):
    """
    Finds corrected files in the tenant's corrected folder, 
    learns from metadata, and moves them to a structured archive.
    """
    # 1. Dynamic Path Resolution via Manager
    paths = get_tenant_paths(tenant_id)
    CORRECTED_DIR = paths["review"] / "corrected"
    
    # We maintain your archive structure but keep it under the tenant's folder
    ARCHIVE_ROOT = paths["review"] / "archive"
    ARCHIVE_CORRECTED = ARCHIVE_ROOT / "corrected"

    # Ensure folders exist
    CORRECTED_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_CORRECTED.mkdir(parents=True, exist_ok=True)

    # 2. Identify files to process
    corrected_files = list(CORRECTED_DIR.glob("*.xlsx"))
    
    if not corrected_files:
        print(f"📭 No new files in {CORRECTED_DIR.relative_to(Path.cwd())}")
        return

    print(f"🧠 Found {len(corrected_files)} files. Starting mass learning...")

    success_count = 0
    for file_path in corrected_files:
        print(f"🔄 Processing: {file_path.name}")
        try:
            # Run the self-contained learning logic
            diff_and_learn(file_path)
            
            # Archive the file (move instead of rename for cross-filesystem safety)
            dest = ARCHIVE_CORRECTED / file_path.name
            if dest.exists():
                dest = ARCHIVE_CORRECTED / f"learned_{os.urandom(2).hex()}_{file_path.name}"
            
            shutil.move(str(file_path), str(dest))
            success_count += 1
            print(f"✅ Learned and Archived: {file_path.name}")

        except Exception as e:
            print(f"⚠️ Error processing {file_path.name}: {e}")

    print("-" * 30)
    print(f"✨ Done! Successfully updated AI memory from {success_count} file(s).")

if __name__ == "__main__":
    run_mass_training()