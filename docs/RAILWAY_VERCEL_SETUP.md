# ClawHost — Railway + Vercel Setup Guide

Step-by-step deployment of ClawHost using **Railway** (backend, worker, PostgreSQL, Redis) and **Vercel** (frontend).

**Order of operations:** Create Railway project → Backend + DB + Redis → get Backend URL → run migrations → add Worker → Stripe webhook → Vercel frontend → set `CORS_ALLOWED_ORIGINS` and `NEXT_PUBLIC_API_URL` → verify.

---

## Prerequisites

- [ ] ClawHost repo pushed to **GitHub** (or GitLab/Bitbucket)
- [ ] **Stripe** account (live mode keys when ready)
- [ ] **Contabo** account (API credentials)
- [ ] **Railway** account — [railway.app](https://railway.app)
- [ ] **Vercel** account — [vercel.com](https://vercel.com)

---

## Part 1: Railway — Project Setup

### Step 1.1: Create a new project

1. Go to [railway.app](https://railway.app) and sign in (GitHub recommended).
2. Click **"New Project"**.
3. Choose **"Empty Project"** (we'll add services manually).

### Step 1.2: Add PostgreSQL

1. In the project, click **"+ New"** → **"Database"** → **"Add PostgreSQL"**.
2. Wait for PostgreSQL to provision (~30 seconds).
3. Click the PostgreSQL service → **"Variables"** tab.
4. Copy **`DATABASE_URL`** (format: `postgresql://user:pass@host:port/railway`).
5. **Important:** Our app uses `asyncpg`. Change the URL scheme:
   - From: `postgresql://...`
   - To: `postgresql+asyncpg://...`
   - Also add `?ssl=require` if Railway requires SSL: `postgresql+asyncpg://...?ssl=require`

### Step 1.3: Add Redis

1. Click **"+ New"** → **"Database"** → **"Add Redis"**.
2. Wait for Redis to provision.
3. Click the Redis service → **"Variables"** tab.
4. Copy **`REDIS_URL`** (or `REDIS_PRIVATE_URL` if you have both — use the private one for in-Railway traffic).

---

## Part 2: Railway — Backend Service

### Step 2.1: Deploy from GitHub

1. Click **"+ New"** → **"GitHub Repo"**.
2. Select your ClawHost repository.
3. Railway will create a new service and attempt a build.

### Step 2.2: Configure the Backend service

1. Click the new service (e.g. "clawhost" or your repo name).
2. Go to **"Settings"**:
   - **Root Directory:** Set to `backend`.
   - **Watch Paths:** `backend/**` (optional; ensures rebuilds only when backend changes).
3. **Start Command:** The repo uses a single start command in `backend/railway.json` that runs **Worker** (arq) when `CLAWHOST_RUN_WORKER` is set, otherwise **Backend** (uvicorn). Set the env var only on the Worker service:
   - **Backend (e.g. clawhost):** Do **not** set `CLAWHOST_RUN_WORKER`. It will run: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
   - **Worker (e.g. intelligent-smile):** In **Variables**, add `CLAWHOST_RUN_WORKER` = `true` (any non-empty value). It will run: `arq app.queue.worker.WorkerSettings`.
   (See [Part 3](#part-3-railway--worker-service) for the Worker.)

### Step 2.3: Add a database (reference)

1. In the Backend service → **"Variables"** tab.
2. Click **"+ Add Variable"** → **"Add Reference"**.
3. Select the PostgreSQL service → **`DATABASE_URL`**.
4. If Railway’s variable is `postgresql://`, create a **custom variable**:
   - Name: `DATABASE_URL`
   - Value: paste the PostgreSQL URL and change `postgresql://` to `postgresql+asyncpg://`, add `?ssl=require` if needed.
5. Do the same for **`REDIS_URL`** from the Redis service.

### Step 2.4: Set all Backend environment variables

In **Variables** for the Backend service, add:

| Variable | Value | Notes |
|----------|-------|-------|
| `APP_ENV` | `production` | |
| `SECRET_KEY` | (generate) | Run: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `DATABASE_URL` | (from PostgreSQL) | Use `postgresql+asyncpg://...` |
| `REDIS_URL` | (from Redis) | From Redis service variable |
| `CORS_ALLOWED_ORIGINS` | `https://your-app.vercel.app` | Set after Vercel deploy; update with custom domain later |
| `STRIPE_SECRET_KEY` | `sk_live_...` | Stripe Dashboard → API keys |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` | Set after creating webhook (Step 4) |
| `STRIPE_STARTER_PRICE_ID` | `price_...` | **Must be a price ID**, not a product ID. Stripe Dashboard → Products → your product → Pricing section → copy the **price** ID (starts with `price_`). |
| `STRIPE_PRO_PRICE_ID` | `price_...` | Same as above; use the price ID for the Pro plan. |
| `CONTABO_API_URL` | `https://api.contabo.com` | |
| `CONTABO_CLIENT_ID` | (your value) | Contabo Control Panel → API |
| `CONTABO_CLIENT_SECRET` | (your value) | |
| `CONTABO_API_USER` | (your API user email) | |
| `CONTABO_API_PASSWORD` | (your value) | |
| `CLAWHOST_BASE_DOMAIN` | `customers.yourdomain.com` | Your domain for instance subdomains |
| `CLOUDFLARE_API_TOKEN` | (optional) | For auto DNS |
| `CLOUDFLARE_ZONE_ID` | (optional) | |
| `RESEND_API_KEY` | (optional) | For provisioning emails |
| `EMAIL_FROM` | `noreply@yourdomain.com` | |
| `LOG_LEVEL` | `INFO` (optional) | Logging level; default INFO |
| `ADMIN_SECRET` | (optional) | Secret for admin API (X-Admin-Secret); needed for key pool endpoints |
| `GCP_PROJECT_ID` | (optional) | For automated Gemini key pool replenishment |
| `GOOGLE_APPLICATION_CREDENTIALS` | (optional) | Path or JSON for GCP; set in Worker too if using replenish |
| `GEMINI_KEY_POOL_MIN_AVAILABLE` | `2` (optional) | Min keys to keep in pool |
| `GEMINI_KEY_POOL_REPLENISH_ENABLED` | `false` (optional) | Set `true` to enable cron replenish (Worker must have GCP env) |

**Production requirement:** With `APP_ENV=production`, the app will **not start** unless `SECRET_KEY` is at least 32 characters and `CORS_ALLOWED_ORIGINS` is set. Set a placeholder for CORS (e.g. `https://placeholder.vercel.app`) before first deploy, then update after you have the real Vercel URL.

### Step 2.5: Run database migrations

Migrations run **automatically** on every Backend deploy: the start command in `backend/railway.json` runs `alembic upgrade head` before starting the API. So after the first successful deploy, the database will be up to date.

If you need to run migrations **before** the first deploy (e.g. you created the DB by hand), use one of these:

1. **Option A — Deploy once:** Push your code and let the Backend deploy. The start command will run migrations then start uvicorn. Check Backend logs to confirm “alembic upgrade head” completed.
2. **Option B — Local with public DB URL:** Railway’s Postgres service may expose a **public** URL. In Railway → Postgres → Variables (or Connect), copy the public `DATABASE_URL`. Convert to `postgresql+asyncpg://...` and add `?ssl=require` if needed. Then run locally (with venv activated): `$env:DATABASE_URL="..."; alembic upgrade head`. Note: `railway run alembic upgrade head` from your PC often fails with “getaddrinfo failed” because Railway’s default DB hostname is only reachable from inside Railway’s network.

### Step 2.6: Generate domain for Backend

1. Backend service → **"Settings"** → **"Networking"** (or "Generate Domain").
2. Click **"Generate Domain"**.
3. Copy the URL (e.g. `https://clawhost-backend-production-xxxx.up.railway.app`).
4. This is your **API URL**. You’ll use it for the frontend and Stripe webhook.

---

## Part 3: Railway — Worker Service

### Step 3.1: Add Worker from same repo

1. Click **"+ New"** → **"GitHub Repo"**.
2. Select the **same** ClawHost repository.
3. A second service is created.

### Step 3.2: Configure the Worker service

1. Click the new service → **"Settings"**:
   - **Root Directory:** `backend`
2. The start command is in `backend/railway.json` and runs the Worker when `CLAWHOST_RUN_WORKER` is set. In **Variables**, add `CLAWHOST_RUN_WORKER` = `true`. So this service runs arq; the Backend does not set this var and runs uvicorn.
   ```bash
   arq app.queue.worker.WorkerSettings
   ```
   (The start command is not in `railway.json`, so the field is editable in the UI. Do not use the Backend’s command here.)

### Step 3.3: Set Worker environment variables

1. Worker service → **"Variables"**.
2. Add the **same variables** as the Backend (or use **Shared Variables** if Railway supports it).
3. Minimum required: `DATABASE_URL`, `REDIS_URL`, `APP_ENV`, and all Contabo, Stripe, Cloudflare vars used by the provision job.
4. If you use **Gemini key pool replenishment** (cron), set `GEMINI_KEY_POOL_REPLENISH_ENABLED=true`, `GCP_PROJECT_ID`, and `GOOGLE_APPLICATION_CREDENTIALS` (or equivalent) on the Worker as well.
5. You can **reference** the Backend’s variables or duplicate them. Ensure `REDIS_URL` matches the Backend.

### Step 3.4: Deploy

1. Trigger a deploy (push to GitHub or manual "Redeploy").
2. Check **Logs** — you should see `arq` / worker startup messages.

---

## Part 4: Stripe Webhook

Create a webhook in Stripe so your backend is notified when a customer completes checkout, a payment fails, or a subscription is canceled.

### Step 4.1: Create the webhook in Stripe (clear steps)

1. **Open Stripe Dashboard**
   - Go to [https://dashboard.stripe.com](https://dashboard.stripe.com) and sign in.
   - Switch to **Live** or **Test** mode (top-right) depending on which keys you use in Railway.

2. **Open Webhooks**
   - Left sidebar → **Developers** → **Webhooks**.
   - Click **"+ Add endpoint"**.

3. **Endpoint URL**
   - In **Endpoint URL**, enter:
     ```text
     https://YOUR-RAILWAY-BACKEND-DOMAIN/webhooks/stripe
     ```
   - Replace `YOUR-RAILWAY-BACKEND-DOMAIN` with your Backend’s Railway domain (e.g. `clawhost-backend-production-xxxx.up.railway.app`).
   - Use `https://` and **no trailing slash**. Example:
     ```text
     https://clawhost-backend-production-xxxx.up.railway.app/webhooks/stripe
     ```

4. **Events to send**
   - Under **Select events to listen to**, choose **“Select events”** (do not use “Listen to all events”).
   - Add these three events (use the search box or scroll):
     - **`checkout.session.completed`** — when a customer finishes checkout (create subscription + start provisioning).
     - **`invoice.payment_failed`** — when a recurring payment fails (optional handling in your app).
     - **`customer.subscription.deleted`** — when a subscription is canceled (release instance / key pool).
   - Click **“Add endpoint”**.

5. **Get the signing secret**
   - On the new webhook’s page, under **Signing secret**, click **“Reveal”**.
   - Copy the value (it starts with **`whsec_`**). You will use it in Railway as `STRIPE_WEBHOOK_SECRET`.

### Step 4.2: Add webhook secret to Railway

1. In Railway, open your **Backend** service.
2. Go to the **Variables** tab.
3. Add (or edit) a variable:
   - **Name:** `STRIPE_WEBHOOK_SECRET`
   - **Value:** the `whsec_...` value you copied from Stripe.
4. Save. Redeploy the Backend if it was already running so it picks up the new variable.

---

## Part 5: Vercel — Frontend

### Step 5.1: Import project

1. Go to [vercel.com](https://vercel.com) and sign in (GitHub recommended).
2. Click **"Add New..."** → **"Project"**.
3. Import your ClawHost repository.
4. **Framework Preset:** Next.js (auto-detected).

### Step 5.2: Configure build

1. **Root Directory:** `frontend` (or leave blank if repo root is frontend).
2. **Build Command:** `npm run build` (default).
3. **Output Directory:** `.next` (default for Next.js).
4. **Install Command:** `npm install` (default).

### Step 5.3: Environment variables

1. In project **Settings** → **Environment Variables**, add:

| Name | Value | Environment |
|------|-------|-------------|
| `NEXT_PUBLIC_API_URL` | `https://YOUR-RAILWAY-BACKEND-DOMAIN` | Production, Preview |

2. Use your Railway Backend domain (e.g. `https://clawhost-backend-production-xxxx.up.railway.app`).
3. No trailing slash.

### Step 5.4: Deploy

1. Click **"Deploy"**.
2. After deployment, copy the project URL (e.g. `https://clawhost-xxx.vercel.app`).

### Step 5.5: Update CORS in Railway

1. Backend service → **Variables**.
2. Set `CORS_ALLOWED_ORIGINS` to the **exact** origin of your frontend (the full URL from the browser address bar, without path or trailing slash).
   - **Vercel production:** e.g. `https://clawhost.vercel.app`
   - **Vercel preview/deploy URL:** e.g. `https://clawhost-n3491z3wj-rcat36410-3461s-projects.vercel.app` — copy from the address bar when you open the app.
   - Multiple origins: comma-separated, no spaces: `https://app.clawhost.com,https://clawhost.vercel.app`
3. Redeploy Backend after changing variables.

---

## Part 6: Verify Deployment

### 6.1: Health check

```bash
# Liveness (process up)
curl https://YOUR-RAILWAY-BACKEND-DOMAIN/health
# Expected: {"status":"ok"}

# Readiness (DB + Redis reachable; use for load balancer health checks if supported)
curl https://YOUR-RAILWAY-BACKEND-DOMAIN/health/ready
# Expected: {"status":"ready","checks":{"database":"ok","redis":"ok"}}
```

### 6.2: Frontend

1. Open your Vercel URL.
2. Register a new account.
3. Log in and open the dashboard.
4. Try **Subscribe** and complete a test checkout (use Stripe test mode first if preferred).

### 6.3: Worker

1. Railway → Worker service → **Logs**.
2. After a subscription, you should see the provisioning job running.
3. Check for errors (Contabo, Redis, DB).

---

## Part 7: Custom Domains (Optional)

### Railway (API)

1. Backend service → **Settings** → **Networking** → **Custom Domain**.
2. Add `api.yourdomain.com` (or similar).
3. Add the CNAME record in your DNS provider.
4. Update `NEXT_PUBLIC_API_URL` and `CORS_ALLOWED_ORIGINS` accordingly.
5. Update Stripe webhook URL.

### Vercel (Frontend)

1. Project → **Settings** → **Domains**.
2. Add `app.yourdomain.com`.
3. Follow Vercel’s DNS instructions.
4. Update `CORS_ALLOWED_ORIGINS` in Railway.

---

## Troubleshooting

| Issue | Check |
|-------|-------|
| **Failed to fetch** (Subscribe / API calls) | 1) **Vercel:** `NEXT_PUBLIC_API_URL` = your Railway Backend URL (e.g. `https://clawhost-production-xxxx.up.railway.app`). 2) **Railway:** `CORS_ALLOWED_ORIGINS` must include the **exact** frontend origin from the browser (e.g. `https://clawhost-n3491z3wj-rcat36410-3461s-projects.vercel.app`). No trailing slash. For multiple deployments, add comma-separated origins. |
| CORS errors | `CORS_ALLOWED_ORIGINS` matches frontend URL exactly (no trailing slash) |
| 502 / timeout | Backend start command correct; check Railway logs |
| Worker not processing jobs | Same `REDIS_URL` as Backend; worker logs for errors |
| DB connection failed | `postgresql+asyncpg://` in `DATABASE_URL`; `?ssl=require` if needed |
| App won't start (production) | `SECRET_KEY` ≥ 32 chars; `CORS_ALLOWED_ORIGINS` non-empty |
| Stripe webhook 401 | Correct `STRIPE_WEBHOOK_SECRET`; webhook URL uses HTTPS |
| **No such price / prod_ in Stripe** | `STRIPE_STARTER_PRICE_ID` and `STRIPE_PRO_PRICE_ID` must be **price** IDs (`price_...`), not product IDs (`prod_...`). In Stripe Dashboard → Product → Pricing, copy the price ID. |
| **Product is not active** | Stripe error "product is not active" or "not available to be purchased": the product linked to that price is archived or draft. Stripe Dashboard → Product catalogue → open the product → set status to **Active** (or unarchive). |
| Provisioning fails | Contabo credentials; Redis reachable from Worker |
| **Instance stuck in "provisioning"** | 1) **Railway → Worker → Logs**: the provision job logs when it starts, when it can't find the instance, when Contabo isn't configured, when create_vps fails, and when the VPS never reaches "running". Look for `provision_instance started`, `no instance in provisioning`, `Contabo not configured`, `create_vps failed`, or `timed out waiting for VPS`. 2) **Contabo dashboard** ([new.contabo.com/servers/vps](https://new.contabo.com/servers/vps)): check if a new VPS was created and its state. 3) Ensure **Worker** has the same **Contabo** and **Redis** env vars as Backend (REDIS_URL, CONTABO_*). 4) Provisioning can take 10–20+ min (poll every 60s, up to ~30 min). Use "Retry provisioning" after fixing config. |
| 503 on /health/ready | DB or Redis down; check Railway service status and vars |

---

## Cost Estimate

| Service | Approx. cost |
|---------|--------------|
| Railway (Backend + Worker + PostgreSQL + Redis) | ~$5–20/mo (usage-based) |
| Vercel (Frontend) | Free tier often sufficient |
| **Total** | ~$5–25/mo |

---

## Quick Reference

| Item | Where |
|------|-------|
| API URL | Railway Backend → Generate Domain |
| Frontend URL | Vercel project URL |
| Stripe webhook | `{API_URL}/webhooks/stripe` |
| CORS | `CORS_ALLOWED_ORIGINS` = frontend URL (required in production) |
| Health (liveness) | `GET /health` |
| Health (readiness) | `GET /health/ready` (DB + Redis) |
