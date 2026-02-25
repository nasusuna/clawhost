# Monitoring and capping per-user Gemini API usage ($15/month)

When **user1** has **key1** and **user2** has **key2** in the **same GCP project**, you want to:

1. **Monitor** each user’s (each key’s) usage.
2. **Restrict** each to ~$15/month.

---

## ClawBolt dashboard and 60M token cap

ClawBolt tracks **Gemini token usage per instance** (per month) and shows it on the **Dashboard**:

- **GET /usage** (authenticated): returns per-instance `tokens_used`, `tokens_cap` (60M), `period_end`, and `over_limit`.
- **Dashboard**: "Gemini token usage" card with a progress bar and "Usage limit reached — API disabled until next period" when over 60M tokens.
- **Recording usage**: **POST /admin/instances/:id/usage** (header `X-Admin-Secret`) with body `{ "tokens_delta": N }` to add or subtract tokens for that instance's current month. Use this from a **proxy** (see below) or from a reporter that sends usage from OpenClaw.

**Enforcing "disable at 60M":** The dashboard is informational. To actually stop API calls when the cap is met you need one of:

1. **Proxy:** Run Gemini requests through a ClawBolt proxy endpoint that checks usage before forwarding; if `over_limit`, return **429** and do not call Gemini. OpenClaw would need to call this proxy URL instead of Gemini directly (if it supports a custom base URL).
2. **Key revocation:** When usage reaches 60M, revoke or clear the instance's Gemini key (e.g. via GCP or by clearing `instance.gemini_api_key`). This only takes effect after OpenClaw restarts or refetches config; there is no live config push today.

---

## Monitoring usage per key

### Request counts per key

- In **GCP Console** go to **APIs & Services** → **Enabled APIs** → **Generative Language API** → **Metrics** (or the API’s metrics/dashboard).
- Use the **credentials** (or similar) filter to select **API key** and pick the key by **name** (e.g. `ClawBolt sub <subscription_id_hex>`).
- You can see **request volume** (and often quota usage) **per credential**.

So you can monitor **user1 vs user2** by selecting each key in the metrics and comparing request counts.

### Cost per key

- The **Billing** report in GCP does **not** break down cost by API key; charges are at **project** level.
- So you **cannot** see “user1 = $X, user2 = $Y” directly in the billing UI in the same project.

To get approximate **cost per user** you can:

1. **Estimate from metrics:** Use request counts (and token counts if available) per key from the API metrics above, then apply [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing) to estimate $ per key.
2. **Use one project per user:** Create a separate GCP project per subscriber and create the key in that project. Then each project’s **Billing** tab is that user’s cost (see “Restricting to $15/month” below).

---

## Restricting each user to ~$15/month

Google Cloud has **no** “per–API-key spending limit” in a single project. You have two practical options.

### Option 1: Separate GCP project per user (native $ cap)

- Create a **dedicated GCP project** per subscriber (or tenant).
- Create the Gemini API key **in that project**.
- In **Billing → Budgets**, create a **Budget** for that project (e.g. $15/month) and, if the product supports it, enable **cap** so spend is hard-limited.

**Pros:** Real $ per user in Billing; real $15 cap per project.  
**Cons:** ClawBolt must support creating keys in **different** projects (e.g. per-instance or per-subscription `GCP_PROJECT_ID` or a project pool). More ops (many projects).

### Option 2: Application-level tracking and cap (single project)

- Keep **one** GCP project; all keys (key1, key2, …) live there.
- Your system **tracks usage per key** (e.g. request count or token count) and **estimates cost** from [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing).
- When a key’s estimated cost exceeds a threshold (e.g. $15), you **disable or revoke that key** (or throttle requests).

**Challenge:** OpenClaw runs on the user’s VPS and calls the **Gemini API directly** with the key. ClawBolt does **not** see those requests. So to track and cap you need one of:

- **Proxy:** A service that sits in front of Gemini, receives requests (with key), forwards to Gemini, counts usage per key, and **blocks or throttles** when over cap. Most reliable for a hard “$15/user” limit in one project.
- **Usage reported by client:** OpenClaw (or your app) sends usage (e.g. tokens or cost) to ClawBolt; you aggregate and revoke keys when over cap. Depends on client honesty and implementation.
- **GCP export + attribution:** Use Cloud Billing export (e.g. to BigQuery) and try to attribute usage to keys. Billing export often does **not** identify API key per row for Generative Language API; if it does, you can build dashboards and alerts (and optionally revoke keys when over cap).

**Summary:** For a **hard** $15/user cap with **one** project, a **proxy** that counts usage per key and blocks when over cap is the most reliable approach.

---

## Summary table

| Goal | How |
|------|-----|
| **Monitor** usage per key (requests) | **APIs & Services** → **Generative Language API** → **Metrics** → filter by credential (API key). |
| **See $ per user** in GCP | Use **one project per user**; each project’s Billing = that user’s cost. |
| **Hard cap $15/user** | **One project per user** + **Budget** at $15 (with cap if available), **or** **app-level** (e.g. proxy) that tracks usage per key and revokes/throttles when over $15. |

---

## References

- [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Stack Overflow: Gemini API keys usage per API key](https://stackoverflow.com/questions/78814277/gemini-api-keys-usage-per-api-key) — notes that cost report does not break down by API key; metrics can show requests per credential.
- GCP Console: **APIs & Services** → **Generative Language API** → **Metrics** (and **Credentials** for key names).
