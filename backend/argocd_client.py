"""
ArgoCD API client for deployment operations

Provides wrapper functions for:
- Getting application status
- Triggering syncs (deploys)
- Rolling back to previous revisions
- Checking sync status

Environment Variables:
- ARGOCD_SERVER_URL: ArgoCD server URL (default: http://argocd-server.argocd.svc)
- ARGOCD_AUTH_TOKEN: ArgoCD API token (required)
"""
import httpx
import os
from typing import Dict, Any, Optional
from fastapi import HTTPException


class ArgoCDClient:
    """Client for ArgoCD API operations"""
    
    def __init__(self):
        self.base_url = os.getenv("ARGOCD_SERVER_URL", "http://argocd-server.argocd.svc")
        self.token = os.getenv("ARGOCD_AUTH_TOKEN")
        
        if not self.token:
            print("⚠️  ARGOCD_AUTH_TOKEN not set - ArgoCD operations will fail")
            print("   Generate token: ArgoCD UI → Settings → Accounts → Generate Token")
    
    async def get_application(self, app_name: str) -> Dict[str, Any]:
        """
        Get ArgoCD application details
        
        Args:
            app_name: Name of ArgoCD application (e.g., "acme-corp-dev")
            
        Returns:
            Dict containing application details, status, sync info
            
        Raises:
            HTTPException: If application not found or API error
        """
        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/applications/{app_name}",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"ArgoCD application '{app_name}' not found"
                )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"ArgoCD API error: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get ArgoCD application: {str(e)}"
            )
    
    async def sync_application(
        self, 
        app_name: str, 
        revision: str = "HEAD",
        prune: bool = False
    ) -> Dict[str, Any]:
        """
        Trigger ArgoCD application sync (deploy)
        
        Args:
            app_name: Name of ArgoCD application
            revision: Git revision to sync (default: HEAD)
            prune: Delete resources not in Git (default: False)
            
        Returns:
            Dict containing sync operation details
            
        Raises:
            HTTPException: If sync fails or API error
        """
        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/applications/{app_name}/sync",
                    headers={"Authorization": f"Bearer {self.token}"},
                    json={
                        "revision": revision,
                        "prune": prune,
                        "dryRun": False,
                        "syncOptions": {
                            "items": ["CreateNamespace=true"]
                        }
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"ArgoCD sync failed: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to sync ArgoCD application: {str(e)}"
            )
    
    async def get_sync_status(self, app_name: str) -> Dict[str, Any]:
        """
        Get real-time ArgoCD sync status
        
        Args:
            app_name: Name of ArgoCD application
            
        Returns:
            Dict containing status, health, revision, message
            
        Raises:
            HTTPException: If application not found or API error
        """
        try:
            app = await self.get_application(app_name)
            
            status_info = app.get("status", {})
            sync_info = status_info.get("sync", {})
            health_info = status_info.get("health", {})
            operation_state = status_info.get("operationState", {})
            
            return {
                "status": sync_info.get("status", "Unknown"),
                "health": health_info.get("status", "Unknown"),
                "revision": sync_info.get("revision", ""),
                "message": operation_state.get("message", ""),
                "phase": operation_state.get("phase", "")
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get sync status: {str(e)}"
            )
    
    async def rollback_application(
        self, 
        app_name: str, 
        revision: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Rollback to previous or specific revision
        
        Args:
            app_name: Name of ArgoCD application
            revision: Specific revision to rollback to (default: auto-detect previous)
            
        Returns:
            Dict containing rollback operation details
            
        Raises:
            HTTPException: If rollback fails or no previous revision found
        """
        try:
            # Get current app to find previous revision
            app = await self.get_application(app_name)
            history = app.get("status", {}).get("history", [])
            
            if not revision:
                # Auto-detect previous revision
                if len(history) >= 2:
                    # Get second-to-last deployment
                    revision = history[-2].get("revision", "HEAD~1")
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="No previous revision found. Application may not have been deployed yet."
                    )
            
            # Trigger sync to the rollback revision
            return await self.sync_application(app_name, revision=revision)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to rollback application: {str(e)}"
            )


# Global client instance
argocd_client = ArgoCDClient()
