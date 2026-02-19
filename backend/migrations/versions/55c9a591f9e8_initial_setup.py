"""initial_setup

Revision ID: initial_setup
Revises: None
Create Date: 2026-02-11
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'initial_setup'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # 0️⃣ Enable UUID support
    op.execute('CREATE EXTENSION  "pgcrypto";')

    # 1️⃣ Core Infrastructure: Tenants
    op.execute("""
    CREATE TABLE  tenants (
        id TEXT PRIMARY KEY,
        name TEXT,
        last_sla_check TIMESTAMP,
        billing_email TEXT,
        billing_address JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2️⃣ Billing: Subscription Plans
    op.execute("""
    CREATE TABLE  subscription_plans (
        id SERIAL PRIMARY KEY,
        name VARCHAR(50) UNIQUE NOT NULL,
        description TEXT,
        monthly_price DECIMAL(10,2) DEFAULT 0.00,
        credits_included INTEGER DEFAULT 0,
        credit_cost INTEGER DEFAULT 1,
        priority_level INTEGER DEFAULT 1,
        rate_limit_per_min INTEGER DEFAULT 5,
        max_concurrent_jobs INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3️⃣ Core Infrastructure: Users
    op.execute("""
    CREATE TABLE  users (
        id UUID PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        role TEXT DEFAULT 'member',
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 4️⃣ Core Infrastructure: Jobs
    op.execute("""
    CREATE TABLE  jobs (
        id UUID PRIMARY KEY,
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        status TEXT NOT NULL,
        input_path TEXT,
        output_path TEXT,
        error TEXT,
        retry_count INTEGER DEFAULT 0,
        max_retries INTEGER DEFAULT 3,
        priority INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        started_at TIMESTAMP,
        finished_at TIMESTAMP,
        next_retry_at TIMESTAMP
    );
    """)

    # 5️⃣ Billing: Tenant Subscriptions
    op.execute("""
    CREATE TABLE  tenant_subscriptions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        plan_id INTEGER REFERENCES subscription_plans(id),
        status VARCHAR(20) DEFAULT 'active',
        current_period_start DATE NOT NULL,
        current_period_end DATE NOT NULL,
        auto_renew BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 6️⃣ Billing: Ledger
    op.execute("""
    CREATE TABLE  billing_ledger (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        job_id UUID REFERENCES jobs(id),
        event_type VARCHAR(50) NOT NULL,
        amount BIGINT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 7️⃣ Billing: Payment Transactions
    op.execute("""
    CREATE TABLE  payment_transactions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        provider VARCHAR(50) NOT NULL,
        external_reference TEXT,
        amount DECIMAL(10,2),
        currency VARCHAR(10) DEFAULT 'RWF',
        status VARCHAR(20) DEFAULT 'pending',
        metadata JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 8️⃣ Performance Indexes
    op.execute("""
    CREATE INDEX  idx_jobs_status_priority 
    ON jobs(status, priority DESC, created_at ASC);
    """)

    # 9️⃣ Seed Data: Default Plans
    op.execute("""
    INSERT INTO subscription_plans 
        (name, description, monthly_price, credits_included, credit_cost, priority_level, rate_limit_per_min, max_concurrent_jobs)
    VALUES
        ('free', 'Free tier', 0.00, 20, 1, 1, 5, 1),
        ('pro', 'Professional tier', 49000.00, 1000, 1, 5, 30, 3),
        ('enterprise', 'Enterprise tier', 299000.00, 10000, 1, 10, 120, 10)
    ON CONFLICT (name) DO NOTHING;
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_jobs_tenant ON jobs(tenant_id);")

def downgrade():
    # Tables must be dropped in reverse order of creation
    op.execute("DROP TABLE IF EXISTS payment_transactions;")
    op.execute("DROP TABLE IF EXISTS billing_ledger;")
    op.execute("DROP TABLE IF EXISTS tenant_subscriptions;")
    op.execute("DROP TABLE IF EXISTS jobs;")
    op.execute("DROP TABLE IF EXISTS users;")
    op.execute("DROP TABLE IF EXISTS subscription_plans;")
    op.execute("DROP TABLE IF EXISTS tenants;")
