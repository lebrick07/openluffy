# Luffy: The Engine (Not an Assistant)

## Vision

**"Remember Luffy is not the assistant he is the engine he is going to be king of the pirates."**

Luffy is NOT a chatbot. Luffy is NOT a helper. **Luffy is the autonomous DevOps engine that does the work.**

---

## Core Principles

### 1. Luffy Does What Zoro Does

Luffy should be able to execute the same workflows that we (humans) perform manually:
- Create customer infrastructure
- Set up CI/CD pipelines
- Deploy applications
- Troubleshoot and fix issues
- Approve and merge PRs
- Scale and restart services

**Example:** When working together, if I (Zoro) can run `kubectl restart deployment`, Luffy should be able to do the same via his tool system.

### 2. "Create Customer" → Full Automation

When user clicks "Create" and "New Customer" in the UI, Luffy should execute the ENTIRE onboarding flow we did manually:

**Manual Flow (What We Did):**
1. Created GitHub repo (acme-corp-api)
2. Initialized with Node.js/Python/Go template
3. Set up CI/CD pipeline (.github/workflows/)
4. Created ArgoCD Applications (dev, preprod, prod)
5. Deployed to all environments
6. Configured ingresses
7. Set up secrets

**Automated Flow (What Luffy Should Do):**
1. User fills form: Customer name, tech stack, repo URL (optional)
2. Luffy creates:
   - GitHub repository (via GitHub API)
   - CI/CD pipeline from template
   - ArgoCD Applications for all envs
   - K8s namespaces
   - Helm charts
   - Ingresses with proper hostnames
3. Triggers initial deployment
4. Reports status back to user

**Goal:** 5-minute customer onboarding, zero manual work.

### 3. PR Approval from UI

PRs should not require leaving the OpenLuffy UI. The UI should show:
- **Pending PRs** (list with status, CI checks)
- **Diff view** (inline code changes)
- **Approve button** (triggers GitHub API approval + merge)
- **Deployment status** (after merge, track ArgoCD sync)

**Flow:**
1. Developer creates PR via GitHub (or UI in future)
2. CI runs (security, quality, tests)
3. Engineer sees PR in OpenLuffy UI "Pending Approvals" section
4. Reviews diff in UI
5. Clicks "Approve & Merge"
6. Luffy merges PR via GitHub API
7. Pipeline runs
8. Luffy reports deployment status

**Luffy's Role:** Orchestrate the approval and track deployment.

---

## Luffy's Capabilities (Current + Planned)

### ✅ Current Capabilities

**Read Operations:**
- List pods, deployments, ingresses, namespaces
- Get logs from pods
- Check deployment status
- Analyze errors (AI Triage Engine)
- List recent events

**Write Operations:**
- Restart deployments
- Scale deployments
- Delete pods (force restart)

### 🚧 Needed Capabilities

**Customer Management:**
- Create GitHub repo (GitHub API)
- Generate CI/CD pipeline from template
- Create ArgoCD Applications
- Set up namespaces, secrets, ingresses
- Configure DNS/hostnames

**PR Management:**
- List pending PRs (GitHub API)
- Fetch PR diff
- Approve PR (GitHub API)
- Merge PR (GitHub API)
- Track deployment after merge

**Pipeline Management:**
- Trigger GitHub Actions workflow
- Monitor workflow status
- Cancel/re-run workflows
- View workflow logs

**ArgoCD Management:**
- Sync applications
- Rollback applications
- View sync status and health
- Compare live vs desired state

**Monitoring:**
- Fetch metrics (Prometheus/K8s metrics API)
- Alert on issues
- Generate reports

---

## Architecture Changes Needed

### 1. GitHub Integration

**Tool:** `github_client.py`

```python
async def create_repo(org: str, name: str, template: str) -> Dict:
    """Create GitHub repo from template"""
    
async def list_prs(repo: str, state: str = "open") -> List[Dict]:
    """List PRs in repo"""
    
async def get_pr_diff(repo: str, pr_number: int) -> Dict:
    """Get PR diff and files changed"""
    
async def approve_pr(repo: str, pr_number: int) -> Dict:
    """Approve a PR"""
    
async def merge_pr(repo: str, pr_number: int, method: str = "squash") -> Dict:
    """Merge a PR"""
    
async def trigger_workflow(repo: str, workflow: str, inputs: Dict) -> Dict:
    """Trigger GitHub Actions workflow"""
```

### 2. Customer Onboarding Flow

**Tool:** `customer_onboarding.py`

```python
async def create_customer(
    name: str,
    tech_stack: str,
    repo_url: Optional[str] = None
) -> Dict:
    """
    Full customer onboarding automation:
    1. Create GitHub repo (or use existing)
    2. Initialize with template
    3. Create CI/CD pipeline
    4. Create ArgoCD apps
    5. Create namespaces
    6. Deploy to dev
    7. Return status
    """
```

### 3. PR Approval UI Component

**Component:** `PendingPRs.jsx`

```jsx
function PendingPRs() {
  // Fetch PRs from backend
  // Display list with CI status
  // Show diff on click
  // Approve + merge button
  // Track deployment after merge
}
```

### 4. ArgoCD Integration

**Tool:** `argocd_client.py`

```python
async def sync_application(name: str, namespace: str = "argocd") -> Dict:
    """Sync ArgoCD application"""
    
async def rollback_application(name: str, revision: int) -> Dict:
    """Rollback to previous revision"""
    
async def get_app_status(name: str) -> Dict:
    """Get application sync/health status"""
```

---

## RBAC Requirements

Luffy needs **BROAD** permissions to be operational:

### Kubernetes:
- **Create/Update/Delete:** Namespaces, Deployments, Services, Ingresses, Secrets, ConfigMaps
- **Read:** All resources (pods, nodes, events, etc.)
- **Execute:** Logs, exec into pods, port-forward
- **ArgoCD:** Full access to Applications

### GitHub:
- **Repo:** Create, manage repos
- **PR:** List, create, approve, merge PRs
- **Workflows:** Trigger, view, cancel workflows
- **Secrets:** Manage repo secrets

### ArgoCD:
- **Applications:** Create, sync, delete, rollback
- **Projects:** View, create
- **Repositories:** Manage repo connections

---

## Security Considerations

**With great power comes great responsibility:**

1. **Audit Logging:** Log every action Luffy takes
2. **Approval Gates:** Destructive actions require confirmation
3. **Rate Limiting:** Prevent runaway automation
4. **User Context:** Track who initiated each action
5. **Rollback Capability:** Every change must be revertible

**Safety Mechanisms:**
- `--dry-run` mode for testing
- Confirmation prompts for destructive ops
- Automatic backups before changes
- Health checks after operations

---

## Roadmap

### Phase 1: Operational Capabilities ✅ (Current PR)
- ✅ Expanded RBAC (create/update/delete)
- ✅ Restart/scale/delete tools
- ✅ List ingresses, namespaces

### Phase 2: Customer Onboarding 🚧 (Next)
- GitHub API integration
- Template-based repo creation
- ArgoCD application automation
- "Create Customer" UI flow

### Phase 3: PR Management 🚧
- PR list/diff/approve in UI
- GitHub API integration
- Deployment tracking after merge

### Phase 4: Full Autonomy 🔮
- Auto-healing (detect and fix issues)
- Proactive scaling
- Cost optimization
- Security scanning and remediation

---

## The End Goal

**"Luffy is going to be king of the pirates."**

A DevOps engineer should be able to:
1. Click "Create Customer" → Infrastructure provisioned in 5 minutes
2. Review PRs in OpenLuffy UI → Approve and deploy without leaving
3. Ask Luffy "Deploy customer X to production" → Done
4. Say "Customer Y is slow, investigate" → Luffy troubleshoots and reports
5. Trust Luffy to auto-heal common issues while they sleep

**Luffy is not a chatbot. Luffy is the engine. Luffy does the work.**

---

**This is how one DevOps engineer manages 5-10 customers at scale.**
