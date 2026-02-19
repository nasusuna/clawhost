# ClawHost

Managed OpenClaw Hosting — one-click deploy, dedicated VPS, Stripe billing.

## Repo layout

- **backend/** — FastAPI app (auth, subscription, Stripe webhooks, provisioning queue, instances API)
- **frontend/** — Next.js 14 dashboard (Tailwind, App Router)
- **docs/** — DESIGN_SPEC.md

## Backend (FastAPI)

### Setup

**Use Python 3.11 or 3.12** (3.14 is too new; many packages have no pre-built wheels and would require Rust to build.)

```bash
cd backend
py -3.12 -m venv .venv
# or: python3.12 -m venv .venv   if you have that
```

**Activate the venv (pick one):**

- **PowerShell:** `.\.venv\Scripts\Activate.ps1`  
  If you get an execution policy error: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- **CMD:** `.venv\Scripts\activate.bat`
- **Git Bash / WSL:** `source .venv/Scripts/activate`

Then:

```bash
pip install -r requirements.txt
copy .env.example .env     # Windows (use cp on Git Bash/WSL)
# Edit .env with your DB, Stripe, Redis, Contabo, etc.
```

### Database

- PostgreSQL with `asyncpg`. Set `DATABASE_URL` in `.env`.
- Migrations: `alembic upgrade head`
- Or create tables in dev: ensure DB exists, then run app (optional `init_db` on startup).

### Run API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# or: python run.py
```

### Run worker (provisioning jobs)

```bash
arq app.queue.worker.WorkerSettings
```

Requires Redis at `REDIS_URL`.

### Endpoints

- `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
- `GET /subscription/plans`, `GET /subscription/me`, `POST /subscription/checkout`
- `GET /instances`, `GET /instances/{id}`
- `POST /webhooks/stripe` (Stripe webhook; set `STRIPE_WEBHOOK_SECRET`)

## Frontend (Next.js)

### Setup

```bash
cd frontend
npm install
cp .env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Run

```bash
npm run dev
```

Open http://localhost:3000 — home, login, register, dashboard, instances, subscribe.

## Contabo (provider)

Set in backend `.env`:

- `CONTABO_API_URL` — default `https://api.contabo.com`
- `CONTABO_CLIENT_ID`, `CONTABO_CLIENT_SECRET` — from [Customer Control Panel → API](https://my.contabo.com/api/details)
- `CONTABO_API_USER` — API user (email)
- `CONTABO_API_PASSWORD` — API password (set via link from control panel)

Plan mapping: `starter` → VPS 10 SSD (V92), `pro` → VPS 20 SSD (V95). Create uses cloud-init `userData` for Docker + OpenClaw + Nginx + Certbot. The default OpenClaw image is `fourplayers/openclaw:latest` (Control UI on port 18789). Override with `OPENCLAW_DOCKER_IMAGE` and `OPENCLAW_APP_PORT` in backend `.env` if needed.

### Test Contabo connection

With backend venv activated and Contabo vars in `.env`:

```bash
cd backend
python scripts/test_contabo.py
```

This checks OAuth token and lists instances (read-only). If you see "Contabo connection test passed", credentials and API are working.

### Fix existing instance (Nginx default page → OpenClaw)

If an instance already provisioned shows "Welcome to nginx!" instead of OpenClaw, fix it on the server (Option B):

1. **Get the instance domain** from the dashboard (e.g. `d47ba3bd7376.customers.yourdomain.com`).
2. **SSH into the VPS** (use the instance IP from the dashboard; you need root or sudo and Docker/Nginx already installed).
3. **Copy and run the fix script** from this repo:
   - Copy `backend/scripts/fix-nginx-openclaw-on-server.sh` to the server (or paste its contents into a file there).
   - Run: `chmod +x fix-nginx-openclaw-on-server.sh` then  
     `sudo ./fix-nginx-openclaw-on-server.sh <instance-domain>`

The script: stops the old OpenClaw container, starts the image `fourplayers/openclaw:latest` on `127.0.0.1:18789` only, adds an Nginx reverse-proxy config for your domain, reloads Nginx, and runs Certbot for HTTPS (if DNS points to the server). After that, the instance URL should serve the OpenClaw Control UI. To use a different image or port, set `OPENCLAW_DOCKER_IMAGE` and/or `OPENCLAW_APP_PORT` before running the script.

## Design

See **docs/DESIGN_SPEC.md** for architecture, flows, and implementation notes.

## Production

- **Railway + Vercel:** Step-by-step guide → **docs/RAILWAY_VERCEL_SETUP.md**
- **General:** **docs/PRODUCTION.md** — deployment options, env config, Stripe live mode, security
