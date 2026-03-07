"""
Deployment action endpoints: deploy, rollback, scale, restart

Provides REST API endpoints for managing application deployments:
- POST /api/v1/deployments/{deployment_id}/deploy - Trigger ArgoCD sync
- POST /api/v1/deployments/{deployment_id}/rollback - Rollback to previous revision
- POST /api/v1/deployments/{deployment_id}/scale - Scale replicas
- POST /api/v1/deployments/{deployment_id}/restart - Restart pods
- GET /api/v1/deployments/{deployment_id}/sync-status - Get ArgoCD sync status

All endpoints require authentication (future: permission checks).
"""
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from kubernetes import client
from typing import Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from database import get_db
from argocd_client import argocd_client


# ============================================================================
# Request Models
# ============================================================================

class DeployRequest(BaseModel):
    """Request model for deploy action"""
    revision: str = Field(default="HEAD", description="Git revision to deploy")


class RollbackRequest(BaseModel):
    """Request model for rollback action"""
    to_revision: str = Field(
        default="previous", 
        description="Target revision: 'previous' or specific SHA"
    )


class ScaleRequest(BaseModel):
    """Request model for scale action"""
    replicas: int = Field(..., ge=0, le=20, description="Number of replicas (0-20)")


# ============================================================================
# Response Models
# ============================================================================

class ActionResponse(BaseModel):
    """Standard response model for all deployment actions"""
    success: bool
    message: str
    data: Dict[str, Any] = {}


# ============================================================================
# Helper Functions
# ============================================================================

def parse_deployment_id(deployment_id: str) -> tuple:
    """
    Parse deployment_id into customer_id and environment
    
    Format: {customer-id}-{environment}
    Example: acme-corp-dev → ("acme-corp", "dev")
    
    Args:
        deployment_id: Deployment identifier string
        
    Returns:
        Tuple of (customer_id, environment)
        
    Raises:
        HTTPException: If deployment_id format is invalid
    """
    parts = deployment_id.rsplit('-', 1)
    if len(parts) != 2:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid deployment_id format. Expected: customer-environment, got: {deployment_id}"
        )
    return parts[0], parts[1]


def check_customer_access(customer_id: str, user_id: str, db: Session):
    """
    Verify user has access to customer
    
    TODO: Implement real permission check via groups/permissions tables
    
    Args:
        customer_id: Customer identifier
        user_id: User identifier
        db: Database session
        
    Raises:
        HTTPException: If user doesn't have access
    """
    # For MVP, allow all authenticated users
    # In production: query UserCustomerAccess or GroupCustomerAccess tables
    pass


# ============================================================================
# Deployment Action Endpoints
# ============================================================================

async def deploy_application(
    deployment_id: str,
    request: DeployRequest,
    db: Session = Depends(get_db)
) -> ActionResponse:
    """
    POST /api/v1/deployments/{deployment_id}/deploy
    
    Trigger ArgoCD sync to deploy latest or specific revision
    
    Args:
        deployment_id: Deployment identifier (format: customer-environment)
        request: Deploy request with revision
        db: Database session
        
    Returns:
        ActionResponse with deployment details
        
    Raises:
        HTTPException: If deployment fails
    """
    try:
        customer_id, environment = parse_deployment_id(deployment_id)
        app_name = f"{customer_id}-{environment}"
        
        # TODO: Check permissions
        # check_customer_access(customer_id, current_user_id, db)
        
        # Trigger ArgoCD sync
        result = await argocd_client.sync_application(app_name, revision=request.revision)
        
        # Log action (audit trail)
        print(f"🚀 Deploy triggered: {app_name} @ {request.revision} at {datetime.utcnow()}")
        # TODO: Write to audit log table
        
        return ActionResponse(
            success=True,
            message=f"Deployment triggered for {app_name}",
            data={
                "app_name": app_name,
                "customer_id": customer_id,
                "environment": environment,
                "revision": request.revision,
                "argocd_response": result
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Deploy failed: {str(e)}"
        )


async def rollback_application(
    deployment_id: str,
    request: RollbackRequest,
    db: Session = Depends(get_db)
) -> ActionResponse:
    """
    POST /api/v1/deployments/{deployment_id}/rollback
    
    Rollback to previous or specific revision
    
    Args:
        deployment_id: Deployment identifier
        request: Rollback request with target revision
        db: Database session
        
    Returns:
        ActionResponse with rollback details
        
    Raises:
        HTTPException: If rollback fails
    """
    try:
        customer_id, environment = parse_deployment_id(deployment_id)
        app_name = f"{customer_id}-{environment}"
        
        # Determine target revision
        revision = None if request.to_revision == "previous" else request.to_revision
        
        # Trigger rollback via ArgoCD
        result = await argocd_client.rollback_application(app_name, revision=revision)
        
        # Log action
        print(f"⏮️  Rollback triggered: {app_name} to {request.to_revision} at {datetime.utcnow()}")
        # TODO: Write to audit log table
        
        return ActionResponse(
            success=True,
            message=f"Rollback triggered for {app_name}",
            data={
                "app_name": app_name,
                "customer_id": customer_id,
                "environment": environment,
                "target_revision": request.to_revision,
                "argocd_response": result
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Rollback failed: {str(e)}"
        )


async def scale_application(
    deployment_id: str,
    request: ScaleRequest,
    db: Session = Depends(get_db)
) -> ActionResponse:
    """
    POST /api/v1/deployments/{deployment_id}/scale
    
    Scale deployment replicas via Kubernetes API
    
    Args:
        deployment_id: Deployment identifier
        request: Scale request with replica count
        db: Database session
        
    Returns:
        ActionResponse with scale details
        
    Raises:
        HTTPException: If scale fails
    """
    try:
        customer_id, environment = parse_deployment_id(deployment_id)
        namespace = f"{customer_id}-{environment}"
        deployment_name = "app"  # Standard deployment name in OpenLuffy Helm charts
        
        # Scale via K8s API
        apps_v1 = client.AppsV1Api()
        body = {"spec": {"replicas": request.replicas}}
        
        apps_v1.patch_namespaced_deployment_scale(
            name=deployment_name,
            namespace=namespace,
            body=body
        )
        
        # Log action
        print(f"📊 Scaled: {namespace}/{deployment_name} to {request.replicas} replicas at {datetime.utcnow()}")
        # TODO: Write to audit log table
        
        return ActionResponse(
            success=True,
            message=f"Scaled {namespace}/{deployment_name} to {request.replicas} replicas",
            data={
                "namespace": namespace,
                "deployment": deployment_name,
                "customer_id": customer_id,
                "environment": environment,
                "replicas": request.replicas
            }
        )
    
    except client.ApiException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scale failed: {e.reason}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scale failed: {str(e)}"
        )


async def restart_application(
    deployment_id: str,
    db: Session = Depends(get_db)
) -> ActionResponse:
    """
    POST /api/v1/deployments/{deployment_id}/restart
    
    Restart deployment by deleting pods (K8s recreates them automatically)
    
    Args:
        deployment_id: Deployment identifier
        db: Database session
        
    Returns:
        ActionResponse with restart details
        
    Raises:
        HTTPException: If restart fails
    """
    try:
        customer_id, environment = parse_deployment_id(deployment_id)
        namespace = f"{customer_id}-{environment}"
        
        # Delete all pods in deployment (K8s will recreate)
        v1 = client.CoreV1Api()
        pods = v1.list_namespaced_pod(
            namespace=namespace,
            label_selector="app=app"  # Standard label in OpenLuffy Helm charts
        )
        
        deleted_pods = []
        for pod in pods.items:
            v1.delete_namespaced_pod(
                name=pod.metadata.name,
                namespace=namespace
            )
            deleted_pods.append(pod.metadata.name)
        
        # Log action
        print(f"🔁 Restarted: {namespace} - deleted {len(deleted_pods)} pods at {datetime.utcnow()}")
        # TODO: Write to audit log table
        
        return ActionResponse(
            success=True,
            message=f"Restarted {len(deleted_pods)} pods in {namespace}",
            data={
                "namespace": namespace,
                "customer_id": customer_id,
                "environment": environment,
                "deleted_pods": deleted_pods,
                "pods_count": len(deleted_pods)
            }
        )
    
    except client.ApiException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Restart failed: {e.reason}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Restart failed: {str(e)}"
        )


async def get_sync_status(
    deployment_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    GET /api/v1/deployments/{deployment_id}/sync-status
    
    Get real-time ArgoCD sync status
    
    Args:
        deployment_id: Deployment identifier
        db: Database session
        
    Returns:
        Dict with sync status, health, revision, message
        
    Raises:
        HTTPException: If failed to get status
    """
    try:
        customer_id, environment = parse_deployment_id(deployment_id)
        app_name = f"{customer_id}-{environment}"
        
        status = await argocd_client.get_sync_status(app_name)
        
        return {
            "deployment_id": deployment_id,
            "app_name": app_name,
            "customer_id": customer_id,
            "environment": environment,
            **status
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sync status: {str(e)}"
        )
