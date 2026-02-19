from pathlib import Path

# Identify the project root
BASE_DIR = Path(__file__).resolve().parent.parent

def get_tenant_paths(tenant_id="default_tenant"):
    """
    Returns a dictionary of paths for the given tenant.
    Defaults to 'default_tenant' if no ID is provided.
    """
    t_runtime = BASE_DIR / "runtime" / "tenants" / tenant_id
    t_memory = BASE_DIR / "memory" / "tenants" / tenant_id
    
    # Ensure folders exist automatically
    (t_runtime / "clean").mkdir(parents=True, exist_ok=True)
    (t_runtime / "review").mkdir(parents=True, exist_ok=True)
    (t_runtime / "processed_originals").mkdir(parents=True, exist_ok=True)
    t_memory.mkdir(parents=True, exist_ok=True)
    
    return {
        "clean": t_runtime / "clean",
        "review": t_runtime / "review",
        "originals": t_runtime / "processed_originals",
        "memory": t_memory / "correction_memory.json",
        "base": t_runtime
    }