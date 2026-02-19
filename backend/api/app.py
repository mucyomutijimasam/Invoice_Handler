#api/app.py
import uuid
import shutil
import asyncio
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse


# Auth & Database Imports
from auth.models import UserRegister, UserLogin, TokenResponse
from auth.security import hash_password, verify_password, create_access_token
from auth.middleware import get_current_user
from auth.repository import create_user, get_user_by_username 
from database.connection import get_db
from api.billing_routes import router as billing_router

# Rate Limiting Import
from rate_limit.dependency import rate_limit_dependency

# Metric & Janitor Imports
from metrics.admin import get_system_admin_metrics
from metrics.tenant import get_tenant_dashboard_metrics
from jobs.janitor import cleanup_stuck_jobs

# Logic & Job Manager Imports
from review.excel_diff import diff_and_learn
from tenants.manager import get_tenant_paths
from jobs.manager import create_job, get_job
import logging

# -----------------------------
# BACKGROUND JANITOR TASK
# -----------------------------
async def janitor_loop():
    """Infinite loop that runs the janitor every 5 minutes."""
    while True:
        try:
            # Cleans jobs stuck in PROCESSING for > 10 mins
            cleanup_stuck_jobs(timeout_minutes=10)
        except Exception as e:
            print(f"❌ Janitor Loop Error: {e}")
        
        await asyncio.sleep(300) 


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the background janitor
    janitor_task = asyncio.create_task(janitor_loop())
    yield
    # Shutdown: Stop the janitor task
    janitor_task.cancel()

#---LOGGING SERVICES---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# --- INITIALIZE APP ---
app = FastAPI(
    title="Multi-Tenant OCR & Learning API",
    lifespan=lifespan
)

# Register the billing routes
app.include_router(billing_router)

# --- CONFIGURATION ---
UPLOAD_DIR = Path("uploads")
QUEUE_PENDING = Path("queue/pending")
QUEUE_PROCESSING = Path("queue/processing")

for folder in [UPLOAD_DIR, QUEUE_PENDING, QUEUE_PROCESSING]:
    folder.mkdir(parents=True, exist_ok=True)

PLAN_PRIORITY = {"free": 1, "pro": 5, "enterprise": 10}
SEAT_LIMITS = {"free": 1, "pro": 5, "enterprise": 20}
SUPPORTED_INVOICE_EXT = {".jpg", ".jpeg", ".png", ".pdf"}

# -----------------------------
# 1. AUTH & INVITATION ROUTES
# -----------------------------

@app.post("/register")
def register(user: UserRegister, plan: str = "free"):
    """
    Initial registration for a Tenant Admin. 
    Provisions the company, sets the seat limit, and grants 100 trial credits.
    """
    plan_tier = plan.lower() if plan.lower() in PLAN_PRIORITY else "free"
    
    with get_db() as conn:
        with conn.cursor() as cur:
            # Check if user already exists
            cur.execute("SELECT id FROM users WHERE username = %s", (user.username,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="User already exists")

            # Check if Tenant exists
            cur.execute("SELECT id FROM tenants WHERE id = %s", (user.tenant_id,))
            if not cur.fetchone():
                # FIRST USER: Provision the Tenant and Billing
                cur.execute("""
                    INSERT INTO tenants (id, name, plan_tier, max_seats) 
                    VALUES (%s, %s, %s, %s)
                """, (user.tenant_id, f"{user.tenant_id}_org", plan_tier, SEAT_LIMITS[plan_tier]))
                
                cur.execute("""
                    INSERT INTO billing_accounts (tenant_id, credits)
                    VALUES (%s, 100) ON CONFLICT DO NOTHING
                """, (user.tenant_id,))
            else:
                # If tenant exists, new users MUST use /register/join via an invite token
                raise HTTPException(
                    status_code=403, 
                    detail="This company is already registered. Please ask your Admin for an invite link."
                )
            conn.commit()

    # Create the Admin user
    create_user(
        username=user.username,
        password_hash=hash_password(user.password),
        tenant_id=user.tenant_id,
        role="admin"
    )

    return {
        "message": "Company registered successfully!",
        "trial_credits": 100,
        "role": "admin",
        "seats": SEAT_LIMITS[plan_tier]
    }

@app.post("/tenant/invite")
async def invite_user(email: str, user=Depends(get_current_user)):
    """Generates a secure token for a colleague. Only accessible by Admins."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only Admins can invite team members.")

    tenant_id = user["tenant_id"]

    with get_db() as conn:
        with conn.cursor() as cur:
            # Check Seat Limits
            cur.execute("SELECT max_seats FROM tenants WHERE id = %s", (tenant_id,))
            max_seats = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM users WHERE tenant_id = %s", (tenant_id,))
            if cur.fetchone()[0] >= max_seats:
                raise HTTPException(status_code=403, detail="Seat limit reached for your plan.")

            # Generate Token
            cur.execute("""
                INSERT INTO invitations (tenant_id, email) 
                VALUES (%s, %s) RETURNING token
            """, (tenant_id, email))
            token = cur.fetchone()[0]
            conn.commit()

    return {"invite_link": f"/register/join?token={token}", "expires": "48 hours"}

@app.post("/register/join")
def join_by_token(token: str, username: str, password: str):
    """Allows an invited member to join the company securely."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT tenant_id, role FROM invitations 
                WHERE token = %s AND expires_at > CURRENT_TIMESTAMP
            """, (token,))
            invite = cur.fetchone()

            if not invite:
                raise HTTPException(status_code=400, detail="Invalid or expired invitation token.")

            tenant_id, role = invite

            create_user(
                username=username,
                password_hash=hash_password(password),
                tenant_id=tenant_id,
                role=role
            )

            # Clean up token
            cur.execute("DELETE FROM invitations WHERE token = %s", (token,))
            conn.commit()

    return {"message": f"Welcome! You have joined the organization: {tenant_id}"}

@app.post("/login", response_model=TokenResponse)
def login(user: UserLogin):
    db_user = get_user_by_username(user.username)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    stored_hash = db_user.get("hashed_password") 
    if not verify_password(user.password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Issue JWT with Tenant ID and Role
    access_token = create_access_token(
        data={
            "sub": db_user["username"], 
            "tenant_id": db_user["tenant_id"],
            "role": db_user.get("role", "member")
        }
    )
    return {"access_token": access_token, "token_type": "bearer"}

# -----------------------------
# 2. PROTECTED OCR ROUTES
# -----------------------------

@app.post("/upload_invoice")
async def upload_invoice(
    file: UploadFile = File(...),
    _=Depends(rate_limit_dependency),
    user=Depends(get_current_user)
):
    """Handles upload with credit enforcement and job queuing."""
    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_INVOICE_EXT:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    tenant_id = user["tenant_id"]
    priority_level = PLAN_PRIORITY.get(user.get("plan", "free"), 1)

    # Prepare local path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{timestamp}__{uuid.uuid4().hex[:8]}__{file.filename}"
    input_path = UPLOAD_DIR / file_name

    # 1. ATOMIC CREDIT CHECK & JOB CREATION
    try:
        # If credits < 50, create_job raises an Exception
        job_id = create_job(tenant_id, str(input_path), priority=priority_level)
    except Exception as e:
        # Returns 402 Payment Required for insufficient credits
        raise HTTPException(status_code=402, detail=str(e))

    # 2. SAVE FILE (Only if job was successfully created/billed)
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 3. PUSH TO QUEUE FOR WORKER
    shutil.copy(input_path, QUEUE_PENDING / f"{job_id}{suffix}")
    
    return {"status": "QUEUED", "job_id": job_id, "tenant": tenant_id}

# -----------------------------
# 3. UTILITY & METRICS ROUTES
# -----------------------------

@app.get("/status/{job_id}")
async def get_status(job_id: str, user=Depends(get_current_user)):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Strict Tenant Isolation
    job_tenant = job["tenant_id"] if isinstance(job, dict) else job[1]
    if str(job_tenant) != str(user["tenant_id"]):
        raise HTTPException(status_code=403, detail="Unauthorized")

    return {
        "job_id": str(job["id"] if isinstance(job, dict) else job[0]),
        "status": job["status"] if isinstance(job, dict) else job[2],
        "output_file": Path(job["output_path"]).name if (isinstance(job, dict) and job.get("output_path")) else None
    }

@app.delete("/tenant/users/{username}")
async def delete_user_from_tenant(username: str, user=Depends(get_current_user)):
    """
    Allows an Admin to remove a user from their tenant.
    This frees up a seat for new invitations.
    """
    # 1. Security Check: Only Admins can delete
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can manage team members.")

    # 2. Prevent Self-Deletion (Safety Rail)
    if username == user["sub"]:
        raise HTTPException(status_code=400, detail="You cannot delete your own admin account.")

    with get_db() as conn:
        with conn.cursor() as cur:
            # 3. Tenant Isolation Check: Does this user actually belong to the Admin's tenant?
            cur.execute(
                "SELECT tenant_id FROM users WHERE username = %s", 
                (username,)
            )
            target_user = cur.fetchone()

            if not target_user:
                raise HTTPException(status_code=404, detail="User not found.")

            if target_user[0] != user["tenant_id"]:
                raise HTTPException(
                    status_code=403, 
                    detail="Unauthorized: This user belongs to a different organization."
                )

            # 4. Perform Deletion
            cur.execute("DELETE FROM users WHERE username = %s", (username,))
            conn.commit()

    return {"message": f"User {username} has been removed. 1 seat has been freed."}

@app.get("/download/{filename}")
def download_result(filename: str, user=Depends(get_current_user)):
    tenant_id = user["tenant_id"]
    paths = get_tenant_paths(tenant_id)
    for folder in ["clean", "review"]:
        file_path = paths[folder] / filename
        if file_path.exists():
            return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")

@app.post("/reupload_corrected")
async def reupload_corrected(file: UploadFile = File(...), user=Depends(get_current_user)):
    tenant_id = user["tenant_id"]
    paths = get_tenant_paths(tenant_id)
    save_path = paths["review"] / "corrected" / f"corr_{uuid.uuid4().hex[:5]}_{file.filename}"
    save_path.parent.mkdir(exist_ok=True, parents=True)
    
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        diff_and_learn(save_path, tenant_id=tenant_id)
        return {"status": "SUCCESS", "message": "AI model updated"}
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Learning failed: {str(e)}")

@app.get("/tenant/metrics")
async def tenant_metrics(user=Depends(get_current_user)):
    return get_tenant_dashboard_metrics(user["tenant_id"])

@app.get("/admin/metrics")
async def admin_metrics(user=Depends(get_current_user)):
    if user.get("role") != "admin": # System-wide admin check
        raise HTTPException(status_code=403, detail="Admin access required")
    return get_system_admin_metrics()

@app.get("/health")
def health_check(user=Depends(get_current_user)):
    """
    Checks if the API is up, the DB is connected, 
    and returns the tenant's current credit balance.
    """
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                # 1. Test Database Connectivity
                cur.execute("SELECT 1")
                
                # 2. Get Tenant Balance
                cur.execute(
                    "SELECT credits FROM billing_accounts WHERE tenant_id = %s", 
                    (user["tenant_id"],)
                )
                row = cur.fetchone()
                balance = row[0] if row else 0

        return {
            "status": "healthy",
            "database": "connected",
            "tenant_id": user["tenant_id"],
            "credits_remaining": balance,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service Unhealthy: {str(e)}")