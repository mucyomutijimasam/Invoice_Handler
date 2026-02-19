#memory/corrections.py
import json
import difflib
import shutil
from datetime import datetime
from pathlib import Path
from tenants.manager import get_tenant_paths

# --- PATHING ---
DEFAULT_PATHS = get_tenant_paths("default_tenant")
DEFAULT_MEMORY_FILE = DEFAULT_PATHS["memory"]

def create_memory_backup(memory_path):
    """Creates a timestamped snapshot of the memory before it is updated."""
    path = Path(memory_path)
    if not path.exists():
        return

    # Create /versions/ folder next to the memory file
    version_dir = path.parent / "versions"
    version_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = version_dir / f"correction_memory_{timestamp}.json"
    
    shutil.copy2(path, backup_path)
    
    # Keep only the last 10 versions to save disk space
    all_versions = sorted(version_dir.glob("*.json"), key=lambda x: x.stat().st_mtime)
    if len(all_versions) > 10:
        all_versions[0].unlink()

def load_memory(memory_path=None):
    """Loads memory from a specific path, or defaults to default_tenant."""
    path = Path(memory_path) if memory_path else DEFAULT_MEMORY_FILE
    
    if not path.exists():
        return {
            "amount_fixes": {},
            "service_normalization": {},
            "name_fixes": {},
            "known_clients": [],
            "meta": {"version": 0, "last_updated": None}
        }
    
    with open(path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️ Warning: {path.name} corrupted. Returning empty memory.")
            return {"amount_fixes": {}, "service_normalization": {}, "name_fixes": {}, "meta": {"version": 0}}

def save_memory(memory, memory_path=None):
    """Saves memory and creates an automatic version snapshot."""
    path = Path(memory_path) if memory_path else DEFAULT_MEMORY_FILE
    
    # 1. Create backup of current state
    create_memory_backup(path)

    # 2. Update Metadata
    if "meta" not in memory:
        memory["meta"] = {"version": 0}
    memory["meta"]["version"] += 1
    memory["meta"]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 3. Save
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(memory, f, indent=2)

def apply_known_fixes(row, memory):
    """Applies exact and fuzzy fixes using the memory dictionary."""
    # Logic uses 'current' keys by default
    raw_amount = row.get("Amount")
    if raw_amount and str(raw_amount) in memory.get("amount_fixes", {}):
        row["Amount"] = memory["amount_fixes"][str(raw_amount)]

    name = row.get("Name", "")
    if name:
        name_memory = memory.get("name_fixes", {})
        if name in name_memory:
            row["Name"] = name_memory[name]
        else:
            known_errors = list(name_memory.keys())
            matches = difflib.get_close_matches(name, known_errors, n=1, cutoff=0.8)
            if matches:
                row["Name"] = name_memory[matches[0]]

    service = row.get("Service", "").strip()
    if not service:
        return row

    service_memory = memory.get("service_normalization", {})
    if service in service_memory:
        row["Service"] = service_memory[service]
        return row

    matches = difflib.get_close_matches(service, list(service_memory.keys()), n=1, cutoff=0.85)
    if matches:
        row["Service"] = service_memory[matches[0]]
        return row

    for noisy, clean in service_memory.items():
        if len(noisy) > 5 and noisy.lower() in service.lower():
            row["Service"] = clean
            break
    return row

def record_human_correction(original_row, corrected_row, tenant_id="default_tenant"):
    """Learns differences between OCR and Human corrections for a specific tenant."""
    paths = get_tenant_paths(tenant_id)
    memory_path = paths["memory"]
    
    memory = load_memory(memory_path)
    learned = False

    fields_map = {
        "Amount": "amount_fixes",
        "Service": "service_normalization",
        "Name": "name_fixes"
    }

    for field, memory_key in fields_map.items():
        orig = original_row.get(field)
        corr = corrected_row.get(field)
        
        if orig and corr and str(orig).strip() != str(corr).strip():
            memory[memory_key][str(orig).strip()] = str(corr).strip()
            learned = True

    if learned:
        save_memory(memory, memory_path)
        print(f"💡 Learned & Versioned: v{memory['meta']['version']} for [{tenant_id}]")