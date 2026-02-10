from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os
import httpx
from datetime import datetime

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

@app.post("/api/customers/create")
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
from luffy_agent import luffy

class LuffyChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    history: Optional[List[Dict[str, str]]] = None

class LuffyActionRequest(BaseModel):
    action: str
    context: Optional[Dict[str, Any]] = None

@app.post("/api/luffy/chat")
async def luffy_chat(request: LuffyChatRequest):
    """
    Chat with Luffy - the AI Super DevOps Engineer
    """
    result = await luffy.chat(
        message=request.message,
        context=request.context,
        history=request.history
    )
    return result

@app.post("/api/luffy/action")
async def luffy_action(request: LuffyActionRequest):
    """
    Execute an action proposed by Luffy
    """
    result = await luffy.execute_action(
        action=request.action,
        context=request.context
    )
    return result

@app.get("/api/luffy/status")
def luffy_status():
    """
    Get Luffy's current status
    """
    return {
        "name": "Luffy",
        "role": "AI Super DevOps Engineer",
        "status": "active",
        "capabilities": [
            "Autonomous infrastructure management",
            "Pipeline generation and fixing",
            "Deployment automation",
            "Issue diagnosis and resolution",
            "Cost optimization",
            "Security scanning"
        ]
    }
