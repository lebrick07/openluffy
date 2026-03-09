"""
Project-scoped API endpoints for OpenLuffy v1.2

Implements project-based context isolation matching AWS/GCP/Azure patterns.
Each project (Control Plane or Customer Project) has isolated resources.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from database import SessionLocal
from database.models import Customer
import os

# Initialize router
router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


# Global K8s client (imported from main)
v1 = None
apps_v1 = None


def init_k8s_clients(core_v1, apps_v1_client):
    """Initialize Kubernetes clients from main.py"""
    global v1, apps_v1
    v1 = core_v1
    apps_v1 = apps_v1_client


@router.get("")
async def list_projects():
    """
    List all projects (customers) accessible from this OpenLuffy environment.
    
    Returns:
        control_plane: Special project for platform infrastructure
        customer_projects: List of customer workload projects
    """
    current_env = os.getenv('OPENLUFFY_ENV', 'dev').lower()
    
    db = SessionLocal()
    try:
        # Get all projects (customers) created from this environment
        customers = db.query(Customer).filter(
            (Customer.created_from_env == current_env) | (Customer.id == 'control-plane')
        ).all()
        
        control_plane = None
        customer_projects = []
        
        for customer in customers:
            project_data = customer.to_dict()
            
            if customer.project_type == 'control-plane':
                control_plane = project_data
            else:
                customer_projects.append(project_data)
        
        return {
            'control_plane': control_plane,
            'customer_projects': customer_projects,
            'total': len(customer_projects) + (1 if control_plane else 0)
        }
    finally:
        db.close()


@router.get("/{project_id}/applications")
async def list_project_applications(project_id: str, environment: Optional[str] = None):
    """
    List all applications (deployments) for a specific project.
    
    Args:
        project_id: Project ID (control-plane, trucks-inc, acme-corp, etc.)
        environment: Optional filter (dev, preprod, prod)
    
    Returns:
        List of applications with deployment info
        
    Raises:
        404: Project not found
        403: Access denied (if trying to access another environment's project)
    """
    if not v1 or not apps_v1:
        raise HTTPException(status_code=503, detail="Kubernetes not available")
    
    current_env = os.getenv('OPENLUFFY_ENV', 'dev').lower()
    
    # Validate project exists and is accessible
    db = SessionLocal()
    try:
        project = db.query(Customer).filter(Customer.id == project_id).first()
        
        if not project:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
        
        # Check access: control-plane is always accessible, customer projects only if created from this env
        if project.project_type != 'control-plane' and project.created_from_env != current_env:
            raise HTTPException(
                status_code=403, 
                detail=f"Project '{project_id}' not accessible from {current_env} environment"
            )
    finally:
        db.close()
    
    # Get deployments for this project
    applications = []
    
    try:
        all_namespaces = v1.list_namespace()
        
        for ns_obj in all_namespaces.items:
            ns_name = ns_obj.metadata.name
            labels = ns_obj.metadata.labels or {}
            
            # Determine if this namespace belongs to this project
            namespace_project_id = None
            namespace_env = None
            
            if project_id == 'control-plane':
                # Control Plane: only openluffy-{env} namespaces
                if ns_name == f'openluffy-{current_env}':
                    namespace_project_id = 'control-plane'
                    namespace_env = current_env
            else:
                # Customer Project: customer namespaces
                if 'customer' in labels and labels['customer'] == project_id:
                    namespace_project_id = labels['customer']
                    namespace_env = labels.get('environment')
                elif ns_name.startswith(f"{project_id}-"):
                    # Legacy pattern: project-id-env
                    for env_suffix in ['dev', 'preprod', 'prod']:
                        if ns_name == f"{project_id}-{env_suffix}":
                            namespace_project_id = project_id
                            namespace_env = env_suffix
                            break
            
            # Skip if namespace doesn't belong to this project
            if namespace_project_id != project_id:
                continue
            
            # Skip if environment filter provided and doesn't match
            if environment and namespace_env != environment:
                continue
            
            # Get deployments from this namespace
            try:
                deploys = apps_v1.list_namespaced_deployment(ns_name)
                
                for deploy in deploys.items:
                    name = deploy.metadata.name
                    replicas = deploy.status.replicas or 0
                    ready = deploy.status.ready_replicas or 0
                    available = deploy.status.available_replicas or 0
                    updated = deploy.status.updated_replicas or 0
                    
                    applications.append({
                        'id': f"{ns_name}-{name}",
                        'name': name,
                        'namespace': ns_name,
                        'project_id': project_id,
                        'environment': namespace_env,
                        'replicas': {
                            'desired': replicas,
                            'current': replicas,
                            'ready': ready,
                            'available': available,
                            'updated': updated
                        },
                        'status': 'running' if ready == replicas and ready > 0 else 'degraded',
                        'health': 'healthy' if ready == replicas and ready > 0 else 'degraded',
                        'image': deploy.spec.template.spec.containers[0].image if deploy.spec.template.spec.containers else None
                    })
            except Exception as e:
                print(f"Warning: Failed to list deployments in {ns_name}: {e}")
                continue
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list applications: {str(e)}")
    
    return {
        'project_id': project_id,
        'environment_filter': environment,
        'applications': applications,
        'total': len(applications)
    }


@router.get("/{project_id}/applications/{deployment_id}")
async def get_project_application_detail(project_id: str, deployment_id: str):
    """
    Get detailed information for a specific application within a project.
    
    Args:
        project_id: Project ID
        deployment_id: Deployment ID (format: namespace-deployment-name)
    
    Returns:
        Detailed application information
        
    Raises:
        404: Project or application not found
        403: Application doesn't belong to this project
    """
    if not v1 or not apps_v1:
        raise HTTPException(status_code=503, detail="Kubernetes not available")
    
    current_env = os.getenv('OPENLUFFY_ENV', 'dev').lower()
    
    # Validate project exists
    db = SessionLocal()
    try:
        project = db.query(Customer).filter(Customer.id == project_id).first()
        
        if not project:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
        
        # Check access
        if project.project_type != 'control-plane' and project.created_from_env != current_env:
            raise HTTPException(status_code=403, detail=f"Project '{project_id}' not accessible")
    finally:
        db.close()
    
    # Parse deployment_id (format: namespace-deployment-name)
    try:
        namespace, deployment_name = deployment_id.rsplit('-', 1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid deployment_id format")
    
    # Verify deployment belongs to this project
    try:
        # Get namespace to verify project ownership
        ns = v1.read_namespace(namespace)
        labels = ns.metadata.labels or {}
        
        # Check if namespace belongs to this project
        namespace_project_id = None
        
        if project_id == 'control-plane':
            if namespace == f'openluffy-{current_env}':
                namespace_project_id = 'control-plane'
        else:
            if 'customer' in labels and labels['customer'] == project_id:
                namespace_project_id = labels['customer']
            elif namespace.startswith(f"{project_id}-"):
                namespace_project_id = project_id
        
        if namespace_project_id != project_id:
            raise HTTPException(
                status_code=403, 
                detail=f"Application '{deployment_id}' does not belong to project '{project_id}'"
            )
        
        # Get deployment details
        deploy = apps_v1.read_namespaced_deployment(deployment_name, namespace)
        
        # Get pods for this deployment
        pods = v1.list_namespaced_pod(namespace, label_selector=f"app={deployment_name}")
        
        pod_list = []
        for pod in pods.items:
            pod_list.append({
                'name': pod.metadata.name,
                'status': pod.status.phase,
                'ip': pod.status.pod_ip,
                'node': pod.spec.node_name,
                'restarts': sum(cs.restart_count for cs in pod.status.container_statuses) if pod.status.container_statuses else 0,
                'age': str(pod.metadata.creation_timestamp) if pod.metadata.creation_timestamp else None
            })
        
        replicas = deploy.status.replicas or 0
        ready = deploy.status.ready_replicas or 0
        
        return {
            'project_id': project_id,
            'deployment_id': deployment_id,
            'name': deployment_name,
            'namespace': namespace,
            'replicas': {
                'desired': replicas,
                'current': replicas,
                'ready': ready,
                'available': deploy.status.available_replicas or 0,
                'updated': deploy.status.updated_replicas or 0
            },
            'status': 'running' if ready == replicas and ready > 0 else 'degraded',
            'health': 'healthy' if ready == replicas and ready > 0 else 'degraded',
            'image': deploy.spec.template.spec.containers[0].image if deploy.spec.template.spec.containers else None,
            'strategy': deploy.spec.strategy.type if deploy.spec.strategy else 'RollingUpdate',
            'pods': pod_list,
            'created': str(deploy.metadata.creation_timestamp) if deploy.metadata.creation_timestamp else None
        }
        
    except Exception as e:
        if "NotFound" in str(e):
            raise HTTPException(status_code=404, detail=f"Application '{deployment_id}' not found")
        raise HTTPException(status_code=500, detail=f"Failed to get application details: {str(e)}")
