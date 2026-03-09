# OpenLuffy Roadmap

**Mission:** Build the AI-powered DevOps engine that scales one engineer to manage 5-10 customers.

**GitHub Project:** [OpenLuffy Development](https://github.com/lebrick07/openluffy/projects)

---

## Phase 1: Foundation (In Progress)

**Goal:** Stable platform with comprehensive UI and basic automation.

### 1.1 Core Platform ✅ COMPLETE
- [x] React frontend with dark theme
- [x] FastAPI backend
- [x] Kubernetes integration (read-only)
- [x] ArgoCD integration
- [x] Multi-environment support (dev/preprod/prod)
- [x] Authentication system
- [x] Split-screen UI (Dashboard + Luffy Chat)

### 1.2 CI/CD Pipeline ✅ COMPLETE
- [x] GitHub Actions workflows (dev, preprod, prod)
- [x] Multi-arch Docker builds (ARM64)
- [x] ArgoCD auto-sync
- [x] Helm-based deployments
- [x] Environment isolation

### 1.3 Application Management UI 🚧 IN PROGRESS
- [x] Applications table view
- [x] Environment filtering
- [x] Customer-based filtering
- [ ] **Comprehensive Application Detail Page** (PR #113)
  - [x] Sidebar navigation on detail page
  - [x] Responsive navbar (filters visible on mobile)
  - [x] Resources tab (CPU/Memory, deployment strategy, image details)
  - [x] Networking tab (connection commands, service info, DNS)
  - [ ] Backend APIs for real data (not placeholders)
  - [ ] Storage tab (PVCs, volumes)
  - [ ] Security tab (RBAC, service accounts, network policies)
  - [ ] Logs tab (live streaming)
  - [ ] Metrics tab (CPU/Memory graphs)
- [ ] Delete deployment action
- [ ] Download manifest action

---

## Phase 2: Chatbot Parity (Next)

**Goal:** Luffy chatbot can do everything the UI can do.

**GitHub Project Board:** "Chatbot Parity" column

### 2.1 Backend API Expansion
- [ ] `/api/v1/deployments/:id/resources` - Real resource specs from K8s
- [ ] `/api/v1/deployments/:id/networking` - Services, ingress, DNS
- [ ] `/api/v1/deployments/:id/storage` - PVCs, volumes
- [ ] `/api/v1/deployments/:id/security` - RBAC, service accounts, policies
- [ ] `/api/v1/deployments/:id/logs` - Stream container logs
- [ ] `/api/v1/deployments/:id/metrics` - Fetch CPU/Memory from metrics-server
- [ ] `/api/v1/deployments/:id/delete` - Delete deployment (with safeguards)
- [ ] `/api/v1/deployments/:id/manifest` - Download YAML manifest

### 2.2 Chatbot Tool Functions
**Ref:** [CHATBOT-PARITY.md](docs/CHATBOT-PARITY.md)

- [ ] `get_deployment_details(id)` - Show comprehensive info
- [ ] `scale_deployment(id, replicas)` - Scale to N replicas
- [ ] `restart_deployment(id)` - Restart all pods
- [ ] `rollback_deployment(id, revision)` - Rollback to previous version
- [ ] `get_deployment_logs(id, lines)` - Stream logs
- [ ] `get_deployment_events(id, filter)` - Show events
- [ ] `get_resource_specs(id)` - CPU/Memory/limits
- [ ] `get_networking_info(id)` - Service/Ingress/DNS
- [ ] `generate_connect_command(id, method)` - kubectl commands
- [ ] `delete_deployment(id)` - Delete with confirmation

### 2.3 Natural Language Understanding
- [ ] Intent classification (scale/restart/rollback/info/connect)
- [ ] Entity extraction (deployment ID, replicas, environment)
- [ ] Multi-turn conversations (confirmations)
- [ ] Error handling with actionable suggestions

### 2.4 Testing & Documentation
- [ ] Unit tests for all tool functions
- [ ] Integration tests for chat flows
- [ ] User documentation (command reference)
- [ ] Developer documentation (tool API)

**Success Criteria:** DevOps engineer can manage deployments entirely via chat.

---

## Phase 3: Customer Onboarding Automation (Future)

**Goal:** "Create Customer" button → Full infrastructure in 5 minutes.

**Ref:** [LUFFY_ENGINE.md](docs/LUFFY_ENGINE.md#2-create-customer--full-automation)

### 3.1 GitHub Integration
- [ ] GitHub API client (`github_client.py`)
- [ ] Create repo from template
- [ ] Initialize with CI/CD pipeline
- [ ] Manage secrets via GitHub API
- [ ] Trigger workflows programmatically

### 3.2 Customer Onboarding Flow
- [ ] UI wizard: "Create New Customer"
- [ ] Backend orchestration: `customer_onboarding.py`
- [ ] Automated flow:
  1. Create GitHub repo (or use existing)
  2. Initialize with template (Node.js/Python/Go/Java)
  3. Create CI/CD pipeline (.github/workflows/)
  4. Create ArgoCD Applications (dev, preprod, prod)
  5. Create K8s namespaces
  6. Deploy to dev environment
  7. Configure ingresses
  8. Set up secrets
- [ ] Progress tracking in UI
- [ ] Rollback on failure

### 3.3 Templates
- [ ] Node.js/Express API template
- [ ] Python/FastAPI template
- [ ] Go/Gin template
- [ ] Java/Spring Boot template
- [ ] React/Vue frontend template

**Success Criteria:** Customer onboarded in < 5 minutes with zero manual steps.

---

## Phase 4: PR Management (Future)

**Goal:** Review and merge PRs without leaving OpenLuffy UI.

**Ref:** [LUFFY_ENGINE.md](docs/LUFFY_ENGINE.md#3-pr-approval-from-ui)

### 4.1 PR List View
- [ ] Fetch pending PRs via GitHub API
- [ ] Show CI status (passing/failing)
- [ ] Filter by customer/repo
- [ ] Sort by priority/age

### 4.2 PR Review UI
- [ ] Inline diff view
- [ ] File tree navigation
- [ ] Comment on lines
- [ ] Approve/Request Changes buttons

### 4.3 PR Actions
- [ ] Approve PR (GitHub API)
- [ ] Merge PR (squash/merge/rebase)
- [ ] Track deployment after merge
- [ ] Show ArgoCD sync status

### 4.4 Luffy Chatbot Integration
```
User: "Show me pending PRs"
Luffy: 3 pending PRs:
       
       #42 - feat: Add user authentication (✓ CI passing)
       #43 - fix: Memory leak in worker (⚠️ CI failing)
       #44 - chore: Update dependencies (✓ CI passing)

User: "Show me diff for PR #42"
Luffy: [Displays diff with file changes]

User: "Approve and merge PR #42"
Luffy: ✓ Approved PR #42
       ✓ Merged to main
       🚀 Deployment triggered
       Status: Syncing...
```

**Success Criteria:** DevOps engineer can manage PRs without leaving OpenLuffy.

---

## Phase 5: Full Autonomy (Future)

**Goal:** Luffy auto-heals issues and proactively optimizes.

### 5.1 Auto-Healing
- [ ] Detect common failure patterns
- [ ] Auto-restart crashed pods
- [ ] Auto-scale under load
- [ ] Rollback on deployment failures
- [ ] Self-healing network issues

### 5.2 Proactive Monitoring
- [ ] Analyze logs for errors
- [ ] Detect performance degradation
- [ ] Alert on anomalies
- [ ] Generate incident reports

### 5.3 Cost Optimization
- [ ] Right-size resource requests/limits
- [ ] Suggest scaling strategies
- [ ] Identify unused resources
- [ ] Optimize container images

### 5.4 Security
- [ ] Automated CVE scanning
- [ ] Suggest security patches
- [ ] Detect misconfigurations
- [ ] Enforce policies

**Success Criteria:** DevOps engineer trusts Luffy to run overnight without supervision.

---

## GitHub Projects Integration

### Project Board Columns

1. **Backlog** - Future work, not yet prioritized
2. **To Do** - Prioritized, ready to start
3. **In Progress** - Actively being worked on
4. **Review** - PR created, awaiting approval
5. **Testing** - Deployed to dev/preprod, verification in progress
6. **Done** - Merged to main, deployed to production

### Issue Labels

- `phase-1` / `phase-2` / `phase-3` / `phase-4` / `phase-5`
- `frontend` / `backend` / `chatbot` / `infra` / `docs`
- `bug` / `feature` / `enhancement` / `chore`
- `priority-high` / `priority-medium` / `priority-low`
- `chatbot-parity` - Requires chatbot implementation

### Milestones

- **v1.0** - Phase 1 complete (Comprehensive UI, basic automation)
- **v1.5** - Phase 2 complete (Chatbot parity with UI)
- **v2.0** - Phase 3 complete (Customer onboarding automation)
- **v2.5** - Phase 4 complete (PR management in UI)
- **v3.0** - Phase 5 complete (Full autonomy, auto-healing)

---

## Current Sprint (March 2026)

**Goal:** Complete Phase 1.3 + Start Phase 2.1

### In Progress
- [ ] PR #113 - Comprehensive Application Detail Page
  - Sidebar + responsive fixes
  - Resources tab + Networking tab
  - Backend APIs for real data

### Up Next
- [ ] Backend API implementation (resources, networking, storage, security, logs, metrics)
- [ ] Chatbot tool functions (scale, restart, rollback, info)
- [ ] Natural language intent classification

---

## Success Metrics

**Phase 1:**
- ✅ Time to view deployment status: < 3 seconds
- ✅ UI responsiveness: Works on mobile/tablet/desktop
- 🚧 Information completeness: 100% of K8s data visible

**Phase 2:**
- ⏳ Chatbot command success rate: > 95%
- ⏳ Response time: < 3 seconds for most operations
- ⏳ User satisfaction: DevOps engineer prefers chat over clicking

**Phase 3:**
- ⏳ Customer onboarding time: < 5 minutes (from 2+ hours)
- ⏳ Manual steps required: 0
- ⏳ Success rate: > 99%

---

**Last Updated:** 2026-03-09  
**Next Review:** After Phase 1.3 completion

**GitHub Project:** https://github.com/lebrick07/openluffy/projects
