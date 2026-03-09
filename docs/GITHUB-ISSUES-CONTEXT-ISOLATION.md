# GitHub Issues - Project-Based Context Isolation

**Epic:** Implement project-based context isolation (matching cloud provider UX)

**Priority:** HIGH - Blocks further feature development

---

## Issue #1: Database Schema - Add project_id to deployments

**Title:** `[Backend] Add project_id column to deployments table for context isolation`

**Labels:** `backend`, `database`, `priority-high`, `phase-1`

**Description:**
```markdown
## Problem
Current deployment model lacks project-level isolation. User can switch to "Customer A" but still view "Customer B" resources.

## Solution
Add `project_id` column to deployments table to enforce project boundaries.

## Tasks
- [ ] Add `project_id VARCHAR(255)` column to deployments table
- [ ] Create migration script
- [ ] Migrate existing data:
  - `openluffy-*` deployments → `project_id = 'control-plane'`
  - Customer deployments → `project_id = {customer_id}`
- [ ] Make `project_id` NOT NULL after migration
- [ ] Add index: `CREATE INDEX idx_deployments_project_id ON deployments(project_id);`
- [ ] Test migration on dev database

## Acceptance Criteria
- [x] All deployments have valid project_id
- [x] Index created for performance
- [x] Migration tested and verified

## References
- Analysis: `openluffy-context-isolation-analysis.md`
```

---

## Issue #2: Backend API - Project-scoped endpoints

**Title:** `[Backend] Implement project-scoped API endpoints for context isolation`

**Labels:** `backend`, `api`, `priority-high`, `phase-1`

**Description:**
```markdown
## Problem
Current API endpoints don't enforce project boundaries. Need project-scoped endpoints.

## Solution
Create new API endpoints that filter resources by project_id and enforce access control.

## New Endpoints
```python
GET /api/v1/projects
# Returns list of projects user has access to

GET /api/v1/projects/{project_id}/applications
# Returns ONLY applications belonging to {project_id}

GET /api/v1/projects/{project_id}/applications/{deployment_id}
# Returns deployment details ONLY if deployment belongs to {project_id}
# Otherwise: 403 Forbidden

GET /api/v1/projects/{project_id}/applications/{deployment_id}/logs
GET /api/v1/projects/{project_id}/applications/{deployment_id}/events
GET /api/v1/projects/{project_id}/applications/{deployment_id}/resources
GET /api/v1/projects/{project_id}/applications/{deployment_id}/networking
# All detail endpoints scoped to project
```

## Tasks
- [ ] Create `ProjectService` class
- [ ] Implement `/projects` endpoint
- [ ] Implement `/projects/{id}/applications` endpoint
- [ ] Add project context validation middleware
- [ ] Return 403 if user accesses wrong project's resources
- [ ] Update existing detail endpoints to validate project context
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Update API documentation

## Acceptance Criteria
- [x] All endpoints filter by project_id
- [x] Cross-project access returns 403 Forbidden
- [x] Tests pass
- [x] API docs updated

## References
- Schema: Issue #1
- Analysis: `openluffy-context-isolation-analysis.md`
```

---

## Issue #3: Frontend - ProjectContext implementation

**Title:** `[Frontend] Replace CustomerContext with ProjectContext for true isolation`

**Labels:** `frontend`, `priority-high`, `phase-2`

**Description:**
```markdown
## Problem
CustomerContext is just a label, not a true context switch. Need ProjectContext that enforces isolation.

## Solution
Create ProjectContext that:
1. Manages selected project state
2. Redirects to project's applications list on switch
3. Blocks navigation to wrong project's resources

## Tasks
- [ ] Create `src/contexts/ProjectContext.jsx`
- [ ] Implement `ProjectProvider` component
- [ ] Add `selectedProject` state
- [ ] Add `selectProject(projectId)` function that redirects
- [ ] Replace CustomerContext with ProjectContext in App.jsx
- [ ] Update all components using CustomerContext
- [ ] Test context switching behavior
- [ ] Test isolation (cannot access wrong project)

## Code Structure
```jsx
// src/contexts/ProjectContext.jsx
export function ProjectProvider({ children }) {
  const [selectedProject, setSelectedProject] = useState('control-plane')
  const [projects, setProjects] = useState([])
  
  const selectProject = (projectId) => {
    setSelectedProject(projectId)
    navigate(`/projects/${projectId}/applications`) // Force redirect
  }
  
  return (
    <ProjectContext.Provider value={{ selectedProject, projects, selectProject }}>
      {children}
    </ProjectContext.Provider>
  )
}
```

## Acceptance Criteria
- [x] ProjectContext manages project state
- [x] Switching project redirects to project's app list
- [x] Cannot navigate to wrong project's resources
- [x] All components migrated from CustomerContext

## References
- Backend APIs: Issue #2
- Analysis: `openluffy-context-isolation-analysis.md`
```

---

## Issue #4: Frontend - Update routes for project-based navigation

**Title:** `[Frontend] Migrate routes from /customers/... to /projects/.../applications/...`

**Labels:** `frontend`, `priority-high`, `phase-2`

**Description:**
```markdown
## Problem
Current routes: `/customers/:customerId/:environment`  
This doesn't match project-based context model.

## Solution
New routes: `/projects/:projectId/applications/:deploymentId`

## Route Migration

**Old routes:**
```jsx
/customers/:customerId/:environment
```

**New routes:**
```jsx
/projects/:projectId/applications                      // List view
/projects/:projectId/applications/:deploymentId        // Detail view
```

**Example URLs:**
```
Control Plane:
  /projects/control-plane/applications
  /projects/control-plane/applications/openluffy-dev

Trucks Inc:
  /projects/trucks-inc/applications
  /projects/trucks-inc/applications/trucks-api-dev
```

## Tasks
- [ ] Update App.jsx routes
- [ ] Update ApplicationsTable navigation links
- [ ] Update CustomerApplicationDetail component to use project context
- [ ] Add redirect from old URLs to new URLs (backwards compatibility)
- [ ] Update all `<Link>` components
- [ ] Test navigation flows
- [ ] Test direct URL access (bookmarks)

## Acceptance Criteria
- [x] All routes use new `/projects/...` structure
- [x] Old URLs redirect to new structure
- [x] Navigation works correctly
- [x] Direct URL access works

## References
- ProjectContext: Issue #3
- Analysis: `openluffy-context-isolation-analysis.md`
```

---

## Issue #5: Frontend - Project selector UI component

**Title:** `[Frontend] Build project selector component with Control Plane vs Customer distinction`

**Labels:** `frontend`, `ui`, `priority-medium`, `phase-2`

**Description:**
```markdown
## Problem
Current "Customer" dropdown doesn't clearly distinguish platform infrastructure vs customer workloads.

## Solution
New "Project" selector with visual distinction:
- Control Plane (platform infrastructure)
- Customer Projects (customer workloads)

## Design

**Dropdown:**
```
┌─────────────────────────────┐
│ 🎛️  Control Plane          │ ← Blue accent
├─────────────────────────────┤
│ 🏢 Customer Projects        │
│   📦 Trucks Inc             │ ← Green accent
│   📦 Acme Corp              │
│   📦 Widget Co              │
└─────────────────────────────┘
```

**Navbar placement:**
```
[≡] OpenLuffy    [Project: Control Plane ▼] [Env: All ▼]
```

## Tasks
- [ ] Rename component: CustomerSelector → ProjectSelector
- [ ] Add project type distinction (control-plane vs customer)
- [ ] Add visual styling (blue for platform, green for customers)
- [ ] Add icons (🎛️ for control-plane, 📦 for customers)
- [ ] Update TopNavbar to use ProjectSelector
- [ ] Test dropdown behavior
- [ ] Test visual distinction
- [ ] Responsive design (mobile/tablet/desktop)

## Acceptance Criteria
- [x] Clear visual distinction between Control Plane and Customer Projects
- [x] Selecting project redirects to project's applications
- [x] Works on mobile/tablet/desktop
- [x] Matches design spec

## References
- ProjectContext: Issue #3
- Analysis: `openluffy-context-isolation-analysis.md`
```

---

## Issue #6: Frontend - Add breadcrumb navigation

**Title:** `[Frontend] Add breadcrumb navigation for project context awareness`

**Labels:** `frontend`, `ui`, `priority-medium`, `phase-2`

**Description:**
```markdown
## Problem
User doesn't always know which project context they're in.

## Solution
Add breadcrumb navigation showing: Project → Section → Resource

## Examples

**Control Plane:**
```
Control Plane → Applications → openluffy-dev
```

**Customer Project:**
```
Trucks Inc → Applications → trucks-api-dev
```

## Tasks
- [ ] Create Breadcrumb component
- [ ] Integrate with router (useLocation, useParams)
- [ ] Add to ApplicationsTable view
- [ ] Add to ApplicationDetail view
- [ ] Style to match design system
- [ ] Test navigation from breadcrumbs
- [ ] Responsive design

## Acceptance Criteria
- [x] Breadcrumbs show current context
- [x] Clickable breadcrumbs navigate correctly
- [x] Updates on route change
- [x] Works on mobile

## References
- Routes: Issue #4
- Analysis: `openluffy-context-isolation-analysis.md`
```

---

## Issue #7: Testing - Project isolation end-to-end tests

**Title:** `[Testing] E2E tests for project context isolation`

**Labels:** `testing`, `priority-high`, `phase-3`

**Description:**
```markdown
## Tests Required

### Backend Tests
- [ ] Test: Control Plane project shows only OpenLuffy deployments
- [ ] Test: Customer project shows only that customer's deployments
- [ ] Test: Cross-project access returns 403 Forbidden
- [ ] Test: Project list endpoint returns correct projects

### Frontend Tests
- [ ] Test: Selecting Control Plane shows only platform apps
- [ ] Test: Selecting Customer Project shows only customer apps
- [ ] Test: Switching project redirects to project's app list
- [ ] Test: Cannot navigate to wrong project's resources (blocked)
- [ ] Test: Breadcrumbs update correctly
- [ ] Test: Direct URL access works
- [ ] Test: Old URLs redirect to new structure

### Integration Tests
- [ ] Test: Full flow: Select project → View apps → View detail
- [ ] Test: Cross-project navigation attempt (should fail)
- [ ] Test: Project switch → context fully isolated

## Acceptance Criteria
- [x] All tests pass
- [x] Project isolation verified
- [x] No cross-project leaks
- [x] Test coverage > 80%

## References
- Backend: Issue #2
- Frontend: Issues #3, #4, #5, #6
```

---

## Issue #8: Documentation - Update for project-based model

**Title:** `[Docs] Update documentation for project-based context model`

**Labels:** `documentation`, `priority-medium`, `phase-4`

**Description:**
```markdown
## Updates Required

### User Documentation
- [ ] Update README with project concept
- [ ] Add "How to switch projects" guide
- [ ] Update screenshots showing new UI
- [ ] Explain Control Plane vs Customer Projects

### Developer Documentation
- [ ] Update API docs with project-scoped endpoints
- [ ] Document ProjectContext usage
- [ ] Update route structure docs
- [ ] Add migration guide (old to new)

### Architecture Documentation
- [ ] Document project isolation model
- [ ] Add database schema diagrams
- [ ] Document comparison to cloud providers
- [ ] Update ROADMAP.md

## Acceptance Criteria
- [x] All docs updated
- [x] Screenshots current
- [x] Migration guide complete
- [x] Architecture clearly documented

## References
- Analysis: `openluffy-context-isolation-analysis.md`
```

---

## Recommended Issue Creation Order

1. **Issue #1** (Database schema) - Foundation
2. **Issue #2** (Backend APIs) - Enforcement layer
3. **Issue #3** (ProjectContext) - Frontend state management
4. **Issue #4** (Routes) - URL structure
5. **Issue #5** (Project selector UI) - User interface
6. **Issue #6** (Breadcrumbs) - Context awareness
7. **Issue #7** (Testing) - Validation
8. **Issue #8** (Documentation) - Knowledge transfer

## GitHub Project Board Structure

**Columns:**
1. **Backlog** - Not started
2. **To Do** - Prioritized, ready to work
3. **In Progress** - Actively being worked on
4. **Review** - PR created, awaiting approval
5. **Testing** - Deployed to dev/preprod
6. **Done** - Merged to main, in production

**Milestones:**
- **v1.2 - Project Isolation** - All 8 issues complete
  - Target: 2026-03-15
  - Description: "Implement project-based context isolation matching cloud provider UX"

---

**Next Step:** Create these issues in GitHub and link them to the project board.
