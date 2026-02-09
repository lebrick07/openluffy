from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from kubernetes import client, config
from kubernetes.client.rest import ApiException

app = FastAPI(title="lebrickbot")

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
    return {"service": "lebrickbot", "status": "running", "version": "0.1.0"}

@app.get("/status")
def api_status():
    return {
        "service": "lebrickbot-backend",
        "status": "operational",
        "version": "0.1.0",
        "k8s": k8s_available
    }

@app.get("/customers")
def get_customers():
    """Get all customer deployments"""
    if not k8s_available:
        return {'error': 'K8s not available', 'customers': [], 'total': 0}
    
    customers = []
    
    # Acme Corp
    try:
        acme_pods = v1.list_namespaced_pod('acme-corp')
        acme_replicas = len([p for p in acme_pods.items if p.status.phase == 'Running'])
        acme_status = 'running' if acme_replicas > 0 else 'error'
    except:
        acme_replicas = 0
        acme_status = 'error'
    
    customers.append({
        'id': 'acme-corp',
        'name': 'Acme Corp',
        'app': 'acme-corp-api',
        'stack': 'Node.js',
        'status': acme_status,
        'replicas': acme_replicas,
        'namespace': 'acme-corp',
        'url': 'http://acme.local',
        'endpoints': ['/health', '/products', '/orders']
    })
    
    # TechStart
    try:
        techstart_pods = v1.list_namespaced_pod('techstart')
        techstart_replicas = len([p for p in techstart_pods.items if p.status.phase == 'Running'])
        techstart_status = 'running' if techstart_replicas > 0 else 'error'
    except:
        techstart_replicas = 0
        techstart_status = 'error'
    
    customers.append({
        'id': 'techstart',
        'name': 'TechStart Inc',
        'app': 'techstart-webapp',
        'stack': 'Python FastAPI',
        'status': techstart_status,
        'replicas': techstart_replicas,
        'namespace': 'techstart',
        'url': 'http://techstart.local',
        'endpoints': ['/health', '/metrics', '/analytics', '/users']
    })
    
    # WidgetCo
    try:
        widgetco_pods = v1.list_namespaced_pod('widgetco')
        widgetco_replicas = len([p for p in widgetco_pods.items if p.status.phase == 'Running'])
        widgetco_status = 'running' if widgetco_replicas > 0 else 'error'
    except:
        widgetco_replicas = 0
        widgetco_status = 'error'
    
    customers.append({
        'id': 'widgetco',
        'name': 'WidgetCo Manufacturing',
        'app': 'widgetco-api',
        'stack': 'Go',
        'status': widgetco_status,
        'replicas': widgetco_replicas,
        'namespace': 'widgetco',
        'url': 'http://widgetco.local',
        'endpoints': ['/health', '/inventory', '/suppliers']
    })
    
    return {'customers': customers, 'total': len(customers)}

@app.get("/deployments")
def get_deployments():
    """Get all deployments across all customer namespaces"""
    if not k8s_available:
        return {'error': 'K8s not available', 'deployments': [], 'total': 0}
    
    deployments = []
    namespaces = ['acme-corp', 'techstart', 'widgetco']
    
    for ns in namespaces:
        try:
            deploys = apps_v1.list_namespaced_deployment(ns)
            
            for deploy in deploys.items:
                name = deploy.metadata.name
                replicas = deploy.status.replicas or 0
                ready = deploy.status.ready_replicas or 0
                
                deployments.append({
                    'id': f"{ns}-{name}",
                    'name': name,
                    'namespace': ns,
                    'customer': ns.replace('-', ' ').title(),
                    'replicas': replicas,
                    'ready': ready,
                    'status': 'running' if ready == replicas and ready > 0 else 'degraded',
                    'image': deploy.spec.template.spec.containers[0].image
                })
        except ApiException:
            pass
    
    return {'deployments': deployments, 'total': len(deployments)}
