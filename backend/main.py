from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import os
import httpx
import json
from pathlib import Path
from datetime import datetime
from triage import triage_engine
from luffy_agent import get_agent
from database import init_db, get_db, check_db_connection, Customer, Integration, ProvisioningStep
from init_github_integrations import init_github_integrations

app = FastAPI(title="openluffy")

# Database initialization flag
db_available = False

# Persistent storage for integration configs
INTEGRATIONS_FILE = Path("/data/integrations.json")
integrations_store: Dict[str, Dict[str, Any]] = {}

def load_integrations():
    """Load integrations from disk"""
    global integrations_store
    if INTEGRATIONS_FILE.exists():
        try:
            with open(INTEGRATIONS_FILE, 'r') as f:
                integrations_store = json.load(f)
                print(f"✅ Loaded {len(integrations_store)} customer integrations from disk")
        except Exception as e:
            print(f"⚠️ Failed to load integrations: {e}")
            integrations_store = {}
    else:
        print("ℹ️ No existing integrations file, starting fresh")
        integrations_store = {}

def save_integrations():
    """Save integrations to disk"""
    try:
        INTEGRATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(INTEGRATIONS_FILE, 'w') as f:
            json.dump(integrations_store, f, indent=2)
        print(f"💾 Saved integrations to disk ({len(integrations_store)} customers)")
    except Exception as e:
        print(f"⚠️ Failed to save integrations: {e}")

# Load integrations on startup
load_integrations()


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup with retry logic"""
    global db_available
    import time
    
    # Check if DATABASE_URL is set
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        print(f"🗄️ Database URL configured: {database_url.split('@')[0]}@...")  # Hide credentials
        
        # Retry logic: wait for database to be fully ready
        max_retries = 30  # 30 retries * 2s = 60s max wait
        retry_delay = 2
        
        for attempt in range(1, max_retries + 1):
            try:
                print(f"📊 Database connection attempt {attempt}/{max_retries}...")
                init_db()
                
                if check_db_connection():
                    db_available = True
                    print("✅ Database connection successful")
                    
                    # Migrate existing integrations_store to database
                    await migrate_integrations_to_db()
                    
                    # Initialize GitHub integrations for all customers
                    from database import SessionLocal
                    db = SessionLocal()
                    try:
                        init_github_integrations(db)
                    finally:
                        db.close()
                    
                    break
                else:
                    raise Exception("Connection check failed")
                    
            except Exception as e:
                if attempt < max_retries:
                    print(f"⚠️ Database not ready yet: {e}")
                    print(f"⏳ Retrying in {retry_delay}s... ({attempt}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    print(f"❌ Database initialization failed after {max_retries} attempts")
                    print(f"⚠️ Error: {e}")
                    print("ℹ️ Falling back to file storage")
                    break
    else:
        print("ℹ️ DATABASE_URL not set - using file storage")


async def migrate_integrations_to_db():
    """Migrate existing integrations from file storage to database"""
    if not integrations_store:
        return
    
    from database import get_db_session
    
    try:
        with get_db_session() as db:
            migrated = 0
            for customer_id, integrations in integrations_store.items():
                # Check if customer exists in DB
                customer = db.query(Customer).filter(Customer.id == customer_id).first()
                
                # If not, create customer from integrations data
                if not customer:
                    github = integrations.get('github', {})
                    repo = github.get('repo', f'{customer_id}-app')
                    
                    customer = Customer(
                        id=customer_id,
                        name=customer_id.replace('-', ' ').title(),
                        stack='nodejs',  # Default, will be updated later
                        github_repo=f"{github.get('org', 'unknown')}/{repo}"
                    )
                    db.add(customer)
                    db.flush()
                
                # Migrate integrations
                for integration_type, config in integrations.items():
                    # Check if integration already exists
                    existing = db.query(Integration).filter(
                        Integration.customer_id == customer_id,
                        Integration.type == integration_type
                    ).first()
                    
                    if not existing:
                        integration = Integration(
                            customer_id=customer_id,
                            type=integration_type,
                            config=config
                        )
                        db.add(integration)
                        migrated += 1
            
            db.commit()
            print(f"✅ Migrated {migrated} integrations to database")
    except Exception as e:
        print(f"⚠️ Migration failed: {e}")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load K8s config (in-cluster)
try:
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()
    k8s_available = True
except:
    k8s_available = False
    v1 = None
    apps_v1 = None

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/")
def root():
    return {"service": "openluffy", "status": "running", "version": "0.1.0"}

@app.get("/status")
def api_status():
    return {
        "service": "openluffy-backend",
        "status": "operational",
        "version": "0.1.0",
        "k8s": k8s_available
    }

# ============================================================================
# AI TRIAGE ENDPOINT - Core Feature
# ============================================================================

class TriageRequest(BaseModel):
    error_log: str
    context: Optional[Dict[str, Any]] = None

@app.post("/triage/analyze")
def triage_analyze(request: TriageRequest):
    """
    AI Triage - Analyze error logs and determine root cause
    
    Core feature: Shut down developer blame-shifting with instant,
    authoritative analysis of whether an error is application bug
    or infrastructure issue.
    
    Example usage:
        POST /triage/analyze
        {
            "error_log": "NullPointerException at line 42...",
            "context": {"customer": "acme-corp", "environment": "prod"}
        }
    
    Returns:
        {
            "category": "application_bug",
            "severity": "high",
            "confidence": 0.9,
            "reasoning": "This is an APPLICATION ERROR. Stack trace shows...",
            "evidence": ["Null pointer dereference in application code"],
            "responsible_team": "Development Team",
            "suggested_actions": ["Review application logs...", "..."]
        }
    """
    try:
        result = triage_engine.analyze(request.error_log, request.context)
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# LUFFY AI CHAT - Conversational Interface
# ============================================================================

class ChatMessage(BaseModel):
    role: str
    content: str

class LuffyChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    history: Optional[List[ChatMessage]] = []

class LuffyActionRequest(BaseModel):
    action: str
    context: Optional[Dict[str, Any]] = None

@app.post("/luffy/chat")
async def luffy_chat(request: LuffyChatRequest):
    """
    Luffy AI Chat - Intelligent Conversational AI DevOps Engineer
    
    Uses Claude to provide:
    - Intelligent troubleshooting with real K8s data
    - Error analysis using AI triage engine
    - Deployments with safety checks
    - Rollbacks with version history
    - Proactive recommendations
    """
    try:
        # Get the Luffy agent instance
        agent = get_agent()
        
        # Extract context
        customer = request.context.get('customer') if request.context else None
        environment = request.context.get('environment') if request.context else None
        model = request.context.get('model') if request.context else None
        
        # Convert history to list of dicts
        history = [{"role": msg.role, "content": msg.content} for msg in request.history]
        
        # Call agent
        response = await agent.chat(
            message=request.message,
            customer=customer,
            environment=environment,
            history=history,
            model=model
        )
        
        # Return formatted response
        return {
            "content": response["response"],
            "actions": response.get("actions", []),
            "model": response.get("model"),
            "metadata": {
                "stop_reason": response.get("stop_reason"),
                "customer": customer,
                "environment": environment
            }
        }
        
    except ValueError as e:
        # API key not configured
        return {
            "content": "⚠️ **Configuration Error**\n\n" +
                       "Claude API key not configured. Please set ANTHROPIC_API_KEY environment variable.\n\n" +
                       f"Error: {str(e)}",
            "actions": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/luffy/action")
def luffy_action(request: LuffyActionRequest):
    """
    Execute Luffy AI actions
    
    Actions like:
    - deploy_prod: Deploy to production
    - rollback_vX.X.X: Rollback to version
    - view_logs: Show logs
    - view_errors: Show recent errors
    """
    action = request.action
    context = request.context or {}
    
    try:
        # Mock implementations - replace with real K8s operations
        
        if action == "deploy_prod":
            return {
                "success": True,
                "message": "Production deployment initiated. ETA: 3 minutes."
            }
        
        elif action.startswith("rollback_"):
            version = action.replace("rollback_", "")
            return {
                "success": True,
                "message": f"Rollback to {version} initiated. ETA: 2 minutes."
            }
        
        elif action == "view_logs":
            return {
                "success": True,
                "message": "Opening logs view..."
            }
        
        elif action == "view_errors":
            return {
                "success": True,
                "message": "Fetching recent errors..."
            }
        
        elif action == "check_status":
            return {
                "success": True,
                "message": "Fetching deployment status..."
            }
        
        else:
            return {
                "success": False,
                "message": f"Unknown action: {action}"
            }
        
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

# ============================================================================

@app.get("/customers")
def get_customers():
    """Get all customer deployments with multi-environment support - dynamically discovered"""
    if not k8s_available:
        return {'error': 'K8s not available', 'customers': [], 'total': 0}
    
    customers = []
    customer_map = {}  # {customer_id: {metadata}}
    
    # Helper function to get environment status
    def get_env_status(customer_id, env):
        namespace = f"{customer_id}-{env}"
        try:
            pods = v1.list_namespaced_pod(namespace)
            running = len([p for p in pods.items if p.status.phase == 'Running'])
            total = len(pods.items)
            return {
                'environment': env,
                'status': 'running' if running > 0 else 'error',
                'pods': {'running': running, 'total': total},
                'url': f'http://{customer_id}-{env}.local' if env == 'prod' else f'http://{env}.{customer_id}.local'
            }
        except:
            return {
                'environment': env,
                'status': 'error',
                'pods': {'running': 0, 'total': 0},
                'url': f'http://{customer_id}-{env}.local' if env == 'prod' else f'http://{env}.{customer_id}.local'
            }
    
    # Discover customer namespaces by scanning K8s
    try:
        all_namespaces = v1.list_namespace()
        
        for ns in all_namespaces.items:
            ns_name = ns.metadata.name
            labels = ns.metadata.labels or {}
            
            # Check if this is a customer namespace (has 'customer' label or matches pattern)
            customer_id = None
            env = None
            
            if 'customer' in labels and 'environment' in labels:
                # Namespace created by OpenLuffy (has our labels)
                customer_id = labels['customer']
                env = labels['environment']
            elif '-dev' in ns_name or '-preprod' in ns_name or '-prod' in ns_name:
                # Legacy namespace (pattern-based: customer-id-env)
                if ns_name.endswith('-dev'):
                    customer_id = ns_name.replace('-dev', '')
                    env = 'dev'
                elif ns_name.endswith('-preprod'):
                    customer_id = ns_name.replace('-preprod', '')
                    env = 'preprod'
                elif ns_name.endswith('-prod'):
                    customer_id = ns_name.replace('-prod', '')
                    env = 'prod'
            
            if customer_id and env:
                if customer_id not in customer_map:
                    # Try to get customer metadata from integrations or namespace labels
                    customer_name = labels.get('customer-name', customer_id.replace('-', ' ').title())
                    
                    # Check if we have integration data for this customer
                    github_config = integrations_store.get(customer_id, {}).get('github', {})
                    repo_name = github_config.get('repo', f'{customer_id}-app')
                    
                    # Detect stack from repo or namespace labels
                    stack = labels.get('stack', 'Unknown')
                    if 'node' in repo_name or 'api' in repo_name:
                        stack = 'Node.js'
                    elif 'webapp' in repo_name or 'fastapi' in repo_name:
                        stack = 'Python'
                    elif 'go' in repo_name:
                        stack = 'Go'
                    
                    customer_map[customer_id] = {
                        'id': customer_id,
                        'name': customer_name,
                        'app': repo_name,
                        'stack': stack,
                        'environments': []
                    }
    
    except Exception as e:
        print(f"Error discovering customer namespaces: {e}")
        # Fall back to empty list - no customers found
        return {'customers': [], 'total': 0}
    
    # Build environment status for each discovered customer
    for customer_id in customer_map:
        envs = [get_env_status(customer_id, env) for env in ['dev', 'preprod', 'prod']]
        customer_map[customer_id]['environments'] = envs
        customer_map[customer_id]['overallStatus'] = 'running' if any(e['status'] == 'running' for e in envs) else 'error'
    
    customers = list(customer_map.values())
    
    return {'customers': customers, 'total': len(customers)}

# Customer Integrations Management
integrations_store = {}  # In-memory store: {customer_id: {integration_type: config}}

@app.get("/customers/{customer_id}/integrations/{integration_type}")
def get_customer_integration(customer_id: str, integration_type: str, db: Session = Depends(get_db)):
    """Get integration config for a customer (database-first, with fallback)"""
    
    # Try database first (authoritative source)
    if db_available:
        try:
            integration = db.query(Integration).filter(
                Integration.customer_id == customer_id,
                Integration.type == integration_type
            ).first()
            
            if integration:
                return integration.to_dict(mask_secrets=True)
        except Exception as e:
            print(f"Database query failed: {e}")
    
    # Fall back to in-memory store (backward compatibility)
    if customer_id not in integrations_store:
        return JSONResponse(status_code=404, content={'error': 'No integrations configured'})
    
    if integration_type not in integrations_store[customer_id]:
        return JSONResponse(status_code=404, content={'error': f'{integration_type} not configured'})
    
    config = integrations_store[customer_id][integration_type].copy()
    # Don't expose sensitive data in GET
    if 'token' in config:
        config['token'] = '***'
    if 'password' in config:
        config['password'] = '***'
    
    return config

@app.post("/customers/{customer_id}/integrations/{integration_type}")
async def save_customer_integration(customer_id: str, integration_type: str, request: Request, db: Session = Depends(get_db)):
    """Save or update integration config for a customer (database-first)"""
    try:
        config = await request.json()
        
        # Save to database (authoritative)
        if db_available:
            try:
                # Check if integration already exists
                existing = db.query(Integration).filter(
                    Integration.customer_id == customer_id,
                    Integration.type == integration_type
                ).first()
                
                if existing:
                    # Update existing
                    existing.config = config
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new
                    integration = Integration(
                        customer_id=customer_id,
                        type=integration_type,
                        config=config
                    )
                    db.add(integration)
                
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"Failed to save integration to database: {e}")
        
        # Also save to in-memory store (backward compatibility)
        if customer_id not in integrations_store:
            integrations_store[customer_id] = {}
        
        integrations_store[customer_id][integration_type] = config
        save_integrations()  # Persist to disk
        
        return {'success': True, 'message': f'{integration_type} integration saved'}
    except Exception as e:
        return JSONResponse(status_code=400, content={'error': str(e)})

@app.delete("/customers/{customer_id}/integrations/{integration_type}")
def delete_customer_integration(customer_id: str, integration_type: str, db: Session = Depends(get_db)):
    """Remove integration config for a customer (database-first)"""
    
    # Delete from database (authoritative)
    if db_available:
        try:
            integration = db.query(Integration).filter(
                Integration.customer_id == customer_id,
                Integration.type == integration_type
            ).first()
            
            if integration:
                db.delete(integration)
                db.commit()
            else:
                # Not in database, check in-memory
                if customer_id not in integrations_store or integration_type not in integrations_store[customer_id]:
                    return JSONResponse(status_code=404, content={'error': f'{integration_type} not configured'})
        except Exception as e:
            db.rollback()
            print(f"Failed to delete integration from database: {e}")
    
    # Also delete from in-memory store (backward compatibility)
    if customer_id in integrations_store and integration_type in integrations_store[customer_id]:
        del integrations_store[customer_id][integration_type]
        
        # Clean up empty customer dict
        if not integrations_store[customer_id]:
            del integrations_store[customer_id]
        
        save_integrations()  # Persist to disk
    
    return {'success': True, 'message': f'{integration_type} integration removed'}

def initialize_customer_repo(customer_id: str, customer_name: str, stack: str, github: dict) -> dict:
    """
    Initialize a customer GitHub repo with CI/CD templates
    
    Args:
        customer_id: Customer ID (e.g., 'acme-corp')
        customer_name: Display name (e.g., 'Acme Corp')
        stack: Tech stack (nodejs/python/golang)
        github: GitHub config dict with org, repo, token, branch
    
    Returns:
        dict with templates_pushed list and message
    """
    import requests
    import base64
    from pathlib import Path
    
    result = {'templates_pushed': [], 'message': '', 'errors': []}
    
    try:
        templates_dir = Path(__file__).parent / 'templates'
        
        # Map stack to template files (HELM CHART STRUCTURE - following OpenLuffy pattern)
        stack_templates = {
            'nodejs': {
                '.github/workflows/ci.yaml': 'ci-nodejs.yaml',
                '.github/workflows/release-dev.yaml': 'release-dev.yaml',
                '.github/workflows/release-prod.yaml': 'release-prod.yaml',
                'Dockerfile': 'Dockerfile-nodejs',
                'index.js': 'app-nodejs.js',
                'package.json': 'package.json',
                '.gitignore': 'gitignore',
                'README.md': 'README.md',
                'helm/app/Chart.yaml': 'helm/Chart.yaml',
                'helm/app/values.yaml': 'helm/values.yaml',
                'helm/app/values/dev.yaml': 'helm/values-dev.yaml',
                'helm/app/values/preprod.yaml': 'helm/values-preprod.yaml',
                'helm/app/values/prod.yaml': 'helm/values-prod.yaml',
                'helm/app/templates/_helpers.tpl': 'helm/templates/_helpers.tpl',
                'helm/app/templates/deployment.yaml': 'helm/templates/deployment.yaml',
                'helm/app/templates/service.yaml': 'helm/templates/service.yaml',
            },
            'python': {
                '.github/workflows/ci.yaml': 'ci-python.yaml',
                '.github/workflows/release-dev.yaml': 'release-dev.yaml',
                '.github/workflows/release-prod.yaml': 'release-prod.yaml',
                'Dockerfile': 'Dockerfile-python',
                'app.py': 'app-python.py',
                'requirements.txt': 'requirements.txt',
                '.gitignore': 'gitignore',
                'README.md': 'README.md',
                'helm/app/Chart.yaml': 'helm/Chart.yaml',
                'helm/app/values.yaml': 'helm/values.yaml',
                'helm/app/values/dev.yaml': 'helm/values-dev.yaml',
                'helm/app/values/preprod.yaml': 'helm/values-preprod.yaml',
                'helm/app/values/prod.yaml': 'helm/values-prod.yaml',
                'helm/app/templates/_helpers.tpl': 'helm/templates/_helpers.tpl',
                'helm/app/templates/deployment.yaml': 'helm/templates/deployment.yaml',
                'helm/app/templates/service.yaml': 'helm/templates/service.yaml',
            },
            'golang': {
                '.github/workflows/ci.yaml': 'ci-golang.yaml',
                '.github/workflows/release-dev.yaml': 'release-dev.yaml',
                '.github/workflows/release-prod.yaml': 'release-prod.yaml',
                'Dockerfile': 'Dockerfile-golang',
                'main.go': 'app-golang.go',
                'go.mod': 'go.mod',
                '.gitignore': 'gitignore',
                'README.md': 'README.md',
                'helm/app/Chart.yaml': 'helm/Chart.yaml',
                'helm/app/values.yaml': 'helm/values.yaml',
                'helm/app/values/dev.yaml': 'helm/values-dev.yaml',
                'helm/app/values/preprod.yaml': 'helm/values-preprod.yaml',
                'helm/app/values/prod.yaml': 'helm/values-prod.yaml',
                'helm/app/templates/_helpers.tpl': 'helm/templates/_helpers.tpl',
                'helm/app/templates/deployment.yaml': 'helm/templates/deployment.yaml',
                'helm/app/templates/service.yaml': 'helm/templates/service.yaml',
            }
        }
        
        # Stack-specific instructions for README
        stack_instructions = {
            'nodejs': '''```bash
npm install
npm start
```

Visit: http://localhost:3000''',
            'python': '''```bash
pip install -r requirements.txt
python main.py
```

Visit: http://localhost:8000''',
            'go': '''```bash
go mod download
go run main.go
```

Visit: http://localhost:8080'''
        }
        
        if stack not in stack_templates:
            result['errors'].append(f'Unknown stack: {stack}')
            return result
        
        for target_path, template_file in stack_templates[stack].items():
            template_path = templates_dir / template_file
            
            if not template_path.exists():
                result['errors'].append(f'Template not found: {template_file}')
                continue
            
            # Read template content
            with open(template_path, 'r') as f:
                content = f.read()
            
            # Replace placeholders
            stack_info = {
                'nodejs': {'framework': 'Express.js', 'port': '3000'},
                'python': {'framework': 'FastAPI', 'port': '8000'},
                'golang': {'framework': 'net/http', 'port': '8080'},
            }
            
            info = stack_info.get(stack, {'framework': 'Unknown', 'port': '8000'})
            
            content = content.replace('{{CUSTOMER_ID}}', customer_id)
            content = content.replace('{{CUSTOMER_NAME}}', customer_name)
            content = content.replace('{{GITHUB_OWNER}}', github['org'])
            content = content.replace('{{REPO_NAME}}', github['repo'])
            content = content.replace('{{STACK}}', stack.title())
            content = content.replace('{{FRAMEWORK}}', info['framework'])
            content = content.replace('{{PORT}}', info['port'])
            content = content.replace('{{APP_NAME}}', github['repo'])
            content = content.replace('{{NAMESPACE}}', f"{customer_id}-dev")
            content = content.replace('{{ENVIRONMENT}}', 'development')
            content = content.replace('{{STACK_SETUP}}', stack_instructions.get(stack, ''))
            
            # Push file to GitHub using GitHub API
            file_url = f"https://api.github.com/repos/{github['org']}/{github['repo']}/contents/{target_path}"
            
            # Check if file exists
            check_response = requests.get(file_url, headers={
                'Authorization': f"token {github['token']}",
                'Accept': 'application/vnd.github.v3+json'
            })
            
            file_data = {
                'message': f'Add {target_path} via OpenLuffy',
                'content': base64.b64encode(content.encode()).decode(),
                'branch': github.get('branch', 'main')
            }
            
            if check_response.status_code == 200:
                # File exists, update it
                existing_file = check_response.json()
                file_data['sha'] = existing_file['sha']
            
            # Create or update file
            push_response = requests.put(file_url, json=file_data, headers={
                'Authorization': f"token {github['token']}",
                'Accept': 'application/vnd.github.v3+json'
            })
            
            if push_response.ok:
                result['templates_pushed'].append(target_path)
            else:
                result['errors'].append(f'Failed to push {target_path}: {push_response.status_code}')
        
        result['message'] = f'Repository initialized with {len(result["templates_pushed"])} files'
        
    except Exception as e:
        result['errors'].append(f'Exception: {str(e)}')
    
    return result

@app.post("/customers/create")
async def create_customer(request: Request):
    """
    Create a new customer with GitHub repo and ArgoCD applications
    
    Expects:
    {
        "name": "Acme Corp",
        "id": "acme-corp",
        "stack": "nodejs",
        "github": {
            "org": "lebrick07",
            "repo": "acme-corp-api",
            "token": "ghp_xxx",
            "branch": "main"
        },
        "argocd": {
            "url": "http://argocd.local",
            "token": "xxx"
        }
    }
    """
    try:
        data = await request.json()
        
        customer_name = data.get('name')
        customer_id = data.get('id')
        stack = data.get('stack', 'nodejs')
        github = data.get('github', {})
        argocd = data.get('argocd', {})
        
        if not customer_name or not customer_id:
            return JSONResponse(status_code=400, content={'error': 'Customer name and ID are required'})
        
        if not github.get('org') or not github.get('repo') or not github.get('token'):
            return JSONResponse(status_code=400, content={'error': 'GitHub integration is required'})
        
        if not argocd.get('url') or not argocd.get('token'):
            return JSONResponse(status_code=400, content={'error': 'ArgoCD integration is required'})
        
        result = {
            'success': True,
            'customer_id': customer_id,
            'customer_name': customer_name,
            'github': {},
            'k8s': {},
            'argocd': {}
        }
        
        # Step 1: Check if GitHub repo exists
        import requests
        
        repo_url = f"https://api.github.com/repos/{github['org']}/{github['repo']}"
        repo_response = requests.get(repo_url, headers={
            'Authorization': f"token {github['token']}",
            'Accept': 'application/vnd.github.v3+json'
        })
        
        if repo_response.status_code == 200:
            # Repo exists, use it
            result['github']['action'] = 'existing'
            result['github']['url'] = f"https://github.com/{github['org']}/{github['repo']}"
            result['github']['message'] = 'Using existing repository'
        elif repo_response.status_code == 404:
            # Repo doesn't exist, create it
            create_repo_url = f"https://api.github.com/user/repos"
            create_data = {
                'name': github['repo'],
                'description': f"Customer application - {customer_name}",
                'private': False,
                'auto_init': True
            }
            
            create_response = requests.post(create_repo_url, json=create_data, headers={
                'Authorization': f"token {github['token']}",
                'Accept': 'application/vnd.github.v3+json'
            })
            
            if not create_response.ok:
                return JSONResponse(status_code=400, content={
                    'error': f'Failed to create GitHub repository: {create_response.json().get("message", "Unknown error")}'
                })
            
            result['github']['action'] = 'created'
            result['github']['url'] = f"https://github.com/{github['org']}/{github['repo']}"
            result['github']['message'] = 'Repository created from template'
        else:
            return JSONResponse(status_code=400, content={
                'error': f'Failed to check GitHub repository: {repo_response.status_code}'
            })
        
        # Step 2: Create Customer record in database
        if db_available:
            try:
                from database import SessionLocal
                db = SessionLocal()
                try:
                    # Check if customer already exists
                    existing_customer = db.query(Customer).filter(Customer.id == customer_id).first()
                    if not existing_customer:
                        customer = Customer(
                            id=customer_id,
                            name=customer_name,
                            stack=stack
                        )
                        db.add(customer)
                        db.commit()
                        print(f"✅ Created customer record: {customer_name} ({customer_id})")
                    else:
                        print(f"ℹ️  Customer record already exists: {customer_name} ({customer_id})")
                except Exception as db_error:
                    db.rollback()
                    print(f"⚠️  Failed to create customer record: {db_error}")
                finally:
                    db.close()
            except Exception as e:
                print(f"Database error: {e}")
        
        # Step 3: Store integrations (database + in-memory)
        if db_available:
            try:
                from database import SessionLocal
                db = SessionLocal()
                try:
                    # Create GitHub integration
                    github_integration = Integration(
                        customer_id=customer_id,
                        type='github',
                        config=github
                    )
                    db.add(github_integration)
                    
                    # Create ArgoCD integration
                    argocd_integration = Integration(
                        customer_id=customer_id,
                        type='argocd',
                        config=argocd
                    )
                    db.add(argocd_integration)
                    
                    db.commit()
                    print(f"✅ Created integrations for {customer_id}")
                except Exception as db_error:
                    db.rollback()
                    print(f"⚠️  Failed to create integrations: {db_error}")
                finally:
                    db.close()
            except Exception as e:
                print(f"Database error: {e}")
        
        # Also store in memory (backward compatibility)
        if customer_id not in integrations_store:
            integrations_store[customer_id] = {}
        
        integrations_store[customer_id]['github'] = github
        integrations_store[customer_id]['argocd'] = argocd
        save_integrations()  # Persist to disk
        
        # Step 4: Create K8s namespaces (if k8s available)
        namespaces_created = []
        if k8s_available:
            try:
                for env in ['dev', 'preprod', 'prod']:
                    namespace_name = f"{customer_id}-{env}"
                    try:
                        from kubernetes.client import V1Namespace, V1ObjectMeta
                        namespace = V1Namespace(
                            metadata=V1ObjectMeta(
                                name=namespace_name,
                                labels={
                                    'customer': customer_id,
                                    'customer-name': customer_name,
                                    'environment': env,
                                    'stack': stack,
                                    'managed-by': 'openluffy'
                                }
                            )
                        )
                        v1.create_namespace(namespace)
                        namespaces_created.append(namespace_name)
                    except Exception as ns_error:
                        if '409' in str(ns_error):  # Already exists
                            namespaces_created.append(namespace_name)
                        else:
                            print(f"Failed to create namespace {namespace_name}: {ns_error}")
                
                result['k8s']['namespaces'] = namespaces_created
            except Exception as k8s_error:
                print(f"K8s namespace creation error: {k8s_error}")
                result['k8s']['error'] = str(k8s_error)
        
        # Step 5: Create ArgoCD applications
        argocd_apps_created = []
        argocd_errors = []
        
        if k8s_available:
            try:
                from kubernetes import client
                custom_api = client.CustomObjectsApi()
                
                environments = [
                    {'name': 'dev', 'auto_sync': True, 'values_file': 'values/dev.yaml'},
                    {'name': 'preprod', 'auto_sync': True, 'values_file': 'values/preprod.yaml'},
                    {'name': 'prod', 'auto_sync': False, 'values_file': 'values/prod.yaml'}
                ]
                
                for env in environments:
                    app_name = f"{customer_id}-{env['name']}"
                    namespace = f"{customer_id}-{env['name']}"
                    
                    argocd_app = {
                        'apiVersion': 'argoproj.io/v1alpha1',
                        'kind': 'Application',
                        'metadata': {
                            'name': app_name,
                            'namespace': 'argocd',
                            'finalizers': ['resources-finalizer.argocd.argoproj.io'],
                            'labels': {
                                'customer': customer_id,
                                'environment': env['name'],
                                'managed-by': 'openluffy'
                            }
                        },
                        'spec': {
                            'project': 'default',
                            'source': {
                                'repoURL': f"https://github.com/{github['org']}/{github['repo']}.git",
                                'targetRevision': github.get('branch', 'main'),
                                'path': 'helm/app',
                                'helm': {
                                    'valueFiles': [env['values_file']]
                                }
                            },
                            'destination': {
                                'server': 'https://kubernetes.default.svc',
                                'namespace': namespace
                            },
                            'syncPolicy': {
                                'automated': {
                                    'prune': env['auto_sync'],
                                    'selfHeal': env['auto_sync']
                                } if env['auto_sync'] else None,
                                'syncOptions': ['CreateNamespace=true'],
                                'retry': {
                                    'limit': 5,
                                    'backoff': {
                                        'duration': '5s',
                                        'factor': 2,
                                        'maxDuration': '3m'
                                    }
                                }
                            }
                        }
                    }
                    
                    try:
                        custom_api.create_namespaced_custom_object(
                            group='argoproj.io',
                            version='v1alpha1',
                            namespace='argocd',
                            plural='applications',
                            body=argocd_app
                        )
                        argocd_apps_created.append(app_name)
                        print(f"✅ Created ArgoCD app: {app_name}")
                    except Exception as app_error:
                        if '409' in str(app_error):  # Already exists
                            argocd_apps_created.append(f"{app_name} (already exists)")
                        else:
                            error_msg = f"Failed to create {app_name}: {str(app_error)}"
                            argocd_errors.append(error_msg)
                            print(f"❌ {error_msg}")
                
                result['argocd']['applications'] = argocd_apps_created
                if argocd_errors:
                    result['argocd']['errors'] = argocd_errors
                    result['argocd']['message'] = f'Created {len(argocd_apps_created)} apps with {len(argocd_errors)} errors'
                else:
                    result['argocd']['message'] = f'Successfully created {len(argocd_apps_created)} ArgoCD applications'
                    
            except Exception as argocd_error:
                result['argocd']['error'] = str(argocd_error)
                result['argocd']['message'] = 'Failed to create ArgoCD applications'
                print(f"ArgoCD creation error: {argocd_error}")
        else:
            result['argocd']['applications'] = []
            result['argocd']['message'] = 'K8s not available - ArgoCD apps not created'
        
        # Step 6: Push CI/CD templates to GitHub repo
        template_result = initialize_customer_repo(customer_id, customer_name, stack, github)
        result['github'].update(template_result)
        
        return result
        
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})

@app.post("/customers/{customer_id}/reinitialize")
async def reinitialize_customer_repo(customer_id: str, request: Request):
    """
    Reinitialize a customer's GitHub repository with CI/CD templates
    
    Useful for:
    - Fixing failed initial template push
    - Updating templates after changes
    - Re-applying templates to existing repos
    
    Expects (optional):
    {
        "stack": "nodejs"  // Override stack detection
    }
    """
    try:
        data = await request.json() if request.headers.get('content-type') == 'application/json' else {}
        
        # Get customer integrations
        github_config = None
        stack_override = data.get('stack')
        
        # Try database first
        if db_available:
            try:
                github_integration = db.query(Integration).filter(
                    Integration.customer_id == customer_id,
                    Integration.type == 'github'
                ).first()
                
                if github_integration:
                    github_config = github_integration.config
            except Exception as e:
                print(f"Database query failed: {e}")
        
        # Fall back to in-memory store
        if not github_config and customer_id in integrations_store:
            github_config = integrations_store[customer_id].get('github')
        
        if not github_config:
            return JSONResponse(status_code=404, content={
                'error': 'GitHub integration not configured for this customer'
            })
        
        # Detect stack if not overridden
        stack = stack_override
        if not stack:
            repo_name = github_config.get('repo', '')
            if 'node' in repo_name or 'api' in repo_name or 'express' in repo_name:
                stack = 'nodejs'
            elif 'py' in repo_name or 'fastapi' in repo_name or 'django' in repo_name:
                stack = 'python'
            elif 'go' in repo_name or 'golang' in repo_name:
                stack = 'golang'
            else:
                stack = 'nodejs'  # Default
        
        # Get customer name (try to find it)
        customer_name = customer_id.replace('-', ' ').title()
        
        # Reinitialize repository
        result = initialize_customer_repo(
            customer_id=customer_id,
            customer_name=customer_name,
            stack=stack,
            github=github_config
        )
        
        return {
            'success': len(result['errors']) == 0,
            'customer_id': customer_id,
            'stack': stack,
            **result
        }
        
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})

@app.delete("/customers/{customer_id}")
async def delete_customer(customer_id: str, request: Request, db: Session = Depends(get_db)):
    """
    Delete a customer and destroy all their environments
    
    Query params:
    - delete_repo=true: Also delete the GitHub repository (default: false, archives instead)
    - confirm=customer-id: Safety confirmation (required)
    
    This will:
    1. Delete ArgoCD applications (dev, preprod, prod)
    2. Delete K8s namespaces (dev, preprod, prod) 
    3. Archive or delete GitHub repository
    4. Delete customer record from database
    5. Remove all integrations
    """
    try:
        query_params = dict(request.query_params)
        delete_repo = query_params.get('delete_repo', 'false').lower() == 'true'
        confirmation = query_params.get('confirm', '')
        
        # Safety check: require confirmation
        if confirmation != customer_id:
            return JSONResponse(status_code=400, content={
                'error': 'Confirmation required',
                'message': f'Add ?confirm={customer_id} to confirm deletion'
            })
        
        result = {
            'success': True,
            'customer_id': customer_id,
            'deleted': {
                'argocd_apps': [],
                'k8s_namespaces': [],
                'github_repo': None,
                'integrations': [],
                'database_record': False
            },
            'errors': []
        }
        
        # Step 1: Get customer integrations
        github_config = None
        argocd_config = None
        
        if db_available:
            try:
                # Get GitHub integration
                github_integration = db.query(Integration).filter(
                    Integration.customer_id == customer_id,
                    Integration.type == 'github'
                ).first()
                
                if github_integration:
                    github_config = github_integration.config
                
                # Get ArgoCD integration
                argocd_integration = db.query(Integration).filter(
                    Integration.customer_id == customer_id,
                    Integration.type == 'argocd'
                ).first()
                
                if argocd_integration:
                    argocd_config = argocd_integration.config
            except Exception as e:
                result['errors'].append(f'Database query failed: {e}')
        
        # Fall back to in-memory store
        if not github_config and customer_id in integrations_store:
            github_config = integrations_store[customer_id].get('github')
            argocd_config = integrations_store[customer_id].get('argocd')
        
        # Step 2: Delete ArgoCD applications
        if k8s_available:
            try:
                from kubernetes import client
                custom_api = client.CustomObjectsApi()
                
                for env in ['dev', 'preprod', 'prod']:
                    app_name = f"{customer_id}-{env}"
                    try:
                        custom_api.delete_namespaced_custom_object(
                            group="argoproj.io",
                            version="v1alpha1",
                            namespace="argocd",
                            plural="applications",
                            name=app_name
                        )
                        result['deleted']['argocd_apps'].append(app_name)
                    except Exception as e:
                        if '404' not in str(e):  # Ignore if doesn't exist
                            result['errors'].append(f'Failed to delete ArgoCD app {app_name}: {e}')
            except Exception as e:
                result['errors'].append(f'ArgoCD deletion error: {e}')
        
        # Step 3: Delete K8s namespaces
        if k8s_available:
            try:
                for env in ['dev', 'preprod', 'prod']:
                    namespace_name = f"{customer_id}-{env}"
                    try:
                        v1.delete_namespace(namespace_name)
                        result['deleted']['k8s_namespaces'].append(namespace_name)
                    except Exception as e:
                        if '404' not in str(e):  # Ignore if doesn't exist
                            result['errors'].append(f'Failed to delete namespace {namespace_name}: {e}')
            except Exception as e:
                result['errors'].append(f'K8s namespace deletion error: {e}')
        
        # Step 4: Archive or delete GitHub repository
        if github_config:
            try:
                import requests
                
                org = github_config.get('org')
                repo = github_config.get('repo')
                token = github_config.get('token')
                
                if delete_repo:
                    # Permanently delete repository
                    delete_url = f"https://api.github.com/repos/{org}/{repo}"
                    delete_response = requests.delete(delete_url, headers={
                        'Authorization': f"token {token}",
                        'Accept': 'application/vnd.github.v3+json'
                    })
                    
                    if delete_response.ok or delete_response.status_code == 404:
                        result['deleted']['github_repo'] = f'Deleted: {org}/{repo}'
                    else:
                        result['errors'].append(f'Failed to delete repo: {delete_response.json().get("message", "Unknown error")}')
                else:
                    # Archive repository (safer)
                    archive_url = f"https://api.github.com/repos/{org}/{repo}"
                    archive_response = requests.patch(archive_url, json={'archived': True}, headers={
                        'Authorization': f"token {token}",
                        'Accept': 'application/vnd.github.v3+json'
                    })
                    
                    if archive_response.ok:
                        result['deleted']['github_repo'] = f'Archived: {org}/{repo}'
                    else:
                        result['errors'].append(f'Failed to archive repo: {archive_response.json().get("message", "Unknown error")}')
            except Exception as e:
                result['errors'].append(f'GitHub repo deletion error: {e}')
        
        # Step 5: Delete integrations from database
        if db_available:
            try:
                deleted_count = db.query(Integration).filter(
                    Integration.customer_id == customer_id
                ).delete()
                
                result['deleted']['integrations'] = [f'{deleted_count} integrations']
                db.commit()
            except Exception as e:
                db.rollback()
                result['errors'].append(f'Database integration deletion failed: {e}')
        
        # Step 6: Delete customer record from database
        if db_available:
            try:
                customer = db.query(Customer).filter(Customer.id == customer_id).first()
                if customer:
                    db.delete(customer)
                    db.commit()
                    result['deleted']['database_record'] = True
                else:
                    result['errors'].append('Customer record not found in database')
            except Exception as e:
                db.rollback()
                result['errors'].append(f'Database customer deletion failed: {e}')
        
        # Step 7: Remove from in-memory store
        if customer_id in integrations_store:
            del integrations_store[customer_id]
            save_integrations()
        
        # Determine overall success
        result['success'] = len(result['errors']) == 0
        
        return result
        
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})
@app.get("/deployments")
def get_deployments():
    """Get all deployments across all customer namespaces and environments - dynamically discovered"""
    if not k8s_available:
        return {'error': 'K8s not available', 'deployments': [], 'total': 0}
    
    deployments = []
    
    # Discover all customer namespaces dynamically
    try:
        all_namespaces = v1.list_namespace()
        
        for ns_obj in all_namespaces.items:
            ns_name = ns_obj.metadata.name
            labels = ns_obj.metadata.labels or {}
            
            # Check if this is a customer namespace
            customer_id = None
            env = None
            
            if 'customer' in labels and 'environment' in labels:
                # Namespace created by OpenLuffy (has our labels)
                customer_id = labels['customer']
                env = labels['environment']
            elif '-dev' in ns_name or '-preprod' in ns_name or '-prod' in ns_name:
                # Legacy namespace (pattern-based: customer-id-env)
                if ns_name.endswith('-dev'):
                    customer_id = ns_name.replace('-dev', '')
                    env = 'dev'
                elif ns_name.endswith('-preprod'):
                    customer_id = ns_name.replace('-preprod', '')
                    env = 'preprod'
                elif ns_name.endswith('-prod'):
                    customer_id = ns_name.replace('-prod', '')
                    env = 'prod'
            
            if customer_id and env:
                # Get deployments from this namespace
                try:
                    deploys = apps_v1.list_namespaced_deployment(ns_name)
                    
                    for deploy in deploys.items:
                        name = deploy.metadata.name
                        replicas = deploy.status.replicas or 0
                        ready = deploy.status.ready_replicas or 0
                        
                        deployments.append({
                            'id': f"{ns_name}-{name}",
                            'name': name,
                            'namespace': ns_name,
                            'customer': customer_id,
                            'environment': env,
                            'replicas': replicas,
                            'ready': ready,
                            'status': 'running' if ready == replicas and ready > 0 else 'degraded',
                            'image': deploy.spec.template.spec.containers[0].image
                        })
                except ApiException as e:
                    # Namespace exists but no deployments or access denied
                    pass
    
    except Exception as e:
        print(f"Error discovering deployments: {e}")
    
    return {'deployments': deployments, 'total': len(deployments)}

# Integration models
class IntegrationConfig(BaseModel):
    id: str
    name: str
    config: Dict[str, Any]

@app.get("/integrations")
def get_integrations():
    """Get all configured integrations"""
    integrations = []
    
    # Always include K8s (it's available if we're running in K8s)
    if k8s_available:
        try:
            deploys = apps_v1.list_deployment_for_all_namespaces()
            pod_count = sum(d.status.replicas or 0 for d in deploys.items)
            
            integrations.append({
                'id': 'kubernetes',
                'name': 'Kubernetes',
                'icon': '☸️',
                'status': 'healthy',
                'statusText': 'Cluster healthy',
                'metrics': {
                    'Deployments': len(deploys.items),
                    'Pods': f'{pod_count} running',
                    'Cluster': 'K3s on Pi5'
                }
            })
        except:
            pass
    
    # Check for ArgoCD (check if ingress exists)
    integrations.append({
        'id': 'argocd',
        'name': 'ArgoCD',
        'icon': '🐙',
        'status': 'connected',
        'statusText': 'Connected',
        'metrics': {
            'Status': 'Ready',
            'URL': 'http://argocd.local'
        }
    })
    
    # Check for GitHub (always available)
    integrations.append({
        'id': 'github',
        'name': 'GitHub',
        'icon': '⚙️',
        'status': 'connected',
        'statusText': 'Connected',
        'metrics': {
            'Repository': 'lebrick07/openluffy',
            'Status': 'Active'
        }
    })
    
    # Add any configured integrations from store
    for int_id, int_config in integrations_store.items():
        integrations.append({
            'id': int_id,
            'name': int_config.get('name', int_id),
            'status': 'connected',
            'statusText': 'Configured',
            'config_exists': True
        })
    
    return {'integrations': integrations, 'total': len(integrations)}

@app.post("/integrations")
def save_integration(integration: IntegrationConfig):
    """Save integration configuration"""
    # TODO: Validate credentials by testing API connection
    # TODO: Store encrypted in K8s secrets instead of memory
    
    integrations_store[integration.id] = {
        'name': integration.name,
        'config': integration.config
    }
    
    return {
        'success': True,
        'message': f'{integration.name} integration configured',
        'id': integration.id
    }

@app.delete("/integrations/{integration_id}")
def delete_integration(integration_id: str):
    """Remove integration configuration"""
    if integration_id in integrations_store:
        del integrations_store[integration_id]
        return {'success': True, 'message': 'Integration removed'}
    
    raise HTTPException(status_code=404, detail='Integration not found')

@app.get("/integrations/{integration_id}/status")
def get_integration_status(integration_id: str):
    """Get real-time status for a specific integration"""
    # TODO: Implement real API calls to each service
    
    if integration_id == 'kubernetes' and k8s_available:
        try:
            nodes = v1.list_node()
            pods = v1.list_pod_for_all_namespaces()
            
            return {
                'id': 'kubernetes',
                'status': 'healthy',
                'metrics': {
                    'Nodes': len(nodes.items),
                    'Pods': len(pods.items),
                    'Namespaces': len(set(p.metadata.namespace for p in pods.items))
                }
            }
        except:
            return {'id': 'kubernetes', 'status': 'error', 'error': 'Failed to connect'}
    
    elif integration_id == 'argocd':
        # TODO: Call ArgoCD API
        return {
            'id': 'argocd',
            'status': 'connected',
            'message': 'API integration coming soon'
        }
    
    elif integration_id == 'github':
        # TODO: Call GitHub API
        return {
            'id': 'github',
            'status': 'connected',
            'message': 'API integration coming soon'
        }
    
    elif integration_id in integrations_store:
        return {
            'id': integration_id,
            'status': 'connected',
            'configured': True
        }
    
    raise HTTPException(status_code=404, detail='Integration not found')

# Deep deployment insights
@app.get("/deployments/{deployment_id}/details")
def get_deployment_details(deployment_id: str):
    """Get deep insights into a specific deployment"""
    if not k8s_available:
        return {'error': 'K8s not available'}
    
    # Parse deployment_id (format: namespace-deploymentname)
    parts = deployment_id.rsplit('-', 1)
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail='Invalid deployment ID format')
    
    namespace = '-'.join(parts[:-1])
    deployment_name = parts[-1]
    
    try:
        # Get deployment details
        deployment = apps_v1.read_namespaced_deployment(deployment_name, namespace)
        
        # Get pods for this deployment
        label_key = list(deployment.spec.selector.match_labels.keys())[0]
        label_value = deployment.spec.selector.match_labels[label_key]
        pods = v1.list_namespaced_pod(
            namespace,
            label_selector=f"{label_key}={label_value}"
        )
        
        # Get recent events
        events = v1.list_namespaced_event(namespace)
        deployment_events = []
        for event in events.items[-20:]:  # Last 20 events
            if deployment_name in str(event.involved_object.name):
                deployment_events.append({
                    'timestamp': event.last_timestamp.isoformat() if event.last_timestamp else str(event.first_timestamp),
                    'type': event.type,
                    'reason': event.reason,
                    'message': event.message
                })
        
        # Build pod details
        pod_details = []
        for pod in pods.items:
            pod_info = {
                'name': pod.metadata.name,
                'status': pod.status.phase,
                'ip': pod.status.pod_ip,
                'node': pod.spec.node_name,
                'restarts': sum(c.restart_count for c in (pod.status.container_statuses or [])),
                'age': str(pod.metadata.creation_timestamp) if pod.metadata.creation_timestamp else None,
                'containers': []
            }
            
            # Container details
            if pod.status.container_statuses:
                for container in pod.status.container_statuses:
                    pod_info['containers'].append({
                        'name': container.name,
                        'ready': container.ready,
                        'restarts': container.restart_count,
                        'image': container.image
                    })
            
            pod_details.append(pod_info)
        
        return {
            'deployment': {
                'name': deployment.metadata.name,
                'namespace': deployment.metadata.namespace,
                'replicas': {
                    'desired': deployment.spec.replicas,
                    'current': deployment.status.replicas or 0,
                    'ready': deployment.status.ready_replicas or 0,
                    'available': deployment.status.available_replicas or 0,
                    'unavailable': deployment.status.unavailable_replicas or 0
                },
                'strategy': deployment.spec.strategy.type if deployment.spec.strategy else 'Unknown',
                'created': str(deployment.metadata.creation_timestamp) if deployment.metadata.creation_timestamp else None
            },
            'pods': pod_details,
            'events': deployment_events[:10],  # Last 10 events
            'image': deployment.spec.template.spec.containers[0].image if deployment.spec.template.spec.containers else None
        }
    except ApiException as e:
        raise HTTPException(status_code=404, detail=f'Deployment not found: {str(e)}')

@app.get("/deployments/{deployment_id}/pods/{pod_name}/logs")
def get_pod_logs(deployment_id: str, pod_name: str, lines: int = 100, container: Optional[str] = None):
    """Get logs from a specific pod"""
    if not k8s_available:
        return {'error': 'K8s not available'}
    
    parts = deployment_id.rsplit('-', 1)
    namespace = '-'.join(parts[:-1])
    
    try:
        logs = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            tail_lines=lines,
            container=container
        )
        
        return {
            'pod': pod_name,
            'namespace': namespace,
            'container': container or 'default',
            'lines': lines,
            'logs': logs
        }
    except ApiException as e:
        raise HTTPException(status_code=404, detail=f'Pod logs not found: {str(e)}')

@app.get("/deployments/{deployment_id}/events")
def get_deployment_events(deployment_id: str, limit: int = 50):
    """Get all events for a deployment"""
    if not k8s_available:
        return {'error': 'K8s not available'}
    
    parts = deployment_id.rsplit('-', 1)
    namespace = '-'.join(parts[:-1])
    deployment_name = parts[-1]
    
    try:
        events = v1.list_namespaced_event(namespace)
        
        deployment_events = []
        for event in events.items:
            if deployment_name in str(event.involved_object.name):
                deployment_events.append({
                    'timestamp': str(event.last_timestamp if event.last_timestamp else event.first_timestamp),
                    'type': event.type,
                    'reason': event.reason,
                    'message': event.message,
                    'count': event.count,
                    'object': event.involved_object.name
                })
        
        # Sort by timestamp descending
        deployment_events.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            'deployment': deployment_id,
            'namespace': namespace,
            'events': deployment_events[:limit],
            'total': len(deployment_events)
        }
    except ApiException as e:
        raise HTTPException(status_code=404, detail=f'Events not found: {str(e)}')

# Helper to parse deployment ID
def parse_deployment_id(deployment_id: str):
    """Parse deployment_id to extract namespace and deployment name
    Format: {namespace}-{deployment-name}
    Challenge: both can contain hyphens
    
    Solution: Look up in deployments list to get the actual mapping
    """
    # Get all deployments to find the match
    if not k8s_available:
        return None, None
    
    # Try to find the deployment in our list
    customers = ['acme-corp', 'techstart', 'widgetco']
    environments = ['dev', 'preprod', 'prod']
    
    for customer in customers:
        for env in environments:
            ns = f"{customer}-{env}"
            try:
                deploys = apps_v1.list_namespaced_deployment(ns)
                for deploy in deploys.items:
                    expected_id = f"{ns}-{deploy.metadata.name}"
                    if expected_id == deployment_id:
                        return ns, deploy.metadata.name
            except:
                continue
    
    return None, None

@app.get("/deployments/{deployment_id}/details-v2")
def get_deployment_details_v2(deployment_id: str):
    """Get deep insights - improved version with better ID parsing"""
    if not k8s_available:
        return {'error': 'K8s not available'}
    
    namespace, deployment_name = parse_deployment_id(deployment_id)
    
    if not namespace or not deployment_name:
        raise HTTPException(status_code=404, detail=f'Deployment not found: {deployment_id}')
    
    try:
        # Get deployment details
        deployment = apps_v1.read_namespaced_deployment(deployment_name, namespace)
        
        # Get pods
        label_key = list(deployment.spec.selector.match_labels.keys())[0]
        label_value = deployment.spec.selector.match_labels[label_key]
        pods = v1.list_namespaced_pod(namespace, label_selector=f"{label_key}={label_value}")
        
        # Get events
        events = v1.list_namespaced_event(namespace)
        deployment_events = []
        for event in events.items[-20:]:
            if deployment_name in str(event.involved_object.name):
                deployment_events.append({
                    'timestamp': str(event.last_timestamp or event.first_timestamp),
                    'type': event.type,
                    'reason': event.reason,
                    'message': event.message
                })
        
        # Build pod details
        pod_details = []
        for pod in pods.items:
            pod_info = {
                'name': pod.metadata.name,
                'status': pod.status.phase,
                'ip': pod.status.pod_ip,
                'node': pod.spec.node_name,
                'restarts': sum(c.restart_count for c in (pod.status.container_statuses or [])),
                'age': str(pod.metadata.creation_timestamp),
                'containers': []
            }
            
            if pod.status.container_statuses:
                for container in pod.status.container_statuses:
                    pod_info['containers'].append({
                        'name': container.name,
                        'ready': container.ready,
                        'restarts': container.restart_count,
                        'image': container.image
                    })
            
            pod_details.append(pod_info)
        
        return {
            'deployment': {
                'id': deployment_id,
                'name': deployment.metadata.name,
                'namespace': deployment.metadata.namespace,
                'replicas': {
                    'desired': deployment.spec.replicas,
                    'current': deployment.status.replicas or 0,
                    'ready': deployment.status.ready_replicas or 0,
                    'available': deployment.status.available_replicas or 0
                },
                'strategy': deployment.spec.strategy.type if deployment.spec.strategy else 'Unknown',
                'created': str(deployment.metadata.creation_timestamp)
            },
            'pods': pod_details,
            'events': deployment_events[:10],
            'image': deployment.spec.template.spec.containers[0].image if deployment.spec.template.spec.containers else None
        }
    except ApiException as e:
        raise HTTPException(status_code=404, detail=f'Error: {str(e)}')

@app.post("/customers/{customer_id}/promote-to-prod")
def promote_to_production(customer_id: str):
    """Promote preprod deployment to production"""
    if not k8s_available:
        return {'error': 'K8s not available'}
    
    try:
        # Import kubernetes dynamic client for patching
        from kubernetes import dynamic
        from kubernetes.client import api_client
        
        dyn_client = dynamic.DynamicClient(
            api_client.ApiClient()
        )
        
        # Get ArgoCD Application API
        api = dyn_client.resources.get(api_version="argoproj.io/v1alpha1", kind="Application")
        
        # Get preprod app to find current revision
        preprod_app_name = f"{customer_id}-preprod"
        preprod_app = api.get(name=preprod_app_name, namespace="argocd")
        
        # Get current revision/commit from preprod
        current_revision = preprod_app.spec.source.targetRevision
        
        # Update prod app to sync to same revision
        prod_app_name = f"{customer_id}-prod"
        
        # Patch the prod application to sync
        patch = {
            "operation": {
                "sync": {
                    "revision": current_revision
                }
            }
        }
        
        # Trigger sync on prod app
        prod_app = api.get(name=prod_app_name, namespace="argocd")
        
        # For now, just return success - actual sync happens via ArgoCD
        # In production, this would call ArgoCD API directly
        
        return {
            'success': True,
            'customer': customer_id,
            'message': f'Production deployment initiated for {customer_id}',
            'preprod_revision': current_revision,
            'prod_app': prod_app_name,
            'note': 'Sync ArgoCD prod application manually or via ArgoCD API'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Promotion failed: {str(e)}')

@app.get("/customers/{customer_id}/approval-status")
def get_approval_status(customer_id: str):
    """Check if customer has pending production approval"""
    if not k8s_available:
        return {'error': 'K8s not available'}
    
    try:
        # Check preprod vs prod status
        preprod_ns = f"{customer_id}-preprod"
        prod_ns = f"{customer_id}-prod"
        
        preprod_deploys = apps_v1.list_namespaced_deployment(preprod_ns)
        prod_deploys = apps_v1.list_namespaced_deployment(prod_ns)
        
        if not preprod_deploys.items or not prod_deploys.items:
            return {
                'customer': customer_id,
                'approval_needed': False,
                'reason': 'No deployments found'
            }
        
        preprod_deploy = preprod_deploys.items[0]
        prod_deploy = prod_deploys.items[0]
        
        preprod_image = preprod_deploy.spec.template.spec.containers[0].image
        prod_image = prod_deploy.spec.template.spec.containers[0].image
        
        # If images differ, approval might be needed
        approval_needed = preprod_image != prod_image
        
        return {
            'customer': customer_id,
            'approval_needed': approval_needed,
            'preprod': {
                'image': preprod_image,
                'ready': preprod_deploy.status.ready_replicas or 0,
                'replicas': preprod_deploy.spec.replicas
            },
            'prod': {
                'image': prod_image,
                'ready': prod_deploy.status.ready_replicas or 0,
                'replicas': prod_deploy.spec.replicas
            }
        }
        
    except Exception as e:
        return {
            'customer': customer_id,
            'approval_needed': False,
            'error': str(e)
        }

@app.get("/approvals/pending")
def get_pending_approvals():
    """Get all customers with pending production approvals"""
    if not k8s_available:
        return {'approvals': [], 'total': 0}
    
    customers = ['acme-corp', 'techstart', 'widgetco']
    pending = []
    
    for customer in customers:
        status = get_approval_status(customer)
        if status.get('approval_needed'):
            pending.append({
                'customer_id': customer,
                'customer_name': customer.replace('-', ' ').title(),
                'preprod_image': status['preprod']['image'],
                'prod_image': status['prod']['image'],
                'preprod_ready': status['preprod']['ready'],
                'prod_ready': status['prod']['ready']
            })
    
    return {
        'approvals': pending,
        'total': len(pending)
    }

# GitHub Actions Integration
CUSTOMER_REPOS = {
    'acme-corp': 'lebrick07/acme-corp-api',
    'techstart': 'lebrick07/techstart-webapp',
    'widgetco': 'lebrick07/widgetco-api'
}

@app.get("/deployments/{deployment_id}/pipeline")
async def get_deployment_pipeline(deployment_id: str):
    """Get GitHub Actions pipeline runs for a deployment"""
    # Parse deployment_id (format: namespace-app where namespace=customer-env)
    # Example: acme-corp-dev-acme-corp-api
    # Extract namespace (everything before the last app name)
    parts = deployment_id.split('-')
    
    # Try to find environment in the ID
    env_index = -1
    for i, part in enumerate(parts):
        if part in ['dev', 'preprod', 'prod']:
            env_index = i
            break
    
    if env_index == -1:
        return {'runs': [], 'total': 0, 'error': 'Could not parse environment from deployment ID'}
    
    customer = '-'.join(parts[:env_index])
    environment = parts[env_index]
    
    # Get GitHub repo
    repo = CUSTOMER_REPOS.get(customer)
    if not repo:
        return {'runs': [], 'total': 0, 'error': f'No repo mapping for {customer}'}
    
    # Fetch workflow runs from GitHub API
    github_token = os.getenv('GITHUB_TOKEN', '')
    headers = {
        'Accept': 'application/vnd.github.v3+json'
    }
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'https://api.github.com/repos/{repo}/actions/runs',
                headers=headers,
                params={'per_page': 10, 'page': 1}
            )
            
            if response.status_code == 200:
                data = response.json()
                runs = []
                
                for run in data.get('workflow_runs', []):
                    runs.append({
                        'id': run['id'],
                        'name': run['name'],
                        'status': run['status'],
                        'conclusion': run['conclusion'],
                        'branch': run['head_branch'],
                        'commit_sha': run['head_sha'][:7],
                        'commit_message': run.get('head_commit', {}).get('message', '').split('\n')[0],
                        'author': run.get('head_commit', {}).get('author', {}).get('name', 'Unknown'),
                        'created_at': run['created_at'],
                        'updated_at': run['updated_at'],
                        'duration': None,  # Calculate if completed
                        'url': run['html_url'],
                        'jobs_url': run['jobs_url']
                    })
                    
                    # Calculate duration for completed runs
                    if run['status'] == 'completed' and run['created_at'] and run['updated_at']:
                        try:
                            created = datetime.fromisoformat(run['created_at'].replace('Z', '+00:00'))
                            updated = datetime.fromisoformat(run['updated_at'].replace('Z', '+00:00'))
                            duration_seconds = (updated - created).total_seconds()
                            runs[-1]['duration'] = int(duration_seconds)
                        except:
                            pass
                
                return {
                    'deployment_id': deployment_id,
                    'customer': customer,
                    'environment': environment,
                    'repo': repo,
                    'runs': runs,
                    'total': len(runs)
                }
            else:
                return {
                    'runs': [],
                    'total': 0,
                    'error': f'GitHub API returned {response.status_code}'
                }
                
    except Exception as e:
        return {
            'runs': [],
            'total': 0,
            'error': str(e)
        }

@app.get("/deployments/{deployment_id}/pipeline/{run_id}/jobs")
async def get_pipeline_jobs(deployment_id: str, run_id: int):
    """Get detailed jobs for a specific pipeline run"""
    parts = deployment_id.split('-')
    customer = '-'.join(parts[:-1]) if parts[-1] in ['dev', 'preprod', 'prod'] else parts[0]
    
    repo = CUSTOMER_REPOS.get(customer)
    if not repo:
        return {'jobs': [], 'error': f'No repo mapping for {customer}'}
    
    github_token = os.getenv('GITHUB_TOKEN', '')
    headers = {
        'Accept': 'application/vnd.github.v3+json'
    }
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f'https://api.github.com/repos/{repo}/actions/runs/{run_id}/jobs',
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                jobs = []
                
                for job in data.get('jobs', []):
                    steps = []
                    for step in job.get('steps', []):
                        steps.append({
                            'name': step['name'],
                            'status': step['status'],
                            'conclusion': step.get('conclusion'),
                            'number': step['number'],
                            'started_at': step.get('started_at'),
                            'completed_at': step.get('completed_at')
                        })
                    
                    jobs.append({
                        'id': job['id'],
                        'name': job['name'],
                        'status': job['status'],
                        'conclusion': job.get('conclusion'),
                        'started_at': job.get('started_at'),
                        'completed_at': job.get('completed_at'),
                        'steps': steps,
                        'url': job['html_url']
                    })
                
                return {
                    'run_id': run_id,
                    'jobs': jobs,
                    'total': len(jobs)
                }
            else:
                return {
                    'jobs': [],
                    'error': f'GitHub API returned {response.status_code}'
                }
    except Exception as e:
        return {
            'jobs': [],
            'error': str(e)
        }

@app.get("/pipelines/status")
async def get_all_pipelines_status():
    """Get pipeline status summary for all customers"""
    customers = {
        'acme-corp': 'lebrick07/acme-corp-api',
        'techstart': 'lebrick07/techstart-webapp',
        'widgetco': 'lebrick07/widgetco-api'
    }
    
    github_token = os.getenv('GITHUB_TOKEN', '')
    headers = {
        'Accept': 'application/vnd.github.v3+json'
    }
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    
    results = []
    
    try:
        async with httpx.AsyncClient() as client:
            for customer_id, repo in customers.items():
                try:
                    response = await client.get(
                        f'https://api.github.com/repos/{repo}/actions/runs',
                        headers=headers,
                        params={'per_page': 1, 'page': 1, 'branch': 'develop'}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        runs = data.get('workflow_runs', [])
                        
                        if runs:
                            latest = runs[0]
                            results.append({
                                'customer_id': customer_id,
                                'repo': repo,
                                'status': latest['status'],
                                'conclusion': latest.get('conclusion'),
                                'branch': latest['head_branch'],
                                'commit_sha': latest['head_sha'][:7],
                                'run_id': latest['id'],
                                'url': latest['html_url'],
                                'created_at': latest['created_at']
                            })
                        else:
                            results.append({
                                'customer_id': customer_id,
                                'repo': repo,
                                'status': 'no_runs',
                                'conclusion': None
                            })
                    else:
                        results.append({
                            'customer_id': customer_id,
                            'repo': repo,
                            'status': 'error',
                            'error': f'GitHub API returned {response.status_code}'
                        })
                except Exception as e:
                    results.append({
                        'customer_id': customer_id,
                        'repo': repo,
                        'status': 'error',
                        'error': str(e)
                    })
        
        return {
            'pipelines': results,
            'total': len(results)
        }
    except Exception as e:
        return {
            'pipelines': [],
            'error': str(e)
        }

# Customer Creation Endpoint
class CustomerCreate(BaseModel):
    name: str
    icon: str = "🏢"
    deploymentModel: str
    runtime: str
    cicdStyle: str
    environments: List[str]
    approvalStrategy: str
    observability: List[str]

@app.post("/customers/create")
async def create_customer(customer_data: CustomerCreate):
    """
    AI-powered customer creation
    Generates:
    - GitHub repository with templates
    - Multi-environment CI/CD pipeline
    - Kubernetes namespaces and manifests
    - ArgoCD applications
    - Ingresses with DNS
    """
    customer_id = customer_data.name.lower().replace(' ', '-').replace('.', '-')
    
    # TODO: Implement actual AI-powered generation
    # For now, return a simulated response
    return {
        "success": True,
        "customer": {
            "id": customer_id,
            "name": customer_data.name,
            "icon": customer_data.icon,
            "stack": customer_data.runtime,
            "deploymentModel": customer_data.deploymentModel,
            "environments": [
                {"environment": env, "status": "provisioning", "pods": {"running": 0, "total": 0}, "url": f"http://{customer_id}-{env}.local"}
                for env in customer_data.environments
            ],
            "overallStatus": "provisioning"
        },
        "message": f"Customer {customer_data.name} is being created. This will take 2-3 minutes.",
        "steps": [
            {"step": "create_github_repo", "status": "in_progress"},
            {"step": "generate_pipeline", "status": "pending"},
            {"step": "create_k8s_namespaces", "status": "pending"},
            {"step": "deploy_argocd_apps", "status": "pending"},
            {"step": "setup_ingress", "status": "pending"}
        ]
    }

# ==================== LUFFY AI AGENT ====================

class LuffyChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    history: Optional[List[Dict[str, str]]] = None

