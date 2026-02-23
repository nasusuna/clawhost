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

**Instance flow:** User signs up → pays via Stripe → new VPS is provisioned → OpenClaw is installed in Docker with **Google Gemini** as the default model. A Gemini API key is injected automatically (see [Per-instance Gemini API key](#per-instance-gemini-api-key) below).

---

## 2. Production checklist (pre-launch)

Use this before going live.

**Backend**

- [ ] `APP_ENV=production`
- [ ] `SECRET_KEY` set to a strong value (min 32 chars); app will not start in production with the default
- [ ] `CORS_ALLOWED_ORIGINS` set to your frontend URL(s); app will not start in production if empty
- [ ] `DATABASE_URL` and `REDIS_URL` point to production instances (TLS where available)
- [ ] Stripe **live** keys and webhook secret configured
- [ ] Contabo (or provider) credentials set
- [ ] Migrations run: `alembic upgrade head`
- [ ] Optional: `LOG_LEVEL=INFO` (or `WARNING` to reduce noise)

**Frontend**

- [ ] `NEXT_PUBLIC_API_URL` set to your production API URL (e.g. `https://api.clawhost.com`); build and deploy with this so the client talks to the right backend
- [ ] Build succeeds: `npm run build`

**Health & deploy**

- [ ] Liveness: `GET /health` returns `{"status":"ok"}`
- [ ] Readiness: `GET /health/ready` returns `{"status":"ready","checks":{"database":"ok","redis":"ok"}`; use this for load balancers or Kubernetes. If DB or Redis is down, returns 503.
- [ ] Worker process running (`arq app.queue.worker.WorkerSettings`) with same env as backend

**Security**

- [ ] HTTPS only; no HTTP in production
- [ ] `.env` / secrets never committed; use platform secrets (Railway, Vercel, etc.)

---

## 3. Environment Configuration

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

## 4. Database

1. **Provision PostgreSQL** (Supabase, Neon, AWS RDS, etc.).
2. **Run migrations:**
   ```bash
   cd backend
   alembic upgrade head
   ```
3. **Backups:** Enable automated backups on your provider.

---

## 5. Redis

1. **Provision Redis** (Upstash, Redis Cloud, ElastiCache).
2. **Set `REDIS_URL`** in backend `.env`.
3. Use TLS (`rediss://`) if available for security.

---

## 6. Backend Deployment

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

## 7. Worker Deployment

The ARQ worker must run as a long-lived process:

```bash
arq app.queue.worker.WorkerSettings
```

- Same `REDIS_URL` and `DATABASE_URL` as backend.
- Can run on the same host or a separate machine.
- For high throughput, run multiple worker processes.

---

## 8. Frontend Deployment

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

## 9. Stripe (Live Mode)

1. **Switch to live mode** in Stripe Dashboard.
2. **Create products/prices** for Starter and Pro plans.
3. **Set live keys** in backend `.env`: `sk_live_...`, `pk_live_...`.
4. **Webhook endpoint:**
   - URL: `https://api.clawhost.com/webhooks/stripe`
   - Events: `checkout.session.completed`, `invoice.payment_failed`, `customer.subscription.deleted`
   - Copy webhook signing secret to `STRIPE_WEBHOOK_SECRET`.
5. **Update frontend** Stripe publishable key if you use Stripe.js (checkout uses redirect).

---

## 10. DNS & SSL

**ClawHost dashboard/app:**
- Point your domain (e.g. `app.clawhost.com`) to your frontend host.
- Point API domain (e.g. `api.clawhost.com`) to backend.
- Use Let's Encrypt (Certbot) or provider-managed SSL.

**Customer instances:**
- `CLAWHOST_BASE_DOMAIN` (e.g. `customers.clawhost.com`) must be a zone you control.
- Configure Cloudflare (`CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ZONE_ID`) so provisioning creates A records automatically.
- Each instance gets `{id}.customers.clawhost.com` → VPS IP; Certbot on the VPS handles SSL for those subdomains.

---

## 11. Security Checklist

- [ ] `SECRET_KEY` is strong and unique
- [ ] `APP_ENV=production`
- [ ] HTTPS everywhere (no HTTP in production)
- [ ] `CORS_ALLOWED_ORIGINS` set to your frontend domain(s) only
- [ ] Database and Redis use strong passwords / TLS
- [ ] Stripe webhook signature verified (already in code)
- [ ] No debug mode or verbose error pages exposed
- [ ] `.env` never committed; use secrets management

---

## 12. Monitoring & Health

- **Liveness:** `GET /health` returns `{"status":"ok"}`. Use for process managers.
- **Readiness:** `GET /health/ready` checks database and Redis; returns 200 with `{"status":"ready","checks":{"database":"ok","redis":"ok"}` when both are up, or 503 with `{"status":"degraded","checks":{...}}` when one fails. Use for load balancers and Kubernetes.
- **Logging:** Set `LOG_LEVEL=INFO` (or `WARNING`) in production. Startup and shutdown are logged; no secrets in log format.
- **Worker:** Ensure it stays running (systemd, Docker restart policy, or platform health checks).
- **Uptime:** Use UptimeRobot, Pingdom, or similar; monitor `/health` and optionally `/health/ready`.

---

## 13. Recommended instance layout (Contabo VPS)

A typical **per-instance** stack on a Contabo (or similar) VPS:

```
Contabo VPS
│
├── Nginx (SSL)          ← Terminates HTTPS, proxies to OpenClaw
├── Docker
│   ├── OpenClaw         ← Gateway + Control UI (port 18789)
│   ├── Ollama           ← Local LLM (port 11434)
│   └── Postgres         ← Optional: DB for this instance if needed
│
└── Ollama and OpenClaw on the same Docker network
```

- **Nginx** on the host: listens on 80/443, terminates SSL (Certbot), proxies `/` to OpenClaw. Add the instance domain (or IP) to `server_name` and set `trustedProxies` in OpenClaw so the gateway treats the connection as local.
- **Docker network:** Create a shared bridge network (e.g. `openclaw-net`). Run Ollama and OpenClaw on that network so OpenClaw reaches Ollama at `http://ollama:11434` (container name or service name). No need for host network unless you prefer it.
- **Postgres** in Docker is optional for the instance itself; the ClawHost platform usually uses a separate managed Postgres for the dashboard/API.

Current install script uses **host network** for OpenClaw and **Ollama on the host** (systemd) so OpenClaw can use `127.0.0.1:11434`. The layout above is the recommended **all-Docker** variant: same Docker network for OpenClaw and Ollama, Nginx on host for SSL.

---

## 14. Ollama as base model on instances

Each instance can use **Ollama** as a local LLM provider so OpenClaw can run models (e.g. Llama, Mistral) on the same VPS with no external API keys. See [OpenClaw Ollama docs](https://docs.openclaw.ai/providers/ollama).

### New instances (automatic)

Cloud-init already installs Ollama and starts OpenClaw with `OLLAMA_API_KEY=ollama-local` and `--network host`, so OpenClaw auto-discovers Ollama at `127.0.0.1:11434`. After provisioning, a default model (`llama3.2`) is pulled in the background. In the OpenClaw Control UI, choose an Ollama model (e.g. `ollama/llama3.2`) as the agent’s primary model.

### Existing instance (e.g. 144.91.98.32)

Run the install script **on the VPS** (via SSH):

1. Copy the script to the server (or paste its contents into a file):
   - `backend/scripts/install-ollama-openclaw-on-server.sh`
2. Ensure LF line endings: `sed -i 's/\r$//' ./install-ollama-openclaw-on-server.sh`
3. Run with your instance domain and gateway token (from the ClawHost dashboard):

   ```bash
   chmod +x install-ollama-openclaw-on-server.sh
   sudo OPENCLAW_GATEWAY_TOKEN='<paste-token-from-dashboard>' ./install-ollama-openclaw-on-server.sh <instance-domain>
   ```

   Example:

   ```bash
   sudo OPENCLAW_GATEWAY_TOKEN='abc123...' ./install-ollama-openclaw-on-server.sh abc123.customers.clawhost.com
   ```

4. Optional: change the default model by setting `OLLAMA_DEFAULT_MODEL` (e.g. `ollama pull qwen2.5-coder:32b` then use `ollama/qwen2.5-coder:32b` in OpenClaw).

The script installs Ollama, pulls a model, and recreates the OpenClaw container with host networking so it can reach Ollama at `127.0.0.1:11434`.

### Running Ollama in Docker (same network as OpenClaw)

To run **Ollama in Docker** on the same network as OpenClaw (recommended layout):

**1. Create a Docker network and run Ollama**

On the VPS:

```bash
# Create shared network
sudo docker network create openclaw-net 2>/dev/null || true

# Run Ollama (official image; use --gpus=all if you have NVIDIA GPU)
sudo docker run -d --restart always \
  --network openclaw-net \
  --name ollama \
  -v ollama-data:/root/.ollama \
  ollama/ollama

# Wait for API, then pull a model
sleep 5
sudo docker exec ollama ollama pull llama3.2:latest
```

Ollama is now reachable at `http://ollama:11434` from any container on `openclaw-net`. No need to publish port 11434 to the host unless you want to call Ollama from the host (e.g. for debugging).

**2. Run OpenClaw on the same network**

Stop and remove the existing OpenClaw container if it uses host network, then start it on `openclaw-net` and publish only port 18789 to the host (for Nginx):

```bash
sudo docker stop openclaw 2>/dev/null || true
sudo docker rm openclaw 2>/dev/null || true

sudo docker run -d --restart always \
  --network openclaw-net \
  -p 127.0.0.1:18789:18789 \
  -e OLLAMA_API_KEY=ollama-local \
  -e OPENCLAW_GATEWAY_TOKEN='YOUR_GATEWAY_TOKEN' \
  --name openclaw \
  --security-opt no-new-privileges \
  --cpus=2 --memory=4g \
  fourplayers/openclaw:latest
```

Replace `YOUR_GATEWAY_TOKEN` with the token from the ClawHost dashboard.

**3. Point OpenClaw config at Ollama by hostname**

In OpenClaw config (`openclaw.json`), set the Ollama provider to use the container name:

```json
"models": {
  "providers": {
    "ollama": {
      "baseUrl": "http://ollama:11434",
      "api": "ollama",
      "apiKey": "ollama-local",
      "models": [
        { "id": "llama3.2:latest", "name": "Llama 3.2", "contextWindow": 32768, "maxTokens": 32768 }
      ]
    }
  }
}
```

Then run `openclaw doctor --fix` and restart OpenClaw:

```bash
sudo docker exec openclaw openclaw doctor --fix
sudo docker restart openclaw
```

Nginx on the host continues to proxy to `127.0.0.1:18789`. Both containers use the same Docker network so OpenClaw can reach `http://ollama:11434` without exposing Ollama on the host.

### "No configured models" / Can't type in Primary Model

If the Primary model dropdown is empty or the field is not editable, add an **explicit Ollama provider** in the Control UI:

1. Open **Settings** → **Config** → **Raw** (Raw JSON5).
2. Add a top-level `models` block (or merge into existing config). For host network use:

```json5
"models": {
  "providers": {
    "ollama": {
      "baseUrl": "http://127.0.0.1:11434",
      "apiKey": "ollama-local",
      "models": [
        {
          "id": "llama3.2:latest",
          "name": "Llama 3.2",
          "contextWindow": 32768,
          "maxTokens": 32768
        }
      ]
    }
  }
}
```

3. Click **Save** (or **Apply**), then go to **Agents** → **main** → **Overview**. The Primary model dropdown should list `ollama/llama3.2:latest`; select it and save. If your `ollama list` shows a different tag, use that as `id` (e.g. `llama3.2`).

### Chat shows "fetch failed" (Ollama works in terminal)

If the Control UI Chat shows "fetch failed" but Ollama responds to `ollama run llama3.2:latest "Hi"` on the server:

1. **Browser:** Open DevTools (F12) → **Network**. Send a message in Chat, then find the failed request. Note the **URL**, **status code** (e.g. 401, 502), and any response body. That identifies whether the failure is auth, proxy, or agent.
2. **Server logs:** On the VPS run `docker logs -f openclaw` and reproduce the Chat action. Look for errors when the UI sends a message (e.g. connection refused to Ollama, session error, or auth).
3. **Access by domain:** Use the instance **domain** (e.g. `your-instance.customers.clawhost.com`) instead of the raw IP, and ensure Nginx has a `server` block for that host so all paths (including Chat API) are proxied to OpenClaw.
4. **Gateway token:** If the gateway uses token auth, ensure the token is set when starting the container (e.g. `OPENCLAW_GATEWAY_TOKEN` from the install script) and that the Control UI is loaded from the same origin that the gateway expects (no cross-origin or wrong port).

### Control UI Save fails / "Invalid config" (v2026.2.17)

In OpenClaw v2026.2.17 the Control UI form or validation can reject valid config (silently drop fields, fail schema checks, or overwrite with minimal content). **Bypass the UI** and edit the config file directly.

**On the instance (SSH into the VPS):**

1. **Back up:**  
   - If OpenClaw runs **natively:** `cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak`  
   - If OpenClaw runs in **Docker:**  
     `docker cp openclaw:/home/node/.openclaw/openclaw.json ~/openclaw.json.bak` (or backup from inside the container).

2. **Replace config:**  
   - **Native:** Edit `~/.openclaw/openclaw.json` and paste your full JSON.  
   - **Docker:** Create the file on the host, then  
     `docker cp ./openclaw.json openclaw:/home/node/.openclaw/openclaw.json`  
     Or: `docker exec -i openclaw sh -c 'cat > /home/node/.openclaw/openclaw.json' < ./openclaw.json`

3. **Validate:**  
   - **Native:** `openclaw doctor --fix`  
   - **Docker:** `docker exec openclaw openclaw doctor --fix`

4. **Restart:**  
   - **Native:** `openclaw gateway --force` (or restart your process manager).  
   - **Docker:** `docker restart openclaw`

After that, the gateway should load the new config. Use the Control UI only for reading if you hit save/validation bugs again.

### "Failed to discover Ollama models: fetch failed" / "No API provider registered for api: undefined" / Health Offline (1006)

These usually go together: the OpenClaw container cannot reach Ollama, so the Ollama provider never registers. When you send a chat message, the gateway crashes with "No API provider registered for api: undefined" and the WebSocket drops (1006).

**Cause:** (1) Inside the container, `http://127.0.0.1:11434` is the container itself unless the container uses the host network. (2) With an **explicit** `models.providers.ollama` block, OpenClaw requires `"api": "ollama"` so the provider is registered; without it you get "No API provider registered for api: undefined" and the gateway crashes when you send a message. If the container was started with bridge networking (e.g. `-p 127.0.0.1:18789:18789` only), Ollama on the host is not at 127.0.0.1 from the container's perspective.

**Fix:**

1. **Add `"api": "ollama"` to the Ollama provider** (required when using an explicit `models.providers.ollama` block). In `openclaw.json`, the ollama block should include:
   ```json
   "ollama": {
     "baseUrl": "http://127.0.0.1:11434",
     "api": "ollama",
     "apiKey": "ollama-local",
     "models": [ ... ]
   }
   ```
   Without `"api": "ollama"`, the stream layer does not register the provider and the gateway crashes on first chat message.

2. **Confirm Ollama is running on the host** (on the VPS):
   ```bash
   curl -s http://127.0.0.1:11434/api/tags
   ```
   You should see JSON with your models. If not, start Ollama: `sudo systemctl start ollama`.

3. **Confirm OpenClaw uses host network** so that 127.0.0.1 inside the container is the host:
   ```bash
   docker inspect openclaw --format '{{.HostConfig.NetworkMode}}'
   ```
   It must print `host`. If it prints `default` (bridge), recreate the container with host network so it can reach Ollama at 127.0.0.1:11434. Use the same pattern as `backend/scripts/install-ollama-openclaw-on-server.sh`: stop/rm the container, then `docker run -d --restart always --network host ... openclaw`.

4. **Restart OpenClaw** after fixing config or Ollama:
   ```bash
   sudo docker restart openclaw
   ```
   Then try Chat again. "Failed to discover Ollama models" should stop and the gateway should no longer crash on send.

### Chat shows "fetch failed" (dashboard can't reach backend)

The red "fetch failed" in the dashboard usually means the browser cannot complete a request to the OpenClaw gateway (wrong status, timeout, or auth). Diagnose and fix:

1. **Network tab:** Press **F12** → **Network**. Refresh the page or repeat the action that fails. Look for **failed requests** (red rows). Note the **URL**, **status code** (e.g. 401 Unauthorized, 404 Not Found, 500 Server Error), and response body. That identifies whether the issue is auth, wrong path, or gateway error.
2. **Gateway token:** Ensure the **Gateway Token** is set when starting the container and matches what the UI/API expects. If it's wrong or missing, requests can return 401 and show as "fetch failed".
   - **Check if the token is set on the container:**  
     `sudo docker exec openclaw printenv OPENCLAW_GATEWAY_TOKEN`  
     If this prints nothing, the variable is not set.
   - **Where the token comes from:** ClawHost dashboard → your instance → copy the gateway token (or use the value you passed when running the install script).
   - **Fix:** Recreate the container with the correct token. Example (replace with your token and domain):
     ```bash
     sudo docker stop openclaw && sudo docker rm openclaw
     sudo docker run -d --restart always --network host \
       -e OLLAMA_API_KEY=ollama-local \
       -e OPENCLAW_GATEWAY_TOKEN='PASTE_TOKEN_FROM_DASHBOARD' \
       --name openclaw --security-opt no-new-privileges --cpus=2 --memory=4g \
       fourplayers/openclaw:latest
     ```
     Or re-run the install script with the token:  
     `sudo OPENCLAW_GATEWAY_TOKEN='your-token' ./install-ollama-openclaw-on-server.sh your-domain`
3. **Doctor (repair):** On the instance, run the built-in repair so config and state are consistent:
   ```bash
   sudo docker exec openclaw openclaw doctor --fix
   ```
   Then restart: `sudo docker restart openclaw`.

### Chat shows "fetch failed" / "Reason: global update" / no assistant reply

Often the UI shows "fetch failed" and "Run: openclaw doctor --non-interactive" when the gateway hit an error (e.g. session file locked, or agent run timeout) and no reply was returned. Fix:

1. **Remove stale session lock files** (can cause "session file locked" and blocked replies):
   ```bash
   sudo docker exec openclaw find /home/node/.openclaw/agents -name "*.lock" -type f -delete
   ```
2. **Run doctor** (as the UI suggests):
   ```bash
   sudo docker exec openclaw openclaw doctor --non-interactive
   ```
3. **Restart the gateway**:
   ```bash
   sudo docker restart openclaw
   ```
4. In the dashboard, click **New session**, then send a short message (e.g. "hi"). Use a new session so the previous broken one is not reused.

### Doctor: "State directory permissions are too open" / "chmod 700"

If `openclaw doctor` recommends tightening permissions on `~/.openclaw`:

```bash
sudo docker exec openclaw chmod 700 /home/node/.openclaw
sudo docker exec openclaw chown -R node:node /home/node/.openclaw
```

Then restart: `sudo docker restart openclaw`.

### Doctor: "Missing transcripts" / "Main session transcript missing"

Doctor may report that a session file (e.g. `.../sessions/<id>.jsonl`) is missing. Chat history for that session will reset; this is safe to ignore. To start clean, you can remove the session metadata (or leave it; OpenClaw will create new transcripts for new messages).

### Doctor: "Failed to discover Ollama models: fetch failed" / "gateway connect failed: pairing required"

- **Ollama fetch failed:** Same cause and fix as [above](#failed-to-discover-ollama-models-fetch-failed--no-api-provider-registered-for-api-undefined--health-offline-1006): container must use host network and reach Ollama (e.g. `baseUrl: "http://127.0.0.1:11434"`), and Ollama must be running on the host.
- **Pairing required:** The gateway is running (port 18789 in use) but the client (e.g. Control UI) must complete device pairing. Open the Control UI in the browser and complete any pairing or login step. If you use token auth only, ensure `OPENCLAW_GATEWAY_TOKEN` is set and the UI sends that token.

### Server shows "webchat connected" but UI shows "fetch failed" / "WebSocket connection to 'ws://...' failed"

The gateway log shows a connection from `127.0.0.1` (Nginx), but the **browser** fails to open the WebSocket. Common cause: you open the dashboard by **IP** (e.g. `http://144.91.98.32/`) while Nginx is configured with `server_name` set to your **instance domain** (e.g. `abc123.customers.clawhost.com`). Requests to the IP then hit the **default** server block, which may not proxy to OpenClaw or may not support WebSocket.

**Fix:**

1. **Use the instance domain in the browser** (recommended): open `http://<instance-domain>/` (e.g. `http://your-instance.customers.clawhost.com`) so the correct Nginx `server_name` block handles both the page and the WebSocket.
2. **If you must use the IP:** on the VPS, add a server block that matches the IP (or make the OpenClaw block the default) and proxies to OpenClaw with WebSocket support. Example (run on the server):
   ```bash
   sudo nano /etc/nginx/sites-available/openclaw
   ```
   In the `server` block, add the IP to `server_name` (e.g. `server_name your-domain.com 144.91.98.32;`) or add a separate `server { listen 80 default_server; server_name _; ... }` with the same `location / { proxy_pass ...; proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade"; proxy_read_timeout 86400; }`. Then `sudo nginx -t && sudo systemctl reload nginx`.

After changing Nginx, reload the dashboard in the browser (and use the domain if possible).

### "Proxy headers detected from untrusted address"

When you use the Control UI through Nginx (or another reverse proxy), the gateway may log: *"Proxy headers detected from untrusted address. Connection will not be treated as local. Configure gateway.trustedProxies to restore local client detection behind your proxy."*

**Fix:** Add `trustedProxies` to the `gateway` block in OpenClaw config so the gateway trusts your proxy and restores local client detection:

```json
"gateway": {
  "trustedProxies": ["127.0.0.1", "::1"],
  ...
}
```

If Nginx runs on the same host as OpenClaw, `127.0.0.1` and `::1` are enough. If the proxy is on another machine, add its IP or CIDR. Then run `openclaw doctor --fix` and restart the container.

---

## 15. Per-instance Gemini API key

New instances are provisioned with **OpenClaw preconfigured for Google Gemini** (default model `google/gemini-2.5-flash-lite`). A Gemini API key must be available so the agent can call the model.

### How the key is chosen

Resolution order when a new instance is provisioned:

1. **Per-instance (set at checkout or later):** If the instance has `gemini_api_key` set, that key is used. **When GCP is configured, the Stripe webhook creates one new Gemini API key per successful subscription** and attaches it to the new instance, so each paying user gets a dedicated key without using the pool.
2. **Shared key:** If the instance has no key, the backend uses the optional **`GEMINI_API_KEY`** from its own `.env`.
3. **Key pool:** If still no key, the backend assigns one **unassigned** key from the **Gemini key pool** (table `gemini_key_pool`). When the subscription is deleted, a pool key is released; per-subscription keys (created at checkout) are not returned to the pool.

Cloud-init writes a minimal `openclaw.json` (Gemini as default model, no key in the file) and, when a key is provided, passes it into the container as **`GEMINI_API_KEY`** (key is base64-encoded in user-data and decoded on the server for security).

### Key pool: create N keys and assign when a new user is created

1. **Create keys** (e.g. in [Google AI Studio](https://aistudio.google.com/apikey) or via [Google Cloud API Keys API](https://cloud.google.com/docs/authentication/api-keys#creating_api_keys)).
2. **Set `ADMIN_SECRET`** in backend `.env` (any strong secret; used as header for admin endpoints).
3. **Add keys to the pool** via the admin API (one or bulk):
   - **POST /admin/gemini-key-pool** — body: `{"api_key": "..."}`. Add one key.
   - **POST /admin/gemini-key-pool/bulk** — body: `{"api_keys": ["...", "..."]}`. Add multiple keys.
   - Send header: **`X-Admin-Secret: <ADMIN_SECRET>`**.
4. **Check pool stats:** **GET /admin/gemini-key-pool** (same header). Returns `{"available": N, "in_use": M}`.
5. When a **new user** subscribes and the instance is provisioned, if the instance has no user-set key and there is no `GEMINI_API_KEY` in env, the worker picks one available key from the pool, assigns it to that instance, and injects it into the VPS. When the subscription is **deleted**, the key is released back to the pool (`instance_id` set to `NULL`).

### One key per subscription (create on Stripe checkout)

If **GCP is configured** on the Backend (`GCP_PROJECT_ID` or `GOOGLE_CLOUD_PROJECT`, and `GOOGLE_APPLICATION_CREDENTIALS` or ADC), then on **successful Stripe subscription** (webhook `checkout.session.completed`):

1. A **new Gemini API key** is created via the Google Cloud API Keys API (restricted to `generativelanguage.googleapis.com`).
2. The key is stored on the new **instance** (`instance.gemini_api_key`).
3. The provision job runs as usual and injects this key into the OpenClaw config for that instance.

So each paying subscriber gets a **dedicated key**; when they open OpenClaw, the Gemini API is already configured. No key pool is used for that instance. If key creation fails (e.g. GCP credentials missing or rate limit), the provision job falls back to shared key or pool as above.

### One GCP project per subscription (recommended for $15 budget cap)

To enforce a **hard spending limit per user** (e.g. $15/month) using GCP Billing, you can create **one GCP project per subscription**. On each successful Stripe checkout the backend will:

1. **Create a new GCP project** under your organization (Cloud Resource Manager API).
2. **Enable** the Generative Language API for that project (Service Usage API).
3. **Link the project to your billing account** (Cloud Billing API).
4. **Create a monthly budget** for that project (e.g. $15) with a 100% threshold alert (Billing Budgets API). You can then enable any “cap” or “disable billing” option in GCP Console if your billing product supports it.
5. **Create a Gemini API key** in that project and attach it to the new instance.

Each subscriber’s usage is billed to their project; you can set budgets and (where available) caps per project. The subscription’s `gcp_project_id` is stored for reference.

**Configuration (Backend / Worker env):**

- `GCP_PROJECT_PER_SUBSCRIPTION_ENABLED=true`
- `GCP_ORGANIZATION_ID` — your GCP organization ID (numeric, e.g. `123456789012`).
- `GCP_BILLING_ACCOUNT_ID` — billing account ID (e.g. `01ABC2D-3EF4G5-6789HI`) or full resource name `billingAccounts/01ABC2D-...`.
- `GCP_BUDGET_AMOUNT_USD` — monthly budget amount per new project (default `15`).
- Same credentials as for other GCP features: `GOOGLE_APPLICATION_CREDENTIALS` (or ADC). The service account must have: **Project Creator** (on the org), **Service Usage Admin**, **Billing User** (link project to billing account), **Budget Admin** (create budgets), **API Keys Admin** (create keys in the new project).

**Dependencies:** `google-cloud-resource-manager`, `google-cloud-billing`, `google-cloud-billing-budgets`, `google-api-python-client` (see `backend/requirements.txt`). Run migration `006_add_subscription_gcp_project_id` so `subscriptions.gcp_project_id` exists.

**Detailed setup (migration, GCP org/billing, service account, IAM, env vars, deploy):** see **[GCP_ONE_PROJECT_PER_SUBSCRIPTION_SETUP.md](./GCP_ONE_PROJECT_PER_SUBSCRIPTION_SETUP.md)**.

If per-subscription project creation is disabled or fails, the backend falls back to creating the key in the single project given by `GCP_PROJECT_ID` / `GOOGLE_CLOUD_PROJECT` as above.

**Limiting spend per key (e.g. ~$15/month):** With **one project per subscription** and a budget (and optional cap) on that project, GCP can enforce the limit. With a **single shared project**, Google Cloud does **not** support a per–API-key spending cap; use **quotas** (APIs & Services → Generative Language API → Quotas) or **project-level budgets** for alerts. For **monitoring per-key usage** and **options to cap each user** (separate projects vs app-level proxy), see **docs/GEMINI_PER_USER_MONITORING_AND_CAPS.md**.

### Generating keys for every user

**Google does not let you programmatically “generate” arbitrary Gemini API keys for end users.** Keys are created by:

- **End users:** In [Google AI Studio](https://aistudio.google.com/apikey) (free tier available). Your app can ask users to paste their key in the dashboard and store it per instance (`PATCH /instances/{id}`).
- **You (shared key):** Create one key in AI Studio or Google Cloud, set `GEMINI_API_KEY` in backend `.env`; every new instance gets that key.
- **You (programmatic):** Use [Google Cloud API Keys API](https://cloud.google.com/docs/authentication/api-keys#creating_api_keys) to create keys under your GCP project. That requires a GCP project, billing, and a service account with “API Keys Admin”. Keys you create are tied to your project and quota. Google does not publish a hard limit on the **number** of API keys per project; the only documented limits are **rate limits** on the API Keys API (e.g. 120 write calls per minute). So you can create many keys; throttle creation if you provision a large number of instances at once.

**Create one key via GCP and store in DB:** The backend script `backend/scripts/create_gemini_key_gcp.py` creates a single API key restricted to `generativelanguage.googleapis.com` and inserts it into `gemini_key_pool`. Prerequisites: (1) GCP project with **API Keys API** and **Generative Language API** enabled; (2) a service account with role **API Keys Admin** (or permission `apikeys.keys.create`); (3) Application Default Credentials — set `GOOGLE_APPLICATION_CREDENTIALS` to the service account JSON path, or run `gcloud auth application-default login`. Set `GOOGLE_CLOUD_PROJECT` or `GCP_PROJECT_ID` and `DATABASE_URL`, then run from the backend directory: `python scripts/create_gemini_key_gcp.py`. The script uses `google-cloud-api-keys` (see `requirements.txt`).

**Create multiple keys via GCP (bulk):** Run `python scripts/create_gemini_keys_gcp_bulk.py [N]` from the backend directory with the same env as above. `N` is the number of keys to create (default 5, max 50). Each key is created via the GCP API Keys API and stored in `gemini_key_pool`; a 2-second delay between creations helps avoid rate limits.

**Automated key replenishment (no manual runs):** The ARQ worker can replenish the pool automatically so you never run the script by hand.

- **Prerequisites (same as above):** GCP project with **API Keys API** and **Generative Language API** enabled; a **service account** with role **API Keys Admin** (or `apikeys.keys.create`); **Application Default Credentials** available to the worker process (e.g. `GOOGLE_APPLICATION_CREDENTIALS` pointing to the service account JSON, or workload identity in Cloud Run/GKE).
- **Backend env (where the ARQ worker runs):**
  - `GCP_PROJECT_ID` or `GOOGLE_CLOUD_PROJECT` — your GCP project ID.
  - `GOOGLE_APPLICATION_CREDENTIALS` — path to the service account JSON (or leave unset if using workload identity / gcloud default).
  - `GEMINI_KEY_POOL_MIN_AVAILABLE` — minimum number of unassigned keys to keep in the pool (default `2`).
  - `GEMINI_KEY_POOL_REPLENISH_ENABLED=true` — turn on automated replenishment.
- **Behavior:** A cron job in the ARQ worker runs every 6 hours (00:00, 06:00, 12:00, 18:00 UTC). If the number of available (unassigned) keys is below `GEMINI_KEY_POOL_MIN_AVAILABLE`, it creates keys via the GCP API Keys API and stores them in the DB until the threshold is met (up to 5 keys per run to respect rate limits). No manual script runs needed.
- **Deploy:** Ensure the **ARQ worker** is running (e.g. `arq app.queue.worker.WorkerSettings`); it must have the same env as above so it can call GCP and the database.

Recommended for ClawHost: **user-supplied key** (optional field in dashboard before or after checkout) and/or **one shared `GEMINI_API_KEY`** in backend env for trials.

### Backend env

```env
# Optional: used for new instances when the instance has no gemini_api_key set
GEMINI_API_KEY=your-key-from-google-ai-studio
```

### API

- **PATCH /instances/{instance_id}** — body: `{"gemini_api_key": "optional string"}`. Sets or clears the per-instance key. Used on **next** provision (or retry); existing VPS is not updated automatically.
- **Admin (header `X-Admin-Secret: <ADMIN_SECRET>`):**
  - **POST /admin/gemini-key-pool** — body: `{"api_key": "..."}`. Add one key to the pool.
  - **POST /admin/gemini-key-pool/bulk** — body: `{"api_keys": ["...", "..."]}`. Add multiple keys.
  - **GET /admin/gemini-key-pool** — returns `{"available": N, "in_use": M}`.

---

## 16. Telegram channel on instances

OpenClaw can receive and reply to messages via a **Telegram bot** (DMs and optional groups). You provide the bot token; ClawHost does not store it. Configure it in OpenClaw on your instance.

### 1. Create the bot and get the token

1. In Telegram, open a chat with **@BotFather** (exact handle).
2. Send `/newbot`, follow the prompts (name and username), and copy the **token** (e.g. `123456789:ABCdefGHI...`).
3. Optional: for groups where the bot should see all messages (not only when mentioned), in BotFather run `/setprivacy` → **Disable**; then remove and re-add the bot to each group.

### 2. Add Telegram to OpenClaw config

**Option A – Edit config on the server (recommended)**

SSH to the VPS, then:

1. **Back up:**  
   `docker cp openclaw:/home/node/.openclaw/openclaw.json ~/openclaw.json.bak`

2. **Get current config:**  
   `docker cp openclaw:/home/node/.openclaw/openclaw.json ./openclaw.json`  
   Edit `openclaw.json` on your machine and add a top-level `channels` object (merge with existing keys if you already have `channels`):

```json
"channels": {
  "telegram": {
    "enabled": true,
    "botToken": "YOUR_BOT_TOKEN_FROM_BOTFATHER",
    "dmPolicy": "pairing",
    "groups": { "*": { "requireMention": true } }
  }
}
```

3. **Put config back and fix permissions:**  
   `docker cp ./openclaw.json openclaw:/home/node/.openclaw/openclaw.json`  
   `docker exec openclaw chown node:node /home/node/.openclaw/openclaw.json && docker exec openclaw chmod 600 /home/node/.openclaw/openclaw.json`

4. **Validate and restart:**  
   `docker exec openclaw openclaw doctor --fix`  
   `docker restart openclaw`

**Option B – Environment variable (single bot)**

If you prefer not to put the token in config, you can set it in the container env and rely on the default account:

- When creating/starting the OpenClaw container, add:  
  `-e TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_FROM_BOTFATHER`  
  Then in config you only need `channels.telegram.enabled: true` (and optionally `dmPolicy`, `groups`). Config values override the env.

### 3. Approve DMs (pairing)

By default, DMs use **pairing**: only approved users can chat.

1. **Start the gateway** (it runs automatically in the container after restart).
2. **Open Telegram** and send a message to your bot (e.g. "hi"). The bot will respond with a pairing code or instructions.
3. **On the VPS**, list and approve the pending pairing:

   ```bash
   docker exec openclaw openclaw pairing list telegram
   docker exec openclaw openclaw pairing approve telegram <CODE>
   ```

   Codes expire after about 1 hour. After approval, that Telegram user can use the bot in DM.

**Alternative – allowlist by user ID:**  
To allow specific users without pairing, set `dmPolicy` to `"allowlist"` and add your Telegram numeric user IDs to `allowFrom`, e.g. `"allowFrom": ["123456789"]`. You can get your ID by DMing the bot and reading `from.id` in `docker exec openclaw openclaw logs --follow`, or via [Telegram Bot API getUpdates](https://core.telegram.org/bots/api#getupdates).

### 4. Optional: use the bot in a group

1. Add the bot to the Telegram group.
2. If the bot should see all messages (not only when @mentioned), disable Privacy Mode in BotFather (`/setprivacy` → Disable) and remove + re-add the bot to the group.
3. In config you can restrict which groups are allowed and whether mention is required, e.g.:

```json
"channels": {
  "telegram": {
    "enabled": true,
    "botToken": "YOUR_TOKEN",
    "dmPolicy": "pairing",
    "groups": {
      "*": { "requireMention": true }
    }
  }
}
```

Use a specific group ID (e.g. `"-1001234567890"`) instead of `"*"` to allow only that group. Get the group ID from `openclaw logs --follow` when someone posts in the group (see `chat.id`), or from Telegram Bot API `getUpdates`.

### 5. Troubleshooting

- **Bot doesn’t respond in DM:** Run `openclaw pairing list telegram` and approve your code; ensure `channels.telegram.enabled` is `true` and the gateway was restarted after config change.
- **Bot doesn’t see group messages:** Ensure the bot is in the group; if `groups` is set, the group must be listed or use `"*"`; if you need all messages, disable Privacy Mode and re-add the bot.
- **`setMyCommands` failed:** Outbound HTTPS to `api.telegram.org` may be blocked (firewall/DNS). Check from the host: `curl -sI https://api.telegram.org`.

Full reference: [OpenClaw Telegram channel](https://docs.openclaw.ai/channels/telegram).

---

## 17. Quick Reference: Production URLs

| Item | Example |
|------|---------|
| Frontend | `https://app.clawhost.com` |
| API | `https://api.clawhost.com` |
| Stripe webhook | `https://api.clawhost.com/webhooks/stripe` |
| Instance domain pattern | `*.customers.clawhost.com` |

---

## 18. Deployment Platforms

| Platform | Backend | Frontend | Worker | DB/Redis |
|----------|---------|----------|--------|----------|
| **Vercel** | — | ✅ | — | — |
| **Railway** | ✅ | ✅ | ✅ | ✅ (add-ons) |
| **Render** | ✅ | ✅ | ✅ | ✅ (add-ons) |
| **Fly.io** | ✅ | ✅ | ✅ | External |
| **AWS/GCP/Azure** | EC2/Cloud Run | Static/S3 | ECS/Lambda | RDS/ElastiCache |

Pick a platform that supports long-running processes (worker) and provides PostgreSQL + Redis or integration with managed services.
