# One GCP project per subscription — detailed setup

This guide walks you through enabling **one GCP project per subscription**: on each successful Stripe checkout, ClawHost creates a new GCP project, enables the Generative Language API, links billing, creates a $15 budget, and creates a Gemini API key in that project. Use this for a **$15/month cap per user** via GCP Billing.

**Prerequisites:** You already have ClawHost deployed (Backend + Worker on Railway, Stripe, Contabo, etc.). See [RAILWAY_VERCEL_SETUP.md](./RAILWAY_VERCEL_SETUP.md) and [PRODUCTION.md](./PRODUCTION.md).

---

## Step 1: Run the database migration

The `subscriptions` table needs a `gcp_project_id` column.

### 1.1 Locally (before or after deploy)

```bash
cd backend
# Ensure DATABASE_URL is set (e.g. from .env or export) to your production DB if you want to migrate prod
export DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/clawhost?ssl=require"
alembic upgrade head
```

You should see migration `006_add_subscription_gcp_project_id` applied.

### 1.2 On Railway (if you prefer to run migration there)

1. In Railway, open your **Backend** service.
2. Go to **Settings** → find **Deploy** or **Custom start command** (or use a one-off run).
3. Run a one-off command in the Backend service (Railway may offer “Run command” or you can use the shell from a deploy):
   - Command: `alembic upgrade head`
   - Ensure the same `DATABASE_URL` and env as the Backend so it connects to your PostgreSQL.

Alternatively, run the migration locally once with `DATABASE_URL` pointing at your Railway PostgreSQL (copy the URL from Railway → PostgreSQL → Variables, change to `postgresql+asyncpg://...?ssl=require`).

---

## Step 2: GCP setup

You need a **Google Cloud organization**, a **billing account**, and a **service account** with the right roles. The Backend/Worker will use this service account (via `GOOGLE_APPLICATION_CREDENTIALS`) to create projects and keys.

### 2.1 Get your Organization ID

1. Open [Google Cloud Console](https://console.cloud.google.com).
2. In the top bar, click the **project selector** (project name).
3. In the dialog, open the **Organization** dropdown or look for **Organization** in the left panel.
4. Your **Organization ID** is a numeric value (e.g. `123456789012`).  
   - If you don’t see an organization, you may be under “No organization”. **One project per subscription requires an organization.** Create or join an organization in [Cloud Identity / Admin](https://admin.google.com) and link it to Google Cloud, or use a Google Workspace org.

Write it down: **`GCP_ORGANIZATION_ID`** = `________________`.

### 2.2 Get your Billing Account ID

1. In GCP Console go to **Billing** → [Billing](https://console.cloud.google.com/billing).
2. Select the billing account you will use for ClawHost subscriber projects.
3. Open **Account management** (or the account name). The **Billing account ID** is in the URL or on the page (e.g. `01ABC2D-3EF4G5-6789HI`).  
   - You can use either the ID alone or the full resource name: `billingAccounts/01ABC2D-3EF4G5-6789HI`.

Write it down: **`GCP_BILLING_ACCOUNT_ID`** = `________________`.

### 2.3 Create a service account for ClawHost

1. In GCP Console, select a **project** where you will manage this service account (can be your main ClawHost project or a dedicated “admin” project).
2. Go to **IAM & Admin** → [Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts).
3. Click **+ Create Service Account**.
4. **Service account name:** e.g. `clawhost-project-creator`.
5. **Service account ID:** (auto-filled). Click **Create and Continue**.
6. **Grant access (optional):** Skip for now; we’ll grant roles at org/billing level. Click **Continue** → **Done**.

### 2.4 Grant Project Creator on the organization (detailed steps)

Granting **Project Creator** at the **organization** level lets the service account create new projects under your org. Do the following in order:

1. **Open the IAM page**
   - In the left sidebar go to **IAM & Admin** → **IAM**  
   - Or open: [console.cloud.google.com/iam-admin/iam](https://console.cloud.google.com/iam-admin/iam)

2. **Switch from “Project” to “Organization”**
   - At the **top of the page** you’ll see a breadcrumb or dropdown that says the current **project** name (e.g. “BoltReceipt”).
   - Click that dropdown to open the **resource picker**.
   - In the left column, select **“Organization”** (not “Project” or “Folder”).
   - Click your **organization** (e.g. `receiptrecon.com`). The main table should now show **“Permission for [your org name]”** or similar. Confirm you’re on the org, not a project.

3. **Add the service account as a principal**
   - Click **“Grant Access”** (or **“+ Add”** / **“Add principal”**).
   - In **“New principals”**, paste the **full service account email**, e.g.  
     `clawhost-project-creator@boltreceipt.iam.gserviceaccount.com`  
     (Use the email from **IAM & Admin → Service accounts** in the project where you created the SA.)

4. **Assign the Project Creator role**
   - In **“Role”**, click the dropdown (or “Select a role”).
   - In the search box type **“Project Creator”** or **“Resource Manager”**.
   - Under **Resource Manager**, select **“Project Creator”**.
   - Do **not** choose “Project Creator” under a different product; only **Resource Manager → Project Creator** grants the right to create projects under the org.

5. **Save**
   - Click **Save**. The service account should now appear in the org IAM list with the role **Project Creator**.

6. **Verify**
   - In the same IAM list (for the organization), find your service account and confirm it has **Project Creator** (Resource Manager).

---

### 2.5 Grant billing account roles (Billing User, budget creation)

The service account must be able to **link projects to the billing account** (permission `billing.resourceAssociations.create`) and create budgets. Grant roles **on the billing account** (not on a project):

1. Go to **Billing** → [Billing](https://console.cloud.google.com/billing) → select your billing account.
2. Open **Manage account access** (or **Account management** → **Permissions** / **IAM**).
3. Click **Add members** (or **Grant access**).
4. **Principal:** paste the **service account email** (e.g. `clawhost-project-creator@your-project.iam.gserviceaccount.com`).
5. **Roles:** add **both**:
   - **Billing** → **Billing Account User** (grants `billing.resourceAssociations.create` so the SA can link projects to this billing account).
   - **Billing** → **Billing Account Costs Manager** or **Billing Account Administrator** (so the SA can create budgets; there is no "Budget Admin" role in the console).
6. Save.

If you see **403 PERMISSION_DENIED** with `billing.resourceAssociations.create` in logs, the principal making the request does not have **Billing Account User** on this billing account — add the SA here and wait a minute for IAM to propagate.

### 2.6 Confirm the service account gets Owner on new projects (or add org-level roles)

When the service account **creates** a new project via the API, it must be able to **enable APIs** and **create API keys** in that new project. That requires roles like **Service Usage Admin** and **API Keys Admin** (or **Owner**) **on the new project**. Google documents that the identity that creates a project becomes **Owner** of that project. So in the typical case you don't need to do anything extra. If your org behaves differently, use the fallback below.

---

#### 2.6.1 Verify / rely on "project creator = Owner" (recommended first)

**A. Where Google says the creator becomes Owner**

1. Open the official doc: [Creating and managing projects](https://cloud.google.com/resource-manager/docs/creating-managing-projects).
2. On that page, find the section that describes **who gets access** when a project is created. Google states that the **identity that creates the project** is made **Owner** of that project.
3. So: your ClawHost service account (with **Project Creator** on the org from step 2.4) will automatically get **Owner** on each new project it creates and can enable APIs and create API keys there.

**B. Navigation steps to verify in the console (after a project is created)**

Do this after you have at least one project created by the ClawHost service account (e.g. after a test subscription or a one-off create).

1. **Open Resource Manager**
   - In the left sidebar: **IAM & Admin** → **Manage resources**  
   - Or go to: [console.cloud.google.com/cloudresourcemanager](https://console.cloud.google.com/cloudresourcemanager)

2. **Switch to the right scope**
   - At the top, use the **project/organization** dropdown.
   - Select your **Organization** (e.g. `receiptrecon.com`) so you see all projects and folders under it.

3. **Find the new project**
   - In the list, find the project that was just created (e.g. name like `ClawHost sub xxxxxxxx` or project ID like `ch-<hex>`).
   - Click the **project name** (or the row) to open that project.

4. **Open IAM for that project**
   - With the project selected/opened, in the left sidebar go to **IAM & Admin** → **IAM**  
   - Or: [console.cloud.google.com/iam-admin/iam](https://console.cloud.google.com/iam-admin/iam) and ensure the **project** dropdown at the top shows the new project (not the org).

5. **Confirm the service account has Owner**
   - In the **IAM** table, look for the principal that is your ClawHost service account (e.g. `clawhost-project-creator@boltreceipt.iam.gserviceaccount.com`).
   - Check the **Role(s)** column for that principal. It should include **Owner**.
   - If you see **Owner** (or **Owner** plus other roles), the “project creator = Owner” behavior is in effect → no further steps needed for 2.6.

If the service account **does not** appear with **Owner** on the new project, use Option A (2.6.2) or Option B (2.6.3) below.

---

#### 2.6.2 Option A — Add org-level Service Usage Admin and API Keys Admin

If your console lets you grant these roles at the **organization** level, the service account will be able to enable APIs and create keys in any project under the org (including newly created ones).

1. **Open org IAM** (same as 2.4)
   - **IAM & Admin** → **IAM** → switch the resource picker to **Organization** → select your org (e.g. `receiptrecon.com`).

2. **Edit the existing principal** (your ClawHost service account)
   - In the list, find the principal that is your ClawHost service account (e.g. `clawhost-project-creator@...`).
   - Click the **pencil (Edit)** icon on that row.

3. **Add two more roles**
   - Click **"Add another role"**.
   - **First role:** search for **"Service Usage Admin"** (under **Service Usage**) → select it.
   - Click **"Add another role"** again.
   - **Second role:** search for **"API Keys Admin"** (under **API Keys**) → select it.
   - Click **Save**.

4. **Verify**
   - The service account row should now show: **Project Creator**, **Service Usage Admin**, **API Keys Admin** (plus any billing roles are on the billing account, not here).

If **API Keys Admin** (or Service Usage Admin) is **not available** when the resource is "Organization", your org may not support that role at org level. In that case use **Option B** (2.6.3).

**Practical approach (legacy):** Grant at **organization** level:

- **Project Creator** (already done).
- **Service Usage Admin** (organization level if your console allows it; otherwise the service account may need to be granted **Owner** or **Editor** on the **new** project via a **folder** or **organization** default. Google’s default is that the **creator** of a project is not automatically an owner. So you have two options:
  - **Option 1:** Use a **folder** under the org, grant the SA **Owner** on that folder, and create projects under that folder (would require a small code change to pass folder as parent).
  - **Option 2:** After creating the project, the backend uses the **same** credentials; for **new projects**, the Cloud Resource Manager API often leaves the creating identity with access. Verify in [Creating and managing projects](https://cloud.google.com/resource-manager/docs/creating-managing-projects): “When you create a project, you become the owner of that project.” So the **service account** that creates the project should get **Owner** on it. In that case you only need **Project Creator** at org, **Billing Account User** and **Billing Account Costs Manager** (or **Billing Account Administrator**) on the billing account, and the SA will have Owner on each new project and can enable APIs and create keys.

So minimal setup:

- **Organization:** Service account has **Project Creator**.
- **Billing account:** Service account has **Billing Account User** and **Billing Account Costs Manager** (or **Billing Account Administrator**).
- **New projects:** Created by this SA, so the SA is **Owner** of each new project and can enable Service Usage and create API keys.

---

#### 2.6.3 Option B — Use a folder and grant Owner on the folder

If the service account does **not** get Owner on newly created projects and org-level API Keys Admin / Service Usage Admin are not available, create a **folder**, grant the service account **Owner** on that folder, and create all ClawHost subscriber projects **under that folder**. This requires a **code change** so ClawHost uses the folder as parent instead of the organization.

1. **Create a folder under the org:** IAM & Admin → Manage resources → set picker to Organization → Create Folder (e.g. `ClawHost Subscriber Projects`).
2. **Grant the SA Owner on the folder:** Open the folder → Permissions / IAM → Grant Access → principal = SA email, Role = Owner → Save.
3. **Use folder as parent in ClawHost:** Env var `GCP_PARENT_FOLDER_ID` = folder ID; backend would use `folders/<id>` as parent (code change required).

#### 2.6.4 Summary

- **Default:** After 2.4 and 2.5, the SA that creates projects gets **Owner** on each new project → no extra steps for 2.6.
- **If not:** Add **Service Usage Admin** and **API Keys Admin** on the **organization** (2.6.2).
- **If org does not allow those roles:** Use a **folder** with **Owner** for the SA (2.6.3) and a backend change to use folder as parent.

---

### 2.7 Enable required APIs (in the project where the SA lives, or in the org)

Enable these so the SA can call them (they are enabled for the **project** or **org** the SA uses; new projects get APIs enabled by the backend via Service Usage API):

1. Go to [APIs & Services → Library](https://console.cloud.google.com/apis/library).
2. Enable:
   - **Cloud Resource Manager API**
   - **Service Usage API**
   - **Cloud Billing API**
   - **Cloud Billing Budget API** (Billing Budgets)
   - **API Keys API** (if not already on)
   - **Generative Language API** (for Gemini)

Enable them in the **project** that holds your service account (or at org level if your console allows). The backend will enable **Generative Language API** in each **new** project it creates; the others are used from the “admin” project or org.

### 2.8 Create and download the service account key

1. Go to **IAM & Admin** → **Service Accounts**.
2. Click the ClawHost service account (e.g. `clawhost-project-creator@...`).
3. Open **Keys** → **Add Key** → **Create new key** → **JSON**.
4. Download the JSON file. Keep it **secret**; never commit it to git.
5. You will put the **contents** of this JSON into Railway as the value of `GOOGLE_APPLICATION_CREDENTIALS` (see Step 4). Alternatively, some platforms let you mount a file; then use the path to that file.

---

## Step 3: Install new Python dependencies (Backend)

The one-project-per-subscription flow uses extra packages. They are already in `backend/requirements.txt`:

- `google-cloud-resource-manager`
- `google-cloud-billing`
- `google-cloud-billing-budgets`
- `google-api-python-client`

### 3.1 Local

```bash
cd backend
pip install -r requirements.txt
```

### 3.2 Railway

Railway builds from `requirements.txt` when you deploy. So:

1. Ensure the **Backend** and **Worker** services use the **same** repo and **Root Directory** = `backend`.
2. Push your latest code (with the updated `requirements.txt`).
3. Trigger a **redeploy** of both Backend and Worker so they pick up the new dependencies.

No extra step if you already deploy from the repo; a new deploy is enough.

---

## Step 4: Set environment variables (Backend and Worker)

Set these on **both** the **Backend** and **Worker** services in Railway (the webhook runs on the Backend; credentials are needed there; Worker may need them if you add other GCP tasks later; keeping them in sync avoids confusion).

### 4.1 In Railway

1. Open your **Backend** service → **Variables**.
2. Add or edit:

| Variable | Value | Required |
|----------|--------|----------|
| `GCP_PROJECT_PER_SUBSCRIPTION_ENABLED` | `true` | Yes |
| `GCP_ORGANIZATION_ID` | Your org ID (e.g. `123456789012`) | Yes |
| `GCP_BILLING_ACCOUNT_ID` | Billing account ID (e.g. `01ABC2D-3EF4G5-6789HI`) or `billingAccounts/01ABC2D-...` | Yes |
| `GCP_BUDGET_AMOUNT_USD` | `15` (or your desired monthly cap) | No (default 15) |
| `GOOGLE_APPLICATION_CREDENTIALS` | **JSON contents** of the service account key (see 4.2) | Yes (or use file path if your platform supports it) |

3. Repeat the same variables for the **Worker** service.

### 4.2 Providing the service account key on Railway

Railway does not support uploading a file easily. The Backend supports **inline JSON**: if `GOOGLE_APPLICATION_CREDENTIALS` is set to a string that **starts with `{`** (i.e. the raw JSON), the app writes it to a temp file at startup and sets the variable to that path so Google client libraries work.

**Steps:**

1. Open the service account JSON file you downloaded.
2. Minify it to **one line** (remove newlines and extra spaces). Examples:
   - **PowerShell:** `(Get-Content -Raw path\to\key.json) -replace '\s+', ' '`
   - **Node:** `JSON.stringify(require('./key.json'))`
   - Or copy the file contents and use any JSON minifier.
3. In Railway → Backend (and Worker) → **Variables**:
   - Name: `GOOGLE_APPLICATION_CREDENTIALS`
   - Value: paste the **entire one-line JSON string** (it must start with `{`).

The app will detect JSON and write it to a temp file on startup; no extra code needed.

**Option A — File path (if your platform supports it)**  
If you can mount the key as a file (e.g. a secret file or volume), set:

- `GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json`

### 4.3 Optional: fallback single project

If per-subscription project creation **fails** (e.g. quota, permissions), the backend falls back to creating the Gemini key in a **single** project. To support that fallback, keep:

- `GCP_PROJECT_ID` or `GOOGLE_CLOUD_PROJECT` = that project’s ID.

So you can set:

- `GCP_PROJECT_ID` = the project where your ClawHost service account lives (or any project where the SA has API Keys Admin). Used only when the per-subscription project flow is not used or fails.

---

## Step 5: Redeploy and verify

1. **Redeploy Backend and Worker** after changing variables (Railway often redeploys on variable change; if not, trigger a deploy).
2. **Check logs** (Backend and Worker) for errors on startup (e.g. missing env, import errors).
3. **Test:** Create a **new test subscription** (Stripe test mode):
   - Use a test card, complete checkout.
   - In Stripe Dashboard, confirm the subscription and that the webhook was sent.
   - In Backend logs, look for messages like:
     - “Created GCP project …”
     - “Enabled Generative Language API for project …”
     - “Linked project … to billing account …”
     - “Created budget … for project …”
     - “Created Gemini API key for subscription …”
4. In **GCP Console**:
   - **Resource Manager** → switch to your org → you should see a new project (e.g. `ch-<subscription-uuid-hex>`).
   - **Billing** → **Budgets** → a new budget for that project at $15 (or your `GCP_BUDGET_AMOUNT_USD`).
   - In that project: **APIs & Services** → **Enabled APIs** → Generative Language API and API Keys API enabled; **Credentials** → API keys → one new key.

---

## Step 6: Optional — budget cap / disable billing at limit

The backend creates a **budget** with a **100% threshold** (alert when spend reaches the budget). GCP Budgets are primarily for **alerts** (email, Pub/Sub). A true **spending cap** or “disable billing” depends on your billing product and region:

1. In **Billing** → **Budgets**, open the budget created for a subscriber project.
2. Check for options like **Set budget alert** vs **Set budget cap** or **Disable billing when budget is exceeded**.
3. If available, enable the cap or disable-billing behavior you want for the $15 limit.

---

## Troubleshooting

| Symptom | What to check |
|--------|----------------|
| “Permission denied” creating project | SA has **Project Creator** on the **organization** (not only on a project). |
| “Permission denied” enabling API or creating key | SA is **Owner** of the new project (creator usually is), or has **Service Usage Admin** and **API Keys Admin** (org/folder/project as applicable). |
| “Permission denied” linking billing | SA has **Billing Account User** on the **billing account**. Grant it under Billing → [your account] → Manage account access → Add members → SA email + role **Billing Account User**. If logs show `billing.resourceAssociations.create`, the SA is missing that role on this billing account. |
| “Permission denied” creating budget | SA has **Billing Account Costs Manager** or **Billing Account Administrator** on the **billing account**. |
| “Organization not found” or “Parent invalid” | `GCP_ORGANIZATION_ID` is the **numeric** org ID; no `organizations/` prefix. |
| “Billing account not found” | `GCP_BILLING_ACCOUNT_ID` is correct; use either `01ABC...` or `billingAccounts/01ABC...`. |
| Webhook creates subscription but no project | Backend logs for the webhook run; look for Python tracebacks from `create_project_and_setup`. Ensure `GCP_PROJECT_PER_SUBSCRIPTION_ENABLED=true` and both org and billing ID are set. |
| Migration fails | `DATABASE_URL` uses `postgresql+asyncpg://...`. Run migration with the same DB as the app. |

---

## Summary checklist

- [ ] Migration `006_add_subscription_gcp_project_id` applied (`alembic upgrade head`).
- [ ] GCP Organization ID and Billing Account ID noted.
- [ ] Service account created; granted **Project Creator** (org), **Billing Account User** and **Billing Account Costs Manager** or **Billing Account Administrator** (billing account).
- [ ] Required APIs enabled (Resource Manager, Service Usage, Cloud Billing, Billing Budgets, API Keys, Generative Language).
- [ ] Service account key JSON downloaded and stored securely.
- [ ] Backend and Worker env set: `GCP_PROJECT_PER_SUBSCRIPTION_ENABLED=true`, `GCP_ORGANIZATION_ID`, `GCP_BILLING_ACCOUNT_ID`, `GCP_BUDGET_AMOUNT_USD` (optional), `GOOGLE_APPLICATION_CREDENTIALS` (path or inline).
- [ ] Dependencies installed (redeploy from repo with updated `requirements.txt`).
- [ ] Test subscription created; new GCP project and budget visible; Gemini key created in that project.
