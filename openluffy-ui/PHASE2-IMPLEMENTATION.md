# Phase 2: Frontend Project Isolation - Implementation Plan

**Status:** IN PROGRESS  
**Branch:** feature/project-isolation-frontend

---

## Phase 2.0: Context Layer ✅ (This Commit)

- [x] Create `ProjectContext.jsx` (replaces CustomerContext)
- [x] Uses new `/api/v1/projects` endpoint
- [x] Manages project selection state
- [x] Auto-navigates to `/projects/{id}/applications` on project switch

---

## Phase 2.1: UI Changes (Next Commits)

### Remove Navbar Dropdowns
- [ ] Remove customer dropdown from TopNavbar
- [ ] Remove environment dropdown from TopNavbar  
- [ ] Keep only: Logo | Search | Notifications | Profile

### Update Sidebar
- [ ] Add project switcher section at top
- [ ] Show "🎛️ Control Plane" with expand/collapse
- [ ] Show "📦 Customer Projects" list
- [ ] Highlight active project
- [ ] Views (Applications, Pipelines, etc.) shown under active project

### Update Routes
- [ ] Change `/customers/:id/:env` → `/projects/:projectId/applications/:deploymentId`
- [ ] Update App.jsx routing structure
- [ ] Add redirect for old URLs

---

## Phase 2.2: API Integration (After UI)

### ApplicationsTable
- [ ] Use `/api/v1/projects/{projectId}/applications` instead of `/api/deployments`
- [ ] Remove client-side filtering (server handles it)
- [ ] Add environment filter LOCAL to table (not global navbar)

### ApplicationDetail
- [ ] Use `/api/v1/projects/{projectId}/applications/{deploymentId}`
- [ ] Validate project ownership
- [ ] Handle 403 errors (cross-project access)

---

## Phase 2.3: Migration (Final)

- [ ] Replace all `useCustomer()` with `useProject()`
- [ ] Update all components importing CustomerContext
- [ ] Remove CustomerContext.jsx file
- [ ] Test cross-project access blocks (should 403)
- [ ] Test navigation flows

---

## Testing Checklist

- [ ] Control Plane shows only openluffy-{env} deployments
- [ ] Customer projects show only their deployments
- [ ] Cannot access wrong project's resources (403)
- [ ] Sidebar navigation works (expand/collapse)
- [ ] Routes work: `/projects/control-plane/applications`
- [ ] Routes work: `/projects/trucks-inc/applications/trucks-api-dev`
- [ ] Mobile responsive (sidebar collapses to hamburger)

---

## References

- **Backend API:** `backend/projects_api.py`
- **Design Doc:** `docs/SIDEBAR-NAVIGATION.md`
- **Context Isolation:** `docs/CONTEXT-ISOLATION.md`

---

**Estimated Completion:** 3-4 commits total
