# OpenLuffy Context Isolation - Cloud Provider Analysis

**Problem Statement:**
Current "Customer" dropdown doesn't enforce context isolation. User can switch to "Trucks Inc" but still view "Openluffy" platform workloads. This violates fundamental multi-tenancy principles.

**Date:** 2026-03-09

---

## How Cloud Providers Handle Context Switching

### AWS Console

**Context Hierarchy:**
1. **Account Switcher** (top-right corner)
   - Organization → Member Accounts
   - Switching account = COMPLETE resource isolation
   - Different set of EC2 instances, S3 buckets, everything

2. **Region Selector** (top-right)
   - us-east-1, eu-west-1, etc.
   - Regional resources (EC2, RDS)
   - Global resources (IAM, S3) visible across regions

3. **Service Navigation** (left sidebar)
   - EC2, S3, RDS, Lambda, etc.
   - Within the selected Account + Region context

**Key Principle:**
- **Switching account = Different resources**
- No way to view Account A resources while in Account B context
- Account is the PRIMARY isolation boundary

**Example:**
```
Account: Production-AWS (selected)
Region: us-east-1
Service: EC2

Resources shown: ONLY Production-AWS EC2 instances in us-east-1
```

---

### Google Cloud Platform (GCP)

**Context Hierarchy:**
1. **Project Selector** (top-left dropdown)
   - Organization → Folders → Projects
   - **PROJECT is the primary isolation boundary**
   - Switching project = COMPLETE resource view change

2. **Service Menu** (hamburger icon)
   - Compute Engine, Cloud Storage, Cloud SQL, etc.
   - Scoped to selected project

3. **Resource Breadcrumbs**
   - Project → Service → Resource
   - Always visible, always in context

**Key Principle:**
- **Project is the isolation unit**
- Resources belong to ONE project
- No cross-project resource viewing (unless multi-project view explicitly enabled)

**Example:**
```
Project: trucks-inc-prod (selected)
Service: Compute Engine → VM Instances

Resources shown: ONLY trucks-inc-prod VMs
```

**Cannot see:** acme-corp-prod VMs while trucks-inc-prod is selected

---

### Azure Portal

**Context Hierarchy:**
1. **Directory/Tenant Switcher** (top-right)
   - Organization-level boundary
   
2. **Subscription Selector** (top filter bar)
   - Subscription is the billing + isolation boundary
   - Switching subscription = different resources

3. **Resource Groups** (organizational containers within subscriptions)
   - Logical grouping of resources
   - All resources MUST belong to a resource group

4. **Service Navigation** (left sidebar)
   - Virtual Machines, Storage, Databases, etc.
   - Filtered by selected subscription(s)

**Key Principle:**
- **Subscription is primary isolation**
- Can enable "All Subscriptions" view (advanced)
- Default: one subscription context at a time

**Example:**
```
Subscription: Production-Subscription (selected)
Resource Group: web-tier
Service: Virtual Machines

Resources shown: ONLY Production-Subscription VMs
```

---

### Oracle Cloud Infrastructure (OCI)

**Context Hierarchy:**
1. **Tenancy** (top-level, rarely switched)
   - Root container for all resources

2. **Compartment Selector** (top dropdown)
   - Hierarchical structure (like folders)
   - Compartments provide isolation + RBAC boundaries
   - **Switching compartment = different resources**

3. **Region Selector** (top-right)
   - Regional resource scope

4. **Service Navigation** (hamburger menu)
   - Compute, Storage, Networking, etc.
   - Scoped to Compartment + Region

**Key Principle:**
- **Compartment is the isolation boundary**
- Resources belong to ONE compartment
- Hierarchical: Parent compartments can view child compartments (with permission)

**Example:**
```
Compartment: trucks-inc-production (selected)
Region: us-ashburn-1
Service: Compute → Instances

Resources shown: ONLY trucks-inc-production instances
```

---

## Common Patterns Across All Providers

### 1. Primary Isolation Boundary
- **AWS:** Account
- **GCP:** Project
- **Azure:** Subscription
- **OCI:** Compartment

**Universal Rule:** Switching context = DIFFERENT resources.

### 2. Context Selector Placement
- **Top-left or top-right** (high visibility)
- **Always visible** (persistent across navigation)
- **Clear labeling** (no ambiguity about current context)

### 3. Breadcrumb / Context Awareness
- User always knows: "Which account/project/subscription am I in?"
- Visual indicators (color coding, icons, breadcrumbs)
- Confirmation prompts when switching to production contexts

### 4. No Cross-Context Resource Mixing
- **You CANNOT view Account A resources while in Account B**
- Exception: Explicit "All Accounts" / "All Projects" views (advanced use case)
- Default behavior: strict isolation

### 5. Navigation Flow
```
1. Select Context (Account/Project/Subscription)
   ↓
2. View Resources in that Context
   ↓
3. Drill down to Resource Detail
   ↓
4. Actions are scoped to Context
```

**NOT:**
```
❌ Select Context A → View Context B resources (BROKEN)
```

---

## OpenLuffy Current State (BROKEN)

**What we have:**
```
Customer Dropdown: "Trucks Inc"
Applications Table: Shows ALL deployments (Openluffy, customer apps, everything)
Detail Page: /customers/Openluffy/dev (platform workload visible in customer context)
```

**The problem:**
- "Customer" dropdown is just a filter label, not a true context switch
- Resources are NOT isolated by customer
- User can navigate to ANY deployment regardless of selected customer
- Detail page URL: `/customers/:customerId/:environment` expects customer-specific resources
  - But Openluffy is platform infrastructure, not a customer

---

## Proposed Fix: Project-Based Context Isolation

### 1. Rename "Customer" → "Project"

**Why "Project"?**
- More universal (matches GCP terminology)
- Aligns with industry standards
- Clearer than "Customer" (which implies billing entity, not resource scope)

### 2. Define Project Types

**Control Plane Project:**
- ID: `control-plane` (special/reserved)
- Contains: OpenLuffy platform infrastructure
  - `openluffy-dev`, `openluffy-preprod`, `openluffy-prod` deployments
  - ArgoCD, Prometheus, Grafana, etc.
- Audience: Platform operators (you, DevOps team)

**Customer Projects:**
- ID: `trucks-inc`, `acme-corp`, etc.
- Contains: ONLY that customer's applications
  - `trucks-api-dev`, `trucks-web-preprod`, etc.
- Audience: Customer developers/operators (or platform team managing on their behalf)

### 3. Enforce Context Isolation in Backend

**API Endpoints:**
```python
GET /api/v1/projects
# Returns: List of projects user has access to

GET /api/v1/projects/{project_id}/deployments
# Returns: ONLY deployments belonging to {project_id}

GET /api/v1/projects/{project_id}/deployments/{deployment_id}
# Returns: Deployment details ONLY if deployment belongs to {project_id}
# Otherwise: 404 Not Found (or 403 Forbidden)
```

**Database Schema:**
```sql
-- Add project_id column to deployments table
ALTER TABLE deployments ADD COLUMN project_id VARCHAR(255) NOT NULL;

-- Index for fast filtering
CREATE INDEX idx_deployments_project_id ON deployments(project_id);

-- Existing deployments: assign to control-plane
UPDATE deployments SET project_id = 'control-plane' WHERE customer_id LIKE 'openluffy%';
UPDATE deployments SET project_id = customer_id WHERE customer_id NOT LIKE 'openluffy%';
```

### 4. Update Frontend Context Logic

**New Context Provider:**
```jsx
// src/contexts/ProjectContext.jsx
export function ProjectProvider({ children }) {
  const [selectedProject, setSelectedProject] = useState('control-plane')
  const [projects, setProjects] = useState([])
  
  // When project changes, redirect to project's applications list
  const selectProject = (projectId) => {
    setSelectedProject(projectId)
    navigate(`/projects/${projectId}/applications`) // Force context switch
  }
  
  return (
    <ProjectContext.Provider value={{ selectedProject, projects, selectProject }}>
      {children}
    </ProjectContext.Provider>
  )
}
```

**Updated Routes:**
```jsx
// Old (broken):
/customers/:customerId/:environment

// New (correct):
/projects/:projectId/applications
/projects/:projectId/applications/:deploymentId
```

**Example URLs:**
```
Control Plane:
  /projects/control-plane/applications
  /projects/control-plane/applications/openluffy-dev

Trucks Inc:
  /projects/trucks-inc/applications
  /projects/trucks-inc/applications/trucks-api-dev
  
Acme Corp:
  /projects/acme-corp/applications
  /projects/acme-corp/applications/acme-web-prod
```

### 5. Navigation Flow (Fixed)

**Scenario 1: User selects "Control Plane"**
```
1. Click Project Dropdown → "Control Plane"
2. Redirects to: /projects/control-plane/applications
3. Applications shown: openluffy-dev, openluffy-preprod, openluffy-prod
4. Click "openluffy-dev" → /projects/control-plane/applications/openluffy-dev
5. Detail page shows: OpenLuffy dev deployment (CORRECT)
```

**Scenario 2: User selects "Trucks Inc"**
```
1. Click Project Dropdown → "Trucks Inc"
2. Redirects to: /projects/trucks-inc/applications
3. Applications shown: trucks-api-dev, trucks-web-preprod, trucks-api-prod
4. Click "trucks-api-dev" → /projects/trucks-inc/applications/trucks-api-dev
5. Detail page shows: Trucks API dev deployment (CORRECT)
```

**Scenario 3: User tries to access wrong project resource (BLOCKED)**
```
1. Project Dropdown: "Trucks Inc" selected
2. User navigates to: /projects/trucks-inc/applications/openluffy-dev
3. Backend checks: Does "openluffy-dev" belong to "trucks-inc"?
4. Answer: NO (belongs to "control-plane")
5. Response: 403 Forbidden or redirect to /projects/trucks-inc/applications
6. User cannot access OpenLuffy resources while in Trucks Inc context
```

### 6. Project Selector UI Component

**Design (Top Navbar):**
```
┌──────────────────────────────────────────────────────────────┐
│  [≡] OpenLuffy    [Project: Control Plane ▼] [Env: All ▼]   │
│                                                 [🔔] [👤 Admin]│
└──────────────────────────────────────────────────────────────┘
```

**Project Dropdown:**
```
┌─────────────────────────────┐
│ 🎛️  Control Plane          │ ← Platform infrastructure
├─────────────────────────────┤
│ 🏢 Customer Projects        │
│   📦 Trucks Inc             │
│   📦 Acme Corp              │
│   📦 Widget Co              │
└─────────────────────────────┘
```

**Visual Distinction:**
- Control Plane: Blue accent (platform)
- Customer Projects: Green accent (customer workloads)
- Active project: Highlighted background

### 7. Breadcrumb Navigation

**Always show context:**
```
Control Plane → Applications → openluffy-dev

Trucks Inc → Applications → trucks-api-dev
```

---

## Implementation Checklist

### Backend (Phase 1)
- [ ] Add `project_id` column to deployments table
- [ ] Migrate existing data:
  - OpenLuffy deployments → `control-plane`
  - Customer deployments → `{customer_id}`
- [ ] Update API endpoints to filter by `project_id`
- [ ] Add project context validation (403 if accessing wrong project)
- [ ] Create `/api/v1/projects` endpoint

### Frontend (Phase 2)
- [ ] Rename CustomerContext → ProjectContext
- [ ] Update project selector component
- [ ] Change routes: `/customers/...` → `/projects/.../applications/...`
- [ ] Add redirect on project switch
- [ ] Add breadcrumb navigation
- [ ] Visual distinction (Control Plane vs Customer Projects)

### Testing (Phase 3)
- [ ] Test: Control Plane shows only OpenLuffy deployments
- [ ] Test: Customer Project shows only that customer's deployments
- [ ] Test: Cannot access wrong project's resources (403)
- [ ] Test: Project switch redirects correctly
- [ ] Test: Breadcrumbs update on navigation

### Documentation (Phase 4)
- [ ] Update README with project context explanation
- [ ] Update API docs with project-scoped endpoints
- [ ] Add user guide: "How to switch projects"

---

## Success Criteria

✅ **Project isolation working when:**

1. Selecting "Control Plane" → Only OpenLuffy deployments visible
2. Selecting "Trucks Inc" → Only Trucks Inc deployments visible
3. Cannot view Trucks Inc resources while in Control Plane context (and vice versa)
4. Detail page URL includes project context: `/projects/{project}/applications/{deployment}`
5. Backend enforces project boundaries (403 on cross-project access)
6. User always knows which project context they're in (breadcrumbs, selector)

✅ **Matches cloud provider UX:**
- GCP: Project selector behavior
- AWS: Account switcher behavior
- Clear, unambiguous context isolation

---

## Migration Plan

### Step 1: Database Migration (Non-breaking)
```sql
-- Add column (allows NULL initially)
ALTER TABLE deployments ADD COLUMN project_id VARCHAR(255);

-- Migrate data
UPDATE deployments 
SET project_id = CASE 
  WHEN customer_id LIKE 'openluffy%' THEN 'control-plane'
  ELSE customer_id
END;

-- Make NOT NULL after migration
ALTER TABLE deployments ALTER COLUMN project_id SET NOT NULL;
```

### Step 2: Backend API (Gradual)
- Add new `/api/v1/projects/...` endpoints
- Keep old `/api/v1/deployments/...` endpoints working (deprecated)
- Frontend switches to new endpoints
- Remove old endpoints after frontend migration complete

### Step 3: Frontend (Feature Flag)
- Implement ProjectContext alongside CustomerContext
- Feature flag: `USE_PROJECT_ISOLATION` (default: false)
- Test thoroughly in dev/preprod
- Enable in production when validated

### Step 4: Cleanup
- Remove CustomerContext
- Remove old routes
- Update documentation
- Announce to users (if external customers)

---

## Comparison: Before vs After

### Before (BROKEN)
```
User selects: "Trucks Inc"
URL: /customers/Openluffy/dev
Applications Table: Shows ALL deployments (mixed contexts)
Result: CONFUSING, BROKEN
```

### After (CORRECT)
```
User selects: "Trucks Inc"
URL: /projects/trucks-inc/applications
Applications Table: Shows ONLY Trucks Inc deployments
Trying to access /projects/trucks-inc/applications/openluffy-dev → 403 Forbidden
Result: CLEAR, ISOLATED, CORRECT
```

---

## References

- AWS Account Switcher: https://docs.aws.amazon.com/awsconsolehelpdocs/latest/gsg/getting-started.html#account-switcher
- GCP Project Selector: https://cloud.google.com/resource-manager/docs/creating-managing-projects
- Azure Subscriptions: https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-setup-guide/organize-resources
- OCI Compartments: https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingcompartments.htm

---

**Last Updated:** 2026-03-09  
**Status:** Analysis complete, implementation pending
