# Chatbot Parity Requirements

**Core Principle:** Whatever the UI can do, Luffy chatbot MUST be able to do.

---

## Current UI Capabilities → Chatbot Requirements

### Application Management (UI)

**UI Actions:**
- View application details (resources, networking, pods, events)
- Scale deployment (replica count)
- Restart deployment
- Rollback to previous version
- Sync/deploy latest version

**Chatbot Requirements:**

```
User: "Show me details for acme-corp-dev"
Luffy: [Displays resource specs, networking, current status]

User: "Scale acme-corp-dev to 5 replicas"
Luffy: Scaling acme-corp-dev to 5 replicas...
       ✓ Scaled successfully. Current: 5/5 ready

User: "Restart customer-api-prod"
Luffy: ⚠️ Restarting PRODUCTION deployment. Confirm? (yes/no)
User: yes
Luffy: Restarting customer-api-prod...
       ✓ All pods restarted. Status: Healthy

User: "Rollback acme-corp-preprod"
Luffy: Rolling back to previous revision...
       ✓ Rolled back to revision 23. Status: Synced

User: "What's the connection command for acme-corp-dev?"
Luffy: kubectl port-forward -n openluffy-dev deployment/acme-corp-dev 8080:8080
       Then access: http://localhost:8080
```

### Resources Tab (UI)

**UI Shows:**
- CPU/Memory requests and limits
- Deployment strategy
- Container image details
- Image pull policy

**Chatbot Requirements:**

```
User: "What are the resource limits for customer-api-prod?"
Luffy: customer-api-prod resource specs:
       CPU Request: 100m | Limit: 500m
       Memory Request: 128Mi | Limit: 512Mi
       Strategy: RollingUpdate (MaxSurge: 1, MaxUnavailable: 0)

User: "What image is running in acme-corp-dev?"
Luffy: ghcr.io/lebrick07/acme-corp-api:dev-a1b2c3d
       Registry: ghcr.io
       Pull Policy: IfNotPresent
```

### Networking Tab (UI)

**UI Shows:**
- How to connect (kubectl commands)
- Service configuration
- Internal DNS names
- Network policies

**Chatbot Requirements:**

```
User: "How do I connect to customer-api-preprod?"
Luffy: Connection methods:

       1. Port Forward:
       kubectl port-forward -n openluffy-preprod deployment/customer-api-preprod 8080:8080

       2. Internal DNS:
       customer-api-preprod.openluffy-preprod.svc.cluster.local

       3. Shell access:
       kubectl exec -n openluffy-preprod -it deployment/customer-api-preprod -- /bin/sh

User: "What's the service type for acme-corp-prod?"
Luffy: Service: acme-corp-prod
       Type: ClusterIP
       Namespace: openluffy-prod
       Ports: 8080 → 8080 (TCP)
```

### Pods Tab (UI)

**UI Shows:**
- Pod list (name, status, restarts, IP, node, age)
- Container details
- Actions (logs, shell, delete)

**Chatbot Requirements:**

```
User: "List pods for customer-api-dev"
Luffy: Pods in customer-api-dev:
       
       NAME                              STATUS    RESTARTS  IP          NODE
       customer-api-dev-7b9c8d-x9z2k     Running   0         10.42.0.45  pi5-node-0
       
       Containers: customer-api (ready)

User: "Show logs for customer-api-dev"
Luffy: [Streams last 50 lines of logs]
       ...
       [2026-03-09 05:00:00] INFO: Server started on port 8080

User: "Exec into customer-api-dev"
Luffy: Opening shell session...
       (Note: This would require interactive shell support)
```

### Events Tab (UI)

**UI Shows:**
- Event timeline (type, timestamp, reason, message)
- Filter by type (Normal/Warning/Error)

**Chatbot Requirements:**

```
User: "Show recent events for acme-corp-preprod"
Luffy: Recent events for acme-corp-preprod:

       [2026-03-09 04:55:12] Normal - Scaled
       Scaled deployment to 3 replicas

       [2026-03-09 04:50:30] Normal - Pulled
       Successfully pulled image ghcr.io/lebrick07/acme-corp:dev-abc123

       [2026-03-09 04:50:28] Normal - Scheduled
       Successfully assigned pod to pi5-node-0

User: "Any warnings for customer-api-prod?"
Luffy: ⚠️ 2 warnings in last 24h:
       
       [2026-03-09 03:15:00] Warning - BackOff
       Back-off restarting failed container
       
       [2026-03-08 22:30:00] Warning - Unhealthy
       Readiness probe failed
```

---

## Implementation Checklist

### Backend APIs (Required for Chatbot)

- [ ] `/api/v1/chat/deployment/:id/details` - Get comprehensive deployment info
- [ ] `/api/v1/chat/deployment/:id/scale` - Scale deployment
- [ ] `/api/v1/chat/deployment/:id/restart` - Restart deployment
- [ ] `/api/v1/chat/deployment/:id/rollback` - Rollback deployment
- [ ] `/api/v1/chat/deployment/:id/logs` - Stream logs
- [ ] `/api/v1/chat/deployment/:id/events` - Get events
- [ ] `/api/v1/chat/deployment/:id/resources` - Get resource specs
- [ ] `/api/v1/chat/deployment/:id/networking` - Get service/ingress info
- [ ] `/api/v1/chat/command/port-forward` - Generate kubectl commands
- [ ] `/api/v1/chat/command/exec` - Generate exec commands

### Chatbot Tool Functions

**File:** `backend/tools/deployment_tools.py`

```python
async def get_deployment_details(deployment_id: str) -> Dict:
    """Get comprehensive deployment information"""
    
async def scale_deployment(deployment_id: str, replicas: int) -> Dict:
    """Scale deployment to specified replicas"""
    
async def restart_deployment(deployment_id: str) -> Dict:
    """Restart all pods in deployment"""
    
async def rollback_deployment(deployment_id: str, revision: Optional[int] = None) -> Dict:
    """Rollback to previous or specified revision"""
    
async def get_deployment_logs(deployment_id: str, lines: int = 50) -> str:
    """Get recent logs from deployment pods"""
    
async def get_deployment_events(deployment_id: str, filter_type: Optional[str] = None) -> List[Dict]:
    """Get deployment events with optional filtering"""
    
async def get_resource_specs(deployment_id: str) -> Dict:
    """Get CPU/Memory specs and deployment strategy"""
    
async def get_networking_info(deployment_id: str) -> Dict:
    """Get service, ingress, and DNS information"""
    
async def generate_connect_command(deployment_id: str, method: str = "port-forward") -> str:
    """Generate kubectl connection commands"""
```

### Natural Language Processing

**File:** `backend/ai/intent_classifier.py`

Luffy needs to understand variations:

```python
# Scaling intents
"scale X to 5"
"set X replicas to 5"
"increase X to 5 instances"
"grow X to 5 pods"

# Restart intents
"restart X"
"reboot X"
"reload X"
"bounce X"

# Info retrieval
"show me X"
"what's the status of X"
"tell me about X"
"details for X"
"info on X"

# Connection intents
"how do I connect to X"
"give me the connection command for X"
"how to access X"
```

### Confirmation Prompts

**File:** `backend/ai/confirmation_handler.py`

```python
DESTRUCTIVE_ACTIONS = {
    "restart": "⚠️ This will restart all pods. Continue?",
    "rollback": "⚠️ This will rollback to previous version. Continue?",
    "delete": "🚨 This will DELETE the deployment. Type 'DELETE' to confirm.",
    "scale_down_prod": "⚠️ Scaling down PRODUCTION. Continue?",
}

async def require_confirmation(action: str, context: Dict) -> bool:
    """Handle confirmation flow for destructive actions"""
```

---

## Testing Requirements

### Unit Tests

- [ ] Test each tool function independently
- [ ] Mock Kubernetes API responses
- [ ] Verify error handling

### Integration Tests

- [ ] End-to-end flow: User message → Intent → Tool → Response
- [ ] Test confirmation flows
- [ ] Test multi-step operations

### User Acceptance Testing

- [ ] DevOps engineer can perform all UI actions via chat
- [ ] Response time < 3 seconds for most operations
- [ ] Clear, actionable error messages
- [ ] Confirmation prompts work correctly

---

## Documentation Requirements

- [ ] Update LUFFY_ENGINE.md with new capabilities
- [ ] Add chatbot command reference (user docs)
- [ ] Document tool functions (developer docs)
- [ ] Add examples to README

---

## Success Criteria

✅ **Parity Achieved When:**

1. Every action available in the UI can be performed via chat
2. Luffy understands natural language variations
3. Response format matches user expectations
4. Confirmation prompts prevent mistakes
5. Error handling provides clear guidance
6. Performance is acceptable (< 3s for most ops)

**Goal:** A DevOps engineer should be able to manage deployments ENTIRELY via chat if they prefer.

---

**Last Updated:** 2026-03-09  
**Status:** In Progress - Phase 1 UI complete, chatbot implementation pending
