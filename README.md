# Invox: Multi-Tenant OCR Invoice Handler

An AI-powered invoice processing system with built-in billing and multi-tenant support.

## 🚀 Current Status: Transitioning to Frontend Phase
The backend infrastructure is functional with a "Developer Mock" credit system. We are now building the Next.js dashboard.

## 🛠 Tech Stack
- **Backend:** FastAPI (Python 3.12), PostgreSQL, SQLAlchemy/Psycopg2, Tesseract OCR.
- **Frontend:** Next.js 16 (App Router), Tailwind CSS, Shadcn/UI, TypeScript.
- **Billing:** MTN MoMo API (Sandbox Integration).

## ✅ What We've Built (Past 24 Hours)
- **Auth System:** JWT-based authentication with protected routes and role-based access.
- **Billing Engine:** Outbound "Request to Pay" integration with MTN MoMo Sandbox.
- **Credit System:** Manual credit injection utility and database schema for user balances.
- **Infrastructure:** Monorepo folder reorganization (`/backend` and `/frontend`).
- **OCR Engine:** Initial Tesseract configuration and preprocessing pipeline.

## ⚠️ Technical Debt (Known Issues)
- [ ] **Webhook Verification:** Signature validation for MTN MoMo callbacks is pending.
- [ ] **Idempotency:** Payment processing needs duplicate request protection.
- [ ] **Reconciliation:** No automated worker to sync missed payments.
- [ ] **Subdomain Routing:** Multi-tenancy URL logic needs implementation in Frontend Middleware.

## 🏗 Setup
### Backend
1. `cd backend`
2. `python3 -m venv .venv && source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `python3 main.py`

### Frontend
1. `cd frontend`
2. `npm install`
3. `npm run dev`
