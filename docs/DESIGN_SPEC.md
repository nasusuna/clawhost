# ClawBolt — Design Specification

**Product:** Managed OpenClaw Hosting (One-Click Deploy)  
**Reference products:** [easyclaw.in](https://easyclaw.in), [breezeclaw.com](https://breezeclaw.com)  
**Status:** Draft for review  
**Last updated:** 2025-02-18

---

## 1. Product Overview

ClawBolt provides **managed OpenClaw instances** on dedicated VPS. Each customer gets one Contabo (or alternative) VPS, one Dockerized OpenClaw container, one subdomain, and one isolated environment. Billing and lifecycle are driven by Stripe subscriptions; provisioning and teardown are automated via provider API + queue-based jobs.

**Core value:** Stripe → Backend → Provider API → Queue → SSH/Cloud-Init → Docker OpenClaw → Customer.

---

## 2. High-Level Architecture

```
Customer
   ↓
Frontend (Next.js dashboard)
   ↓
Backend API (FastAPI recommended)
   ↓
Stripe (subscriptions + webhooks)
   ↓
Job Queue (BullMQ or equivalent — async provisioning)
   ↓
Provider API (Contabo / Vultr / DO — VPS create/stop/delete)
   ↓
Provisioning (Cloud-Init + optional SSH validation)
   ↓
DNS (Cloudflare API — per-instance A records)
   ↓
Customer OpenClaw Instance (Docker + Nginx + SSL)
```

**Architecture model:** **Dedicated VPS per customer** (Model A). One VPS, one Docker container (OpenClaw), one subdomain, one isolated environment. Enables clean billing and straightforward shutdown on payment failure or cancellation.

---

## 3. Recommended Tech Stack

| Layer        | Choice              | Notes |
|-------------|---------------------|--------|
| **Frontend** | Next.js + Tailwind + shadcn/ui | Dashboard; JWT auth. |
| **Backend**  | **FastAPI** (preferred over Node) | Better fit for async SSH, asyncio, Pydantic validation. |
| **Database** | PostgreSQL + **SQLAlchemy** | If FastAPI; otherwise Prisma with Node. |
| **Queue**    | BullMQ (or similar)  | Async provisioning; retries, backoff. |
| **Infra**    | Contabo / Vultr / DigitalOcean | Consider Vultr/DO for better APIs, cloud-init, regions. |
| **Runtime**  | Docker + Watchtower  | OpenClaw in container; Watchtower for auto-updates. |
| **DNS**      | Cloudflare API       | Automated A records per instance; avoid manual wildcards at scale. |
| **Payments** | Stripe Subscriptions + Webhooks | Checkout, webhooks for lifecycle. |

---

## 4. Database Schema

### 4.1 Core Tables

**Users**

| Column            | Type     | Notes |
|-------------------|----------|--------|
| id                | UUID PK  | |
| email             | string   | Unique. |
| password_hash     | string   | |
| stripe_customer_id| string   | Nullable until first checkout. |
| created_at        | timestamptz | |

**Subscriptions**

| Column                 | Type     | Notes |
|------------------------|----------|--------|
| id                     | UUID PK  | |
| user_id                | FK       | |
| stripe_subscription_id | string   | Unique. |
| status                 | enum     | `active` \| `past_due` \| `canceled` |
| plan_type              | string   | e.g. starter, pro. |
| current_period_end     | timestamptz | |

**Instances**

| Column            | Type     | Notes |
|-------------------|----------|--------|
| id                | UUID PK  | |
| user_id           | FK       | |
| provider_vps_id   | string   | Contabo/Vultr/DO instance ID. |
| ip_address        | string   | Public IP. |
| root_password     | string   | Encrypted; optional if key-only. |
| ssh_private_key   | string   | **Encrypted**; ed25519 per instance. |
| status            | enum     | `provisioning` \| `running` \| `stopped` \| `deleted` |
| domain            | string   | e.g. `customerid.yourdomain.com`. |
| provision_job_id  | string   | **For retries and idempotency.** |
| last_heartbeat    | timestamptz | **For health checks.** |
| created_at        | timestamptz | |

### 4.2 Optional: Usage & Abuse Control

**UsageMetrics** (recommended before scale)

- Track CPU/memory (e.g. from provider API or agent on VPS) per instance, billed or sampled hourly.
- Use for caps, alerts, and “pause on 90% CPU” logic.

---

## 5. Subscription Flow (Stripe-Driven)

1. **User subscribes**  
   Frontend → Stripe Checkout (session or Payment Element).

2. **Success**  
   Stripe webhook → `POST /webhooks/stripe`.  
   Event: `checkout.session.completed`.

3. **Backend (idempotent):**
   - Create or link **User** (by email).
   - Create/update **Subscription** (status `active`, store `stripe_subscription_id`, `plan_type`, `current_period_end`).
   - **Enqueue provisioning job** (do not block webhook). Return 200 quickly.

4. **No synchronous VPS creation in webhook** — all provisioning in queue job.

---

## 6. VPS Provisioning Flow (Queue + Provider API)

**Goal:** Reliable, retryable provisioning with **Cloud-Init** for one-shot setup; SSH only for validation if needed.

### 6.1 Enqueue Job

- Inputs: `user_id`, `subscription_id`, `plan_type`, `region` (from product/plan).
- Store `provision_job_id` on Instance row (status `provisioning`).

### 6.2 Create VPS (Provider API)

- Call provider: create VPS (e.g. Ubuntu 22.04), **with Cloud-Init user-data**.
- **Cloud-Init script** (YAML) must:
  - Install Docker: `curl -fsSL https://get.docker.com | sh`.
  - Run OpenClaw:  
    `docker run -d --restart always -p 80:3000 --name openclaw --security-opt no-new-privileges --cpus=2 --memory=4g openclaw/image:latest`.
  - Install Nginx + Certbot (or embed Nginx config + certbot run).
  - Configure Nginx reverse proxy to `localhost:3000` and run certbot for the **allocated subdomain** (passed in user-data).
- Store: `provider_vps_id`, `ip_address`, and (if applicable) encrypted `root_password` or generate and store SSH key.

### 6.3 Poll Until Ready

- Poll provider **status** every **60s**, **max 30 attempts** (e.g. ~30 min), with **exponential backoff**.
- On `running`: proceed. On timeout/failure: retry job (queue) or mark instance as failed and notify.

### 6.4 DNS

- **Cloudflare API:** Create **A record** for `customerid.yourdomain.com` → VPS public IP.  
- Avoid shared IP; one A record per VPS.  
- Do not rely on manual wildcard at scale.

### 6.5 Optional SSH Validation

- Single SSH connection (key-based, not password) to verify Docker container is running (e.g. `docker ps`).
- **Security:** Disable password login from day one; use ed25519 keys; restrict port 22 to backend IP and/or close after provisioning (e.g. after 1h timeout).

### 6.6 Finalize

- Update Instance: `status = running`, `domain`, `last_heartbeat`.
- Send email: Login URL, default credentials (if any), IP.

---

## 7. Instance Lifecycle Logic

| State            | Condition                         | Backend action |
|------------------|-----------------------------------|----------------|
| **Active**       | Stripe subscription `active`, VPS running | Normal operation. |
| **Payment failed** | Stripe `invoice.payment_failed`   | Call provider power-off; set instance `status = stopped`; email user. |
| **Canceled**     | Stripe `customer.subscription.deleted` | Call provider delete VPS; set `status = deleted`. Optionally keep snapshot 7 days. |

---

## 8. Subdomain Strategy

- **Domain:** You own `yourdomain.com` (or `customers.yourdomain.com`).
- **Per customer:** `{customer_id}.yourdomain.com` (or similar).
- **Mechanism:** **Cloudflare API** — create A record when VPS is ready. No manual wildcard for per-customer scaling; wildcard can still point to a landing page if needed.

---

## 9. Security Design

| Area        | Measure |
|------------|---------|
| **SSH**    | Disable password login from day one; ed25519 keys per instance; restrict port 22 to backend IP; close 22 after provisioning window (e.g. 1h) if possible. |
| **Firewall (VPS)** | UFW: allow only 80, 443, and (temporarily) 22 from backend. |
| **Container** | `--security-opt no-new-privileges`; resource limits `--cpus=2 --memory=4g`. |
| **API**    | JWT auth; rate limiting (e.g. express-rate-limit or FastAPI middleware); validate provider credentials per tenant. |
| **OpenClaw** | Enforce customer API keys; monitor CPU/memory (e.g. Prometheus) if needed. |

---

## 10. Cost & Abuse Control

- **No “unlimited” AI** — tier by vCPU/RAM explicitly (e.g. Starter: 4GB/2vCPU cap).
- **UsageMetrics:** Integrate provider metrics (or agent) for alerts; optional “pause on 90% CPU” webhook.
- **Pre-define limits** in product (e.g. Starter vs Pro) and enforce in container limits and monitoring.

**Pricing example (for reference only):**

| Plan   | Price (example) | VPS spec |
|--------|------------------|----------|
| Starter | ₹2499/mo        | 4GB      |
| Pro     | ₹3999/mo        | 8GB      |

Margin target: ~₹1500–2500 per customer after provider cost (e.g. ₹900–1200/mo).

---

## 11. Health & Reliability

- **Cron:** Ping `https://{instance.domain}/health` (or similar). If repeatedly down, mark instance or alert.
- **last_heartbeat:** Update from health checks or lightweight agent on VPS.
- **Idempotency:** Provisioning script and queue jobs must be idempotent; use `provision_job_id` and guardrails so retries don’t double-create resources.

---

## 12. Scaling Plan (Post-MVP)

- **Phase 1:** 1 VPS per customer (current design).
- **Phase 2:** Pre-warm VPS pool for faster deployment.
- **Phase 3:** Consider orchestration (e.g. Kubernetes) when justified by scale.

---

## 13. Modules to Implement (Cursor / Codebase)

| Module              | Purpose |
|---------------------|--------|
| `/auth`             | Register, login, JWT issue/validate. |
| `/subscription`     | Plans, Stripe Checkout session, subscription status. |
| `/webhooks/stripe`  | Handle `checkout.session.completed`, `invoice.payment_failed`, `customer.subscription.deleted`. |
| `/provision`        | Queue job: create VPS (with Cloud-Init), poll, DNS, optional SSH check, DB + email. |
| `/instances`        | CRUD, list, status, start/stop if supported. |
| `/contabo` (or `/provider`) | Wrapper for Contabo/Vultr/DO API (create, power-off, delete, status). |
| `/ssh`              | Key generation, optional one-time SSH validation. |
| `/email`            | Transactional email (provisioning done, payment failed, canceled). |
| `/dns` (or inside `/provision`) | Cloudflare API: create/update A record. |

---

## 14. Deployment Time Estimate (MVP)

| Component           | Estimate   |
|--------------------|------------|
| Backend API        | 5–7 days   |
| Stripe integration | 2 days     |
| Provider + queue + Cloud-Init | 3–5 days |
| Dashboard (Next.js)| 5 days     |
| **MVP total**      | **~3 weeks** (focused) |

---

## 15. Critical Don’ts

- Do **not** offer unlimited AI usage.
- Do **not** underprice initially.
- Do **not** allow heavy compute abuse — enforce tiers and limits.
- Do **not** do synchronous VPS creation in Stripe webhook — use queue.
- Do **not** rely on manual DNS at scale — use Cloudflare API.

---

## 16. Summary of Changes vs. Original ChatGPT Design

| Area           | Original idea           | Design spec choice |
|----------------|-------------------------|--------------------|
| Provisioning   | SSH + inline scripts    | **Queue + Cloud-Init**; poll 60s, max 30x, backoff; optional SSH validation. |
| DNS            | Manual wildcard or ad hoc | **Cloudflare API**, one A record per VPS. |
| Security       | Basic                   | **SSH keys only**, disable password; container limits and no-new-privileges; firewall. |
| Schema         | Minimal                 | **provision_job_id**, **last_heartbeat**, **ssh_private_key** (encrypted); optional UsageMetrics. |
| Backend        | Node or FastAPI         | **FastAPI** preferred; SQLAlchemy if FastAPI. |
| Provider       | Contabo only            | Contabo **or** Vultr/DO for better API and cloud-init. |

---

*End of Design Spec. Ready for your review.*
