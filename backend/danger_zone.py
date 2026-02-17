"""
Danger Zone API
Destructive per-customer operations requiring confirmation and admin access
"""
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import httpx

from database import get_db, Customer, User, AuditLog, APIToken, Integration, ProvisioningStep
from auth import require_admin
from kubernetes import client, config

# Load Kubernetes config
try:
    config.load_incluster_config()
except:
    config.load_kube_config()

k8s_apps = client.AppsV1Api()
k8s_core = client.CoreV1Api()


# ============================================================================
# REQUEST MODELS
# ============================================================================

class ConfirmationRequest(BaseModel):
    """Confirmation required for destructive actions"""
    customer_id: str = Field(..., description="Customer ID to confirm")
    confirmation: str = Field(..., description="Type customer ID to confirm")
    
    def validate_confirmation(self):
        """Verify user typed customer ID correctly"""
        if self.confirmation != self.customer_id:
            raise HTTPException(
                status_code=400,
                detail=f"Confirmation failed. Please type '{self.customer_id}' exactly."
            )


class DeleteDeploymentsRequest(ConfirmationRequest):
    """Delete all deployments for customer"""
    pass


class ResetSecretsRequest(ConfirmationRequest):
    """Reset all secrets for customer"""
    pass


class DisableCustomerRequest(ConfirmationRequest):
    """Disable customer (soft delete)"""
    reason: Optional[str] = Field(None, description="Reason for disabling")


class DeleteCustomerRequest(ConfirmationRequest):
    """Permanently delete customer"""
    delete_deployments: bool = Field(True, description="Also delete all deployments")
    delete_namespaces: bool = Field(True, description="Also delete Kubernetes namespaces")


class TransferOwnershipRequest(ConfirmationRequest):
    """Transfer customer ownership to another user"""
    new_owner_id: int = Field(..., description="User ID of new owner")


# ============================================================================
# ARGOCD CLIENT
# ============================================================================

class ArgoCDClient:
    """Simple ArgoCD API client"""
    
    def __init__(self):
        import os
        self.base_url = os.getenv("ARGOCD_URL", "http://argocd-server.argocd.svc.cluster.local")
        self.token = os.getenv("ARGOCD_TOKEN", "")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    async def delete_application(self, app_name: str, cascade: bool = True):
        """Delete ArgoCD application"""
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/api/v1/applications/{app_name}"
            params = {"cascade": str(cascade).lower()}
            response = await client.delete(url, headers=self.headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()


# ============================================================================
# DANGER ZONE ACTIONS
# ============================================================================

async def delete_all_deployments(
    request: DeleteDeploymentsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Delete all deployments for customer
    
    POST /api/v1/customers/{customer_id}/danger-zone/delete-deployments
    Body: {customer_id, confirmation}
    
    Actions:
    - Deletes ArgoCD applications (dev, preprod, prod)
    - Scales K8s deployments to 0 replicas
    - Does NOT delete namespaces (can be recreated)
    """
    # Validate confirmation
    request.validate_confirmation()
    
    # Get customer
    customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    environments = ["dev", "preprod", "prod"]
    deleted = []
    errors = []
    
    # Delete ArgoCD applications
    argocd = ArgoCDClient()
    for env in environments:
        app_name = f"{customer.id}-{env}"
        try:
            await argocd.delete_application(app_name, cascade=True)
            deleted.append(f"ArgoCD app: {app_name}")
        except Exception as e:
            errors.append(f"Failed to delete {app_name}: {str(e)}")
    
    # Scale K8s deployments to 0
    for env in environments:
        namespace = f"{customer.id}-{env}"
        try:
            # List all deployments in namespace
            deployments = k8s_apps.list_namespaced_deployment(namespace)
            for deployment in deployments.items:
                # Scale to 0 replicas
                deployment.spec.replicas = 0
                k8s_apps.patch_namespaced_deployment(
                    name=deployment.metadata.name,
                    namespace=namespace,
                    body=deployment
                )
                deleted.append(f"Scaled {namespace}/{deployment.metadata.name} to 0")
        except Exception as e:
            errors.append(f"Failed to scale deployments in {namespace}: {str(e)}")
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="danger_zone_delete_deployments",
        resource_type="customer",
        resource_id=customer.id,
        details={
            "customer_name": customer.name,
            "deleted": deleted,
            "errors": errors
        }
    )
    db.add(audit)
    db.commit()
    
    return {
        "message": f"Deleted all deployments for customer '{customer.name}'",
        "deleted": deleted,
        "errors": errors
    }


async def reset_all_secrets(
    request: ResetSecretsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Reset all secrets for customer
    
    POST /api/v1/customers/{customer_id}/danger-zone/reset-secrets
    Body: {customer_id, confirmation}
    
    Actions:
    - Deletes all Kubernetes secrets in customer namespaces
    - Clears secrets from database (if stored)
    - Does NOT delete service account tokens
    """
    # Validate confirmation
    request.validate_confirmation()
    
    # Get customer
    customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    environments = ["dev", "preprod", "prod"]
    deleted = []
    errors = []
    
    # Delete K8s secrets
    for env in environments:
        namespace = f"{customer.id}-{env}"
        try:
            # List all secrets (exclude service account tokens)
            secrets = k8s_core.list_namespaced_secret(namespace)
            for secret in secrets.items:
                # Skip service account tokens
                if secret.type == "kubernetes.io/service-account-token":
                    continue
                
                # Delete secret
                k8s_core.delete_namespaced_secret(
                    name=secret.metadata.name,
                    namespace=namespace
                )
                deleted.append(f"Secret {namespace}/{secret.metadata.name}")
        except Exception as e:
            errors.append(f"Failed to delete secrets in {namespace}: {str(e)}")
    
    # TODO: Clear secrets from database when Secret model exists
    # For now, just clear integration configs that might contain secrets
    integrations = db.query(Integration).filter(
        Integration.customer_id == customer.id
    ).all()
    
    for integration in integrations:
        # Clear sensitive fields from config
        if 'token' in integration.config:
            integration.config['token'] = None
        if 'password' in integration.config:
            integration.config['password'] = None
        if 'api_key' in integration.config:
            integration.config['api_key'] = None
    
    db.commit()
    deleted.append(f"Cleared {len(integrations)} integration secrets")
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="danger_zone_reset_secrets",
        resource_type="customer",
        resource_id=customer.id,
        details={
            "customer_name": customer.name,
            "deleted": deleted,
            "errors": errors
        }
    )
    db.add(audit)
    db.commit()
    
    return {
        "message": f"Reset all secrets for customer '{customer.name}'",
        "deleted": deleted,
        "errors": errors,
        "warning": "Applications may fail until secrets are recreated"
    }


async def disable_customer(
    request: DisableCustomerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Disable customer (soft delete, reversible)
    
    POST /api/v1/customers/{customer_id}/danger-zone/disable
    Body: {customer_id, confirmation, reason?}
    
    Actions:
    - Marks customer as disabled
    - Scales all deployments to 0
    - Does NOT delete data (can be re-enabled)
    """
    # Validate confirmation
    request.validate_confirmation()
    
    # Get customer
    customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Add disabled flag to customer (requires schema update)
    # For now, we'll use a special integration to track status
    disabled_marker = Integration(
        customer_id=customer.id,
        type="__disabled",
        config={
            "disabled_at": datetime.utcnow().isoformat(),
            "disabled_by": current_user.email,
            "reason": request.reason or "No reason provided"
        }
    )
    db.add(disabled_marker)
    
    # Scale all deployments to 0
    environments = ["dev", "preprod", "prod"]
    scaled = []
    errors = []
    
    for env in environments:
        namespace = f"{customer.id}-{env}"
        try:
            deployments = k8s_apps.list_namespaced_deployment(namespace)
            for deployment in deployments.items:
                deployment.spec.replicas = 0
                k8s_apps.patch_namespaced_deployment(
                    name=deployment.metadata.name,
                    namespace=namespace,
                    body=deployment
                )
                scaled.append(f"{namespace}/{deployment.metadata.name}")
        except Exception as e:
            errors.append(f"Failed to scale {namespace}: {str(e)}")
    
    db.commit()
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="danger_zone_disable_customer",
        resource_type="customer",
        resource_id=customer.id,
        details={
            "customer_name": customer.name,
            "reason": request.reason,
            "scaled": scaled,
            "errors": errors
        }
    )
    db.add(audit)
    db.commit()
    
    return {
        "message": f"Customer '{customer.name}' disabled successfully",
        "scaled": scaled,
        "errors": errors,
        "note": "Customer can be re-enabled by admin"
    }


async def delete_customer_permanently(
    request: DeleteCustomerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Permanently delete customer (CANNOT BE UNDONE)
    
    POST /api/v1/customers/{customer_id}/danger-zone/delete-permanent
    Body: {customer_id, confirmation, delete_deployments, delete_namespaces}
    
    Actions:
    - Deletes customer record from database
    - Optionally deletes all deployments
    - Optionally deletes Kubernetes namespaces
    - Cascades to integrations, provisioning steps, etc.
    """
    # Validate confirmation
    request.validate_confirmation()
    
    # Get customer
    customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer_name = customer.name
    deleted = []
    errors = []
    
    # Delete deployments if requested
    if request.delete_deployments:
        argocd = ArgoCDClient()
        environments = ["dev", "preprod", "prod"]
        for env in environments:
            app_name = f"{customer.id}-{env}"
            try:
                await argocd.delete_application(app_name, cascade=True)
                deleted.append(f"ArgoCD app: {app_name}")
            except Exception as e:
                errors.append(f"Failed to delete {app_name}: {str(e)}")
    
    # Delete namespaces if requested
    if request.delete_namespaces:
        environments = ["dev", "preprod", "prod"]
        for env in environments:
            namespace = f"{customer.id}-{env}"
            try:
                k8s_core.delete_namespace(namespace)
                deleted.append(f"Namespace: {namespace}")
            except Exception as e:
                errors.append(f"Failed to delete namespace {namespace}: {str(e)}")
    
    # Audit log BEFORE deletion
    audit = AuditLog(
        user_id=current_user.id,
        action="danger_zone_delete_customer_permanent",
        resource_type="customer",
        resource_id=customer.id,
        details={
            "customer_id": customer.id,
            "customer_name": customer_name,
            "deleted_deployments": request.delete_deployments,
            "deleted_namespaces": request.delete_namespaces,
            "deleted": deleted,
            "errors": errors
        }
    )
    db.add(audit)
    db.commit()
    
    # Delete customer from database (cascades to integrations, provisioning_steps)
    db.delete(customer)
    db.commit()
    deleted.append(f"Customer record: {customer.id}")
    
    return {
        "message": f"Customer '{customer_name}' permanently deleted",
        "deleted": deleted,
        "errors": errors,
        "warning": "This action CANNOT be undone"
    }


async def transfer_customer_ownership(
    request: TransferOwnershipRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Transfer customer ownership to another user
    
    POST /api/v1/customers/{customer_id}/danger-zone/transfer-ownership
    Body: {customer_id, confirmation, new_owner_id}
    
    Note: This is a placeholder - customer ownership model doesn't exist yet.
    Will be implemented when multi-user customer access is added.
    """
    # Validate confirmation
    request.validate_confirmation()
    
    # Get customer
    customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get new owner
    new_owner = db.query(User).filter(User.id == request.new_owner_id).first()
    if not new_owner:
        raise HTTPException(status_code=404, detail="New owner user not found")
    
    # TODO: Implement when Customer.owner_id field is added
    # For now, just audit log the intent
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="danger_zone_transfer_ownership",
        resource_type="customer",
        resource_id=customer.id,
        details={
            "customer_name": customer.name,
            "old_owner_id": current_user.id,
            "old_owner_email": current_user.email,
            "new_owner_id": new_owner.id,
            "new_owner_email": new_owner.email
        }
    )
    db.add(audit)
    db.commit()
    
    return {
        "message": f"Customer '{customer.name}' ownership transfer logged",
        "note": "Customer ownership model not yet implemented. This is a placeholder.",
        "new_owner": {
            "id": new_owner.id,
            "email": new_owner.email,
            "name": f"{new_owner.first_name} {new_owner.last_name}"
        }
    }


async def revoke_all_customer_tokens(
    request: ConfirmationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Revoke all API tokens associated with customer context
    
    POST /api/v1/customers/{customer_id}/danger-zone/revoke-tokens
    Body: {customer_id, confirmation}
    
    Note: This will be more useful when tokens have customer scopes.
    For now, just documents the pattern.
    """
    # Validate confirmation
    request.validate_confirmation()
    
    # Get customer
    customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # TODO: When tokens have customer_id or customer-scoped permissions,
    # revoke all tokens that have access to this customer
    
    # For now, just audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="danger_zone_revoke_customer_tokens",
        resource_type="customer",
        resource_id=customer.id,
        details={
            "customer_name": customer.name,
            "note": "Token-customer association not yet implemented"
        }
    )
    db.add(audit)
    db.commit()
    
    return {
        "message": f"Token revocation for '{customer.name}' logged",
        "note": "Customer-scoped tokens not yet implemented. This is a placeholder.",
        "warning": "In production, this would revoke all tokens with access to this customer"
    }
