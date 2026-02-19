# ClawHost — Production Deployment Guide

This guide covers steps to run ClawHost in production.

**For a step-by-step Railway + Vercel deployment, see [RAILWAY_VERCEL_SETUP.md](./RAILWAY_VERCEL_SETUP.md).**

---

## 1. Overview

**Components to deploy:**

| Component | Purpose |
|-----------|---------|
| **PostgreSQL** | Database (users, subscriptions, instances) |
| **Redis** | Queue backend for ARQ worker |
| **Backend (FastAPI)** | API, auth, Stripe, webhooks |
| **Worker (ARQ)** | Async provisioning jobs |
| **Frontend (Next.js)** | Dashboard UI |

**External services:** Stripe (live mode), Contabo API, optional Cloudflare DNS, optional Resend email.

---

## 2. Environment Configuration

### Backend `.env` (production)

```env
# Required: use strong values
APP_ENV=production
SECRET_KEY=<generate-with-secrets.token_urlsafe(32)>

# Database: use managed PostgreSQL (Supabase, Neon, RDS, etc.)
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/clawhost?ssl=require

# Redis: use managed Redis (Upstash, Redis Cloud, ElastiCache)
REDIS_URL=redis://default:password@host:6379/0
# Or Redis TLS: rediss://...

# CORS: your production frontend URL(s), comma-separated
CORS_ALLOWED_ORIGINS=https://app.clawhost.com,https://clawhost.com

# Stripe LIVE keys (not test)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_STARTER_PRICE_ID=price_...
STRIPE_PRO_PRICE_ID=price_...

# Contabo (production credentials)
CONTABO_API_URL=https://api.contabo.com
CONTABO_CLIENT_ID=...
CONTABO_CLIENT_SECRET=...
CONTABO_API_USER=...
CONTABO_API_PASSWORD=...

# Domain for customer instances (e.g. customers.clawhost.com)
CLAWHOST_BASE_DOMAIN=customers.clawhost.com

# Cloudflare (for auto DNS A records per instance)
CLOUDFLARE_API_TOKEN=...
CLOUDFLARE_ZONE_ID=...

# Email (Resend or similar)
RESEND_API_KEY=...
EMAIL_FROM=noreply@clawhost.com
```

### Frontend `.env.local` (production)

```env
NEXT_PUBLIC_API_URL=https://api.clawhost.com
```

---

## 3. Database

1. **Provision PostgreSQL** (Supabase, Neon, AWS RDS, etc.).
2. **Run migrations:**
   ```bash
   cd backend
   alembic upgrade head
   ```
3. **Backups:** Enable automated backups on your provider.

---

## 4. Redis

1. **Provision Redis** (Upstash, Redis Cloud, ElastiCache).
2. **Set `REDIS_URL`** in backend `.env`.
3. Use TLS (`rediss://`) if available for security.

---

## 5. Backend Deployment

**Option A: Docker**

```dockerfile
# backend/Dockerfile (example)
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Option B: Systemd or process manager**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

**Recommendations:**
- Run behind Nginx or Caddy (reverse proxy, SSL termination).
- Use multiple workers for uvicorn in production.
- Ensure `SECRET_KEY` is at least 32 chars and never committed.

---

## 6. Worker Deployment

The ARQ worker must run as a long-lived process:

```bash
arq app.queue.worker.WorkerSettings
```

- Same `REDIS_URL` and `DATABASE_URL` as backend.
- Can run on the same host or a separate machine.
- For high throughput, run multiple worker processes.

---

## 7. Frontend Deployment

**Build:**
```bash
cd frontend
npm run build
```

**Deploy options:**
- **Vercel:** Connect repo, set `NEXT_PUBLIC_API_URL`, deploy.
- **Docker:** Use `node:alpine` and `npm run start`.
- **Static export:** If applicable, `npm run build` and serve `out/` via CDN.

Ensure `NEXT_PUBLIC_API_URL` points to your production backend (e.g. `https://api.clawhost.com`).

---

## 8. Stripe (Live Mode)

1. **Switch to live mode** in Stripe Dashboard.
2. **Create products/prices** for Starter and Pro plans.
3. **Set live keys** in backend `.env`: `sk_live_...`, `pk_live_...`.
4. **Webhook endpoint:**
   - URL: `https://api.clawhost.com/webhooks/stripe`
   - Events: `checkout.session.completed`, `invoice.payment_failed`, `customer.subscription.deleted`
   - Copy webhook signing secret to `STRIPE_WEBHOOK_SECRET`.
5. **Update frontend** Stripe publishable key if you use Stripe.js (checkout uses redirect).

---

## 9. DNS & SSL

**ClawHost dashboard/app:**
- Point your domain (e.g. `app.clawhost.com`) to your frontend host.
- Point API domain (e.g. `api.clawhost.com`) to backend.
- Use Let's Encrypt (Certbot) or provider-managed SSL.

**Customer instances:**
- `CLAWHOST_BASE_DOMAIN` (e.g. `customers.clawhost.com`) must be a zone you control.
- Configure Cloudflare (`CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ZONE_ID`) so provisioning creates A records automatically.
- Each instance gets `{id}.customers.clawhost.com` → VPS IP; Certbot on the VPS handles SSL for those subdomains.

---

## 10. Security Checklist

- [ ] `SECRET_KEY` is strong and unique
- [ ] `APP_ENV=production`
- [ ] HTTPS everywhere (no HTTP in production)
- [ ] `CORS_ALLOWED_ORIGINS` set to your frontend domain(s) only
- [ ] Database and Redis use strong passwords / TLS
- [ ] Stripe webhook signature verified (already in code)
- [ ] No debug mode or verbose error pages exposed
- [ ] `.env` never committed; use secrets management

---

## 11. Monitoring & Health

- **Backend health:** `GET /health` returns `{"status":"ok"}`.
- **Worker:** Ensure it stays running (systemd, Docker restart policy, or platform health checks).
- **Logging:** Configure structured logging; consider Sentry for errors.
- **Uptime:** Use UptimeRobot, Pingdom, or similar for alerts.

---

## 12. Quick Reference: Production URLs

| Item | Example |
|------|---------|
| Frontend | `https://app.clawhost.com` |
| API | `https://api.clawhost.com` |
| Stripe webhook | `https://api.clawhost.com/webhooks/stripe` |
| Instance domain pattern | `*.customers.clawhost.com` |

---

## 13. Deployment Platforms

| Platform | Backend | Frontend | Worker | DB/Redis |
|----------|---------|----------|--------|----------|
| **Vercel** | — | ✅ | — | — |
| **Railway** | ✅ | ✅ | ✅ | ✅ (add-ons) |
| **Render** | ✅ | ✅ | ✅ | ✅ (add-ons) |
| **Fly.io** | ✅ | ✅ | ✅ | External |
| **AWS/GCP/Azure** | EC2/Cloud Run | Static/S3 | ECS/Lambda | RDS/ElastiCache |

Pick a platform that supports long-running processes (worker) and provides PostgreSQL + Redis or integration with managed services.
