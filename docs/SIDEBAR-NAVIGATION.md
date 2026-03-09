# OpenLuffy Navigation Model - GitHub-Style Sidebar

**Date:** 2026-03-09

**Problem:** Current design still has context dropdowns in navbar. Wrong pattern.

**Solution:** Each project is its own "realm" — navigate TO it, not filter it.

---

## GitHub Navigation Model (Reference)

### How GitHub Works

When you go to **github.com/lebrick07/openluffy**:

```
Sidebar (left):
  📂 lebrick07
    📂 openluffy          ← Current repo
    📂 another-repo
    
Top navbar:
  [Search] [Pull requests] [Issues] [Marketplace] [Explore] [👤 Profile]
  
Repo context tabs (below navbar):
  Code | Issues | Pull Requests | Actions | Projects | Security | Insights
  
Main content area:
  (Shows content for selected tab within this repo)
```

**Key insights:**
1. **Sidebar = Repository selector** (navigate TO a repo)
2. **Tabs = Views within that repo** (Code, Issues, PRs, etc.)
3. **No dropdowns** to switch repos — sidebar navigation
4. **Each repo is isolated** — you're IN a repo, viewing its resources

---

## OpenLuffy Navigation Model (Proposed)

### Sidebar Structure

```
OpenLuffy

🎛️ Control Plane          ← Click to enter Control Plane realm
   └─ Applications
   └─ Infrastructure
   └─ Monitoring
   └─ Settings

─────────────────────────

📦 Customer Projects

   🏢 Trucks Inc          ← Click to enter Trucks Inc realm
      └─ Applications
      └─ Pipelines
      └─ Secrets & Variables
      └─ Settings

   🏢 Acme Corp           ← Click to enter Acme Corp realm
      └─ Applications
      └─ Pipelines
      └─ Secrets & Variables
      └─ Settings

   🏢 Widget Co
      └─ Applications
      └─ Pipelines
      └─ Secrets & Variables
      └─ Settings

─────────────────────────

➕ Create New Project
```

### When User Clicks "Control Plane"

**URL:** `/projects/control-plane`

**Sidebar (collapsed to active project):**
```
🎛️ Control Plane ▼         ← Expanded, active
   Applications           ← Views within Control Plane
   Infrastructure
   Monitoring
   Settings

📦 Customer Projects
   (collapsed list)
```

**Top navbar:**
```
[OpenLuffy Logo] [Search...] [Notifications] [👤 Admin]
```

**Context tabs (below navbar):**
```
Applications | Infrastructure | Monitoring | Settings
```

**Main content:**
```
(Shows Applications list for Control Plane)

Deployments:
- openluffy-dev
- openluffy-preprod  
- openluffy-prod
```

---

### When User Clicks "Trucks Inc"

**URL:** `/projects/trucks-inc`

**Sidebar (active project expanded):**
```
🎛️ Control Plane
   (collapsed)

📦 Customer Projects

   🏢 Trucks Inc ▼        ← Expanded, active
      Applications       ← Views within Trucks Inc
      Pipelines
      Secrets & Variables
      Settings

   🏢 Acme Corp
      (collapsed)

   🏢 Widget Co
      (collapsed)
```

**Context tabs (below navbar):**
```
Applications | Pipelines | Secrets & Variables | Settings
```

**Main content:**
```
(Shows Applications list for Trucks Inc)

Deployments:
- trucks-api-dev
- trucks-web-preprod
- trucks-api-prod
```

**CANNOT see:** openluffy-dev, acme-corp-api, etc. (different projects)

---

## Navigation Flow

### Scenario 1: Control Plane → Applications → Detail

1. **Sidebar:** Click "Control Plane"
   - URL: `/projects/control-plane`
   - Sidebar expands Control Plane section
   - Main content shows Control Plane overview or Applications list

2. **Tabs:** Click "Applications" (default active)
   - URL: `/projects/control-plane/applications`
   - Shows: openluffy-dev, openluffy-preprod, openluffy-prod

3. **Application:** Click "openluffy-dev"
   - URL: `/projects/control-plane/applications/openluffy-dev`
   - Shows: Application detail page (Resources, Networking, Pods, Events)

---

### Scenario 2: Trucks Inc → Applications → Detail

1. **Sidebar:** Click "Trucks Inc" (under Customer Projects)
   - URL: `/projects/trucks-inc`
   - Sidebar expands Trucks Inc section
   - Main content shows Trucks Inc overview or Applications list

2. **Tabs:** Click "Applications" (default active)
   - URL: `/projects/trucks-inc/applications`
   - Shows: trucks-api-dev, trucks-web-preprod, trucks-api-prod

3. **Application:** Click "trucks-api-dev"
   - URL: `/projects/trucks-inc/applications/trucks-api-dev`
   - Shows: Application detail page

**CANNOT access:** `/projects/trucks-inc/applications/openluffy-dev` → 403 Forbidden

---

### Scenario 3: Switching Projects

**Current context:** Viewing `/projects/trucks-inc/applications/trucks-api-dev`

**User action:** Click "Acme Corp" in sidebar

**Result:**
1. Navigate to `/projects/acme-corp`
2. Sidebar expands Acme Corp section, collapses Trucks Inc
3. Main content shows Acme Corp applications list
4. Previous context (trucks-api-dev) is lost — you're IN a different project now

---

## Sidebar Component Structure

### Desktop View

```
┌──────────────────────────────────────────────────────────────┐
│  [≡] OpenLuffy              [Search...] [🔔] [👤 Admin]      │
├──────────────┬───────────────────────────────────────────────┤
│              │ Applications | Infrastructure | Monitoring    │
│ Sidebar      ├───────────────────────────────────────────────┤
│ (250px)      │                                               │
│              │  Main Content Area                            │
│              │                                               │
│              │  (Applications list or detail view)           │
│              │                                               │
│              │                                               │
└──────────────┴───────────────────────────────────────────────┘
```

### Mobile View (Sidebar Collapsed)

```
┌──────────────────────────────────────────────────────────────┐
│  [≡] OpenLuffy              [Search...] [🔔] [👤]            │
├──────────────────────────────────────────────────────────────┤
│ Applications | Pipelines | Secrets | Settings               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Main Content Area                                           │
│                                                              │
│  (Full width)                                                │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Hamburger button [≡]:** Opens sidebar overlay with project list

---

## What Gets REMOVED

### ❌ Remove from Top Navbar:

1. **Customer/Project Dropdown** - Now in sidebar
2. **Environment Filter Dropdown** - Moved to Applications tab (if needed)

### ✅ Keep in Top Navbar:

1. **OpenLuffy Logo** (home link)
2. **Global Search** (search across all projects)
3. **Notifications** (bell icon)
4. **User Profile** (👤 Admin)
5. **Hamburger menu** (mobile only)

---

## Environment Filtering

**Question:** Where does "DEV / PREPROD / PROD" filter go?

**Answer:** Inside the Applications tab, NOT in navbar.

**Example - Applications Tab:**

```
┌─────────────────────────────────────────────────────────────┐
│ Applications                                                │
├─────────────────────────────────────────────────────────────┤
│ [All Environments ▼] [Search applications...]    [+ Create] │
├─────────────────────────────────────────────────────────────┤
│  trucks-api-dev       DEV      Running    ✓                │
│  trucks-api-preprod   PREPROD  Running    ✓                │
│  trucks-api-prod      PROD     Running    ✓                │
└─────────────────────────────────────────────────────────────┘
```

**Environment filter** is a LOCAL filter within the Applications view, not a global navbar dropdown.

---

## URL Structure (Final)

### Projects (Root Level)

```
/projects                              # List all projects (optional)
/projects/control-plane                # Control Plane home
/projects/trucks-inc                   # Trucks Inc home
/projects/acme-corp                    # Acme Corp home
```

### Project Views (Tabs)

```
/projects/{project_id}/applications              # Applications list
/projects/{project_id}/pipelines                 # CI/CD pipelines
/projects/{project_id}/secrets                   # Secrets & variables
/projects/{project_id}/infrastructure            # Infrastructure (Control Plane only)
/projects/{project_id}/monitoring                # Monitoring (Control Plane only)
/projects/{project_id}/settings                  # Project settings
```

### Application Detail

```
/projects/{project_id}/applications/{deployment_id}
/projects/{project_id}/applications/{deployment_id}/logs
/projects/{project_id}/applications/{deployment_id}/metrics
```

**Examples:**
```
/projects/control-plane/applications/openluffy-dev
/projects/trucks-inc/applications/trucks-api-prod
/projects/acme-corp/applications/acme-web-dev
```

---

## Sidebar Implementation (React Components)

### Component Structure

```jsx
// src/components/Sidebar.jsx
export function Sidebar({ isOpen, onClose }) {
  return (
    <div className={`sidebar ${isOpen ? 'open' : ''}`}>
      <ProjectList onProjectSelect={onClose} />
    </div>
  )
}

// src/components/ProjectList.jsx
export function ProjectList({ onProjectSelect }) {
  const { projects, selectedProject } = useProject()
  const navigate = useNavigate()
  
  const handleSelectProject = (projectId) => {
    navigate(`/projects/${projectId}`)
    onProjectSelect?.() // Close mobile sidebar
  }
  
  return (
    <>
      {/* Control Plane Section */}
      <div className="project-section">
        <div className="section-header">🎛️ Control Plane</div>
        <div 
          className={`project-item ${selectedProject === 'control-plane' ? 'active' : ''}`}
          onClick={() => handleSelectProject('control-plane')}
        >
          Control Plane
        </div>
        
        {/* Expanded views when active */}
        {selectedProject === 'control-plane' && (
          <div className="project-views">
            <div className="view-item" onClick={() => navigate('/projects/control-plane/applications')}>
              Applications
            </div>
            <div className="view-item" onClick={() => navigate('/projects/control-plane/infrastructure')}>
              Infrastructure
            </div>
            <div className="view-item" onClick={() => navigate('/projects/control-plane/monitoring')}>
              Monitoring
            </div>
            <div className="view-item" onClick={() => navigate('/projects/control-plane/settings')}>
              Settings
            </div>
          </div>
        )}
      </div>
      
      <div className="sidebar-divider"></div>
      
      {/* Customer Projects Section */}
      <div className="project-section">
        <div className="section-header">📦 Customer Projects</div>
        
        {projects.filter(p => p.id !== 'control-plane').map(project => (
          <div key={project.id}>
            <div 
              className={`project-item ${selectedProject === project.id ? 'active' : ''}`}
              onClick={() => handleSelectProject(project.id)}
            >
              🏢 {project.name}
            </div>
            
            {/* Expanded views when active */}
            {selectedProject === project.id && (
              <div className="project-views">
                <div className="view-item" onClick={() => navigate(`/projects/${project.id}/applications`)}>
                  Applications
                </div>
                <div className="view-item" onClick={() => navigate(`/projects/${project.id}/pipelines`)}>
                  Pipelines
                </div>
                <div className="view-item" onClick={() => navigate(`/projects/${project.id}/secrets`)}>
                  Secrets & Variables
                </div>
                <div className="view-item" onClick={() => navigate(`/projects/${project.id}/settings`)}>
                  Settings
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
      
      <div className="sidebar-divider"></div>
      
      {/* Create New Project */}
      <div className="create-project-btn" onClick={() => navigate('/projects/new')}>
        ➕ Create New Project
      </div>
    </>
  )
}
```

---

## Context Tabs Component

```jsx
// src/components/ProjectTabs.jsx
export function ProjectTabs() {
  const { projectId } = useParams()
  const location = useLocation()
  
  // Determine available tabs based on project type
  const isControlPlane = projectId === 'control-plane'
  
  const tabs = isControlPlane 
    ? ['applications', 'infrastructure', 'monitoring', 'settings']
    : ['applications', 'pipelines', 'secrets', 'settings']
  
  const activeTab = location.pathname.split('/')[3] || 'applications'
  
  return (
    <div className="project-tabs">
      {tabs.map(tab => (
        <Link
          key={tab}
          to={`/projects/${projectId}/${tab}`}
          className={`tab ${activeTab === tab ? 'active' : ''}`}
        >
          {formatTabName(tab)}
        </Link>
      ))}
    </div>
  )
}
```

---

## Updated Layout Structure

```jsx
// src/App.jsx
function ProjectLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  
  return (
    <div className="app">
      <TopNavbar onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />
      
      <div className="app-body">
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        {sidebarOpen && <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />}
        
        <main className="main-content">
          <ProjectTabs />
          <div className="content-area">
            <Outlet /> {/* Nested routes render here */}
          </div>
        </main>
      </div>
    </div>
  )
}

// Routes
<Routes>
  <Route path="/projects/:projectId" element={<ProjectLayout />}>
    <Route index element={<Navigate to="applications" />} />
    <Route path="applications" element={<ApplicationsList />} />
    <Route path="applications/:deploymentId" element={<ApplicationDetail />} />
    <Route path="pipelines" element={<PipelinesList />} />
    <Route path="secrets" element={<SecretsVariables />} />
    <Route path="infrastructure" element={<Infrastructure />} />
    <Route path="monitoring" element={<Monitoring />} />
    <Route path="settings" element={<ProjectSettings />} />
  </Route>
</Routes>
```

---

## Benefits of This Model

### 1. Mental Model Clarity
- "I'm IN Control Plane" vs "I'm filtering to Control Plane"
- Navigation is intentional, not accidental

### 2. True Isolation
- Cannot accidentally view wrong project's resources
- URL structure enforces project boundaries

### 3. Scalability
- Easy to add new projects (just add to sidebar)
- Each project can have different views/permissions

### 4. Matches Industry Standards
- GitHub repos
- AWS Console (service navigation within account)
- GCP Console (resources within project)

### 5. Mobile-Friendly
- Sidebar collapses to hamburger menu
- Tabs scroll horizontally on small screens
- No complex dropdown interactions

---

## Migration from Current Design

### Phase 1: Remove Navbar Dropdowns
- [ ] Remove Customer dropdown from TopNavbar
- [ ] Remove Environment dropdown from TopNavbar
- [ ] Keep only: Logo, Search, Notifications, User Profile

### Phase 2: Implement Sidebar Project List
- [ ] Create ProjectList component
- [ ] Add Control Plane section
- [ ] Add Customer Projects section
- [ ] Implement expand/collapse on active project

### Phase 3: Add Context Tabs
- [ ] Create ProjectTabs component
- [ ] Show different tabs for Control Plane vs Customer Projects
- [ ] Highlight active tab

### Phase 4: Update Routes
- [ ] Wrap project views in ProjectLayout
- [ ] Update all routes to `/projects/{id}/{view}` structure
- [ ] Add redirects from old URLs

### Phase 5: Environment Filter (Applications Tab)
- [ ] Move environment filter INTO Applications view
- [ ] Make it a local filter, not global context

---

## Summary: Key Changes

**Before (WRONG):**
```
Navbar: [Project: Trucks Inc ▼] [Env: All ▼]
Sidebar: Applications | Pipelines | Secrets
Content: Shows ALL deployments (openluffy-dev visible in Trucks Inc context)
```

**After (CORRECT):**
```
Navbar: [OpenLuffy] [Search] [Notifications] [Profile]
Sidebar: 
  🎛️ Control Plane
  📦 Customer Projects
     🏢 Trucks Inc ▼
        Applications  ← Navigate here
        Pipelines
        Secrets
Content: Shows ONLY Trucks Inc deployments (openluffy-dev NOT visible)
```

**Navigation:** Click project in sidebar → Enter that project's realm → View its resources

---

**This matches how GitHub, AWS, GCP, and Azure handle multi-tenant navigation.**

**Last Updated:** 2026-03-09
