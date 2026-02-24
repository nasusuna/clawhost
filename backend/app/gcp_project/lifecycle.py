"""Create a GCP project per subscription: project, enable API, link billing, create budget. All sync for use in asyncio.to_thread."""
import logging
import re
import time
import uuid

logger = logging.getLogger(__name__)

# Project ID: 6–30 chars, lowercase letters, digits, hyphens; must start with a letter. Globally unique.
_PROJECT_ID_PREFIX = "ch-"
_PROJECT_ID_MAX_LEN = 30


def _make_project_id(subscription_id: uuid.UUID) -> str:
    """Generate a valid GCP project ID from subscription ID (unique, starts with letter)."""
    raw = f"{_PROJECT_ID_PREFIX}{subscription_id.hex}"[: _PROJECT_ID_MAX_LEN]
    return re.sub(r"[^a-z0-9-]", "", raw.lower()) or f"{_PROJECT_ID_PREFIX}{subscription_id.hex[:12]}"


def _norm_billing_account_id(billing_account_id: str) -> str:
    """Return billing account resource name: billingAccounts/ID."""
    s = (billing_account_id or "").strip()
    if not s:
        return ""
    if s.startswith("billingAccounts/"):
        return s
    return f"billingAccounts/{s}"


# --- Resource Manager (create project) ---
try:
    from google.cloud import resourcemanager_v3
except ImportError:
    resourcemanager_v3 = None


def create_project(organization_id: str, project_id: str, display_name: str) -> str:
    """Create a GCP project under the organization. Returns project_id. Sync."""
    if not resourcemanager_v3:
        raise RuntimeError("google-cloud-resource-manager is not installed; pip install google-cloud-resource-manager")
    parent = f"organizations/{organization_id.strip()}"
    client = resourcemanager_v3.ProjectsClient()
    project = resourcemanager_v3.Project(
        project_id=project_id,
        display_name=display_name[:30] if len(display_name) > 30 else display_name,
        parent=parent,
    )
    request = resourcemanager_v3.CreateProjectRequest(project=project)
    operation = client.create_project(request=request)
    result = operation.result()
    out_id = result.project_id or project_id
    logger.info("Created GCP project %s", out_id)
    return out_id


# --- Service Usage (enable Generative Language API) ---
def _enable_generative_language_api(project_id: str) -> None:
    """Enable generativelanguage.googleapis.com for the project. Sync."""
    try:
        from google.auth import default
        from googleapiclient import discovery
        from googleapiclient.errors import HttpError
    except ImportError as e:
        raise RuntimeError(
            "google-api-python-client and google-auth are required for enabling APIs; "
            "pip install google-api-python-client google-auth"
        ) from e

    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    service = discovery.build("serviceusage", "v1", credentials=credentials, cache_discovery=False)
    name = f"projects/{project_id}/services/generativelanguage.googleapis.com"
    try:
        service.services().enable(name=name).execute()
        logger.info("Enabled Generative Language API for project %s", project_id)
    except HttpError as e:
        if e.resp.status == 409 and "already enabled" in (e.content or b"").decode("utf-8", errors="ignore").lower():
            logger.info("Generative Language API already enabled for project %s", project_id)
            return
        raise


# --- Cloud Billing (link project to billing account) ---
try:
    from google.cloud import billing_v1
except ImportError:
    billing_v1 = None


def link_billing_account(project_id: str, billing_account_name: str) -> None:
    """Link the project to the billing account. Sync. Prefer REST API for clearer errors."""
    body = {"billingAccountName": billing_account_name}

    # Try REST API first (often gives clearer 400 error messages than gRPC).
    # REST name must be projects/{projectId} (no /billingInfo); pattern ^projects/[^/]+$
    try:
        from google.auth import default
        from googleapiclient import discovery
        from googleapiclient.errors import HttpError
    except ImportError:
        pass
    else:
        try:
            credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
            service = discovery.build("cloudbilling", "v1", credentials=credentials, cache_discovery=False)
            name = f"projects/{project_id}"  # REST expects projects/{id} only
            logger.info("Linking project %s to billing account %s", project_id, billing_account_name)
            service.projects().updateBillingInfo(name=name, body=body).execute()
            logger.info("Linked project %s to billing account %s", project_id, billing_account_name)
            return
        except HttpError as e:
            err_content = (e.content or b"").decode("utf-8", errors="replace")
            logger.warning("Cloud Billing REST updateBillingInfo failed: %s %s", e.resp.status, err_content[:500])
            if e.resp.status != 400:
                raise
            # Re-raise with REST error body so it's visible (often explains invalid argument).
            raise RuntimeError(
                f"Failed to link billing: {e.resp.status} {err_content[:300]}"
            ) from e


# --- Billing Budgets (create $15 budget for project) ---
try:
    from google.cloud.billing_budgets_v1 import BudgetServiceClient
    from google.cloud.billing_budgets_v1.types import Budget, BudgetAmount, Filter as BudgetFilter
    from google.cloud.billing_budgets_v1.types import CalendarPeriod, ThresholdRule
    from google.type import money_pb2
except ImportError:
    BudgetServiceClient = None
    Budget = BudgetAmount = BudgetFilter = CalendarPeriod = ThresholdRule = money_pb2 = None


def create_budget_for_project(
    billing_account_name: str,
    project_id: str,
    amount_usd: float = 15.0,
    display_name: str | None = None,
) -> None:
    """Create a monthly budget for the project (alerts at 100%). Sync. No-op if google-cloud-billing-budgets not installed."""
    if BudgetServiceClient is None or Budget is None:
        logger.warning(
            "Skipping budget creation: google-cloud-billing-budgets not installed. "
            "Add to requirements.txt and redeploy to create budgets. pip install google-cloud-billing-budgets"
        )
        return
    # specified_amount: Money with units (int) and nanos (int for fractional). $15 = 15 units, 0 nanos.
    units = int(amount_usd)
    nanos = int((amount_usd - units) * 1_000_000_000)
    specified = money_pb2.Money(currency_code="USD", units=units, nanos=nanos)
    amount = BudgetAmount(specified_amount=specified)
    budget_filter = BudgetFilter(
        projects=[f"projects/{project_id}"],
        calendar_period=CalendarPeriod.MONTH,
    )
    display = display_name or f"ClawHost ${amount_usd:.0f} cap"
    budget = Budget(
        display_name=display[:60],
        budget_filter=budget_filter,
        amount=amount,
        threshold_rules=[ThresholdRule(threshold_percent=1.0)],  # alert at 100%
    )
    client = BudgetServiceClient()
    client.create_budget(parent=billing_account_name, budget=budget)
    logger.info("Created budget $%s for project %s", amount_usd, project_id)


def create_project_and_setup(
    organization_id: str,
    billing_account_id: str,
    subscription_id: uuid.UUID,
    amount_usd: float = 15.0,
) -> str | None:
    """
    Create a GCP project for the subscription, enable Generative Language API,
    link billing, and create a monthly budget. Returns project_id or None on failure. Sync.
    """
    project_id = _make_project_id(subscription_id)
    display_name = f"ClawHost sub {subscription_id.hex[:8]}"
    billing_name = _norm_billing_account_id(billing_account_id)
    if not organization_id or not billing_name:
        logger.warning("GCP project creation skipped: missing organization_id or billing_account_id")
        return None

    try:
        create_project(organization_id, project_id, display_name)
        _enable_generative_language_api(project_id)
        # New projects need time to propagate before Billing API accepts the link; otherwise 400 Invalid Argument.
        logger.info("Waiting 10s for project %s to propagate before linking billing", project_id)
        time.sleep(10)
        link_billing_account(project_id, billing_name)
        create_budget_for_project(billing_name, project_id, amount_usd=amount_usd, display_name=display_name)
        return project_id
    except Exception as e:
        logger.warning("Failed to create/setup GCP project for subscription %s: %s", subscription_id, e, exc_info=True)
        return None
