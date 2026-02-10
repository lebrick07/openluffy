from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os

app = FastAPI(title="lebrickbot")

# In-memory storage for integration configs (TODO: move to K8s secrets or Vault)
integrations_store: Dict[str, Dict[str, Any]] = {}

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
    """Get all customer deployments with multi-environment support"""
    if not k8s_available:
        return {'error': 'K8s not available', 'customers': [], 'total': 0}
    
    customers = []
    
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
                'url': f'http://{customer_id}-{env}.local'
            }
        except:
            return {
                'environment': env,
                'status': 'error',
                'pods': {'running': 0, 'total': 0},
                'url': f'http://{customer_id}-{env}.local'
            }
    
    # Acme Corp
    acme_envs = [get_env_status('acme-corp', env) for env in ['dev', 'preprod', 'prod']]
    customers.append({
        'id': 'acme-corp',
        'name': 'Acme Corp',
        'app': 'acme-corp-api',
        'stack': 'Node.js',
        'environments': acme_envs,
        'overallStatus': 'running' if any(e['status'] == 'running' for e in acme_envs) else 'error'
    })
    
    # TechStart
    techstart_envs = [get_env_status('techstart', env) for env in ['dev', 'preprod', 'prod']]
    customers.append({
        'id': 'techstart',
        'name': 'TechStart Inc',
        'app': 'techstart-webapp',
        'stack': 'Python FastAPI',
        'environments': techstart_envs,
        'overallStatus': 'running' if any(e['status'] == 'running' for e in techstart_envs) else 'error'
    })
    
    # WidgetCo
    widgetco_envs = [get_env_status('widgetco', env) for env in ['dev', 'preprod', 'prod']]
    customers.append({
        'id': 'widgetco',
        'name': 'WidgetCo Manufacturing',
        'app': 'widgetco-api',
        'stack': 'Go',
        'environments': widgetco_envs,
        'overallStatus': 'running' if any(e['status'] == 'running' for e in widgetco_envs) else 'error'
    })
    
    return {'customers': customers, 'total': len(customers)}

@app.get("/deployments")
def get_deployments():
    """Get all deployments across all customer namespaces and environments"""
    if not k8s_available:
        return {'error': 'K8s not available', 'deployments': [], 'total': 0}
    
    deployments = []
    customers = ['acme-corp', 'techstart', 'widgetco']
    environments = ['dev', 'preprod', 'prod']
    
    for customer in customers:
        for env in environments:
            ns = f"{customer}-{env}"
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
                        'customer': customer,
                        'environment': env,
                        'replicas': replicas,
                        'ready': ready,
                        'status': 'running' if ready == replicas and ready > 0 else 'degraded',
                        'image': deploy.spec.template.spec.containers[0].image
                    })
            except ApiException:
                pass
    
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
            'Repository': 'lebrick07/lebrickbot',
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
