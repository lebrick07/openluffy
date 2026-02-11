"""
Tool definitions for Luffy AI agent
"""

from typing import List, Dict, Any
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from datetime import datetime
import os

# Initialize K8s client
try:
    config.load_incluster_config()
except:
    config.load_kube_config()

v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
networking_v1 = client.NetworkingV1Api()


def get_tools() -> List[Dict[str, Any]]:
    """Return list of tools available to Claude"""
    return [
        {
            "name": "get_pod_status",
            "description": "Get status of Kubernetes pods for a customer and environment. Returns pod names, status, restart counts, and ages.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "customer": {
                        "type": "string",
                        "description": "Customer name (e.g., 'acme-corp', 'techstart', 'widgetco', 'openluffy')"
                    },
                    "environment": {
                        "type": "string",
                        "description": "Environment: 'dev', 'preprod', or 'prod'",
                        "enum": ["dev", "preprod", "prod"]
                    }
                },
                "required": ["customer", "environment"]
            }
        },
        {
            "name": "get_pod_logs",
            "description": "Retrieve logs from a specific pod. Returns the last N lines of logs.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace (e.g., 'acme-corp-dev', 'openluffy-dev')"
                    },
                    "pod_name": {
                        "type": "string",
                        "description": "Name of the pod"
                    },
                    "lines": {
                        "type": "integer",
                        "description": "Number of log lines to retrieve (default: 100)",
                        "default": 100
                    },
                    "container": {
                        "type": "string",
                        "description": "Container name if pod has multiple containers (optional)"
                    }
                },
                "required": ["namespace", "pod_name"]
            }
        },
        {
            "name": "analyze_error",
            "description": "Use the AI Triage Engine to classify an error and determine root cause. Returns category (application bug, infrastructure, config, or dependencies), severity, confidence, reasoning, evidence, responsible team, and suggested actions.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "error_log": {
                        "type": "string",
                        "description": "The error message, stack trace, or log snippet to analyze"
                    }
                },
                "required": ["error_log"]
            }
        },
        {
            "name": "get_deployment_status",
            "description": "Get status of a Kubernetes deployment including replicas, available replicas, and conditions.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace"
                    },
                    "deployment_name": {
                        "type": "string",
                        "description": "Name of the deployment"
                    }
                },
                "required": ["namespace", "deployment_name"]
            }
        },
        {
            "name": "list_recent_events",
            "description": "List recent Kubernetes events in a namespace. Useful for understanding what happened recently (pod failures, scheduling issues, etc.).",
            "input_schema": {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of recent events to return (default: 10)",
                        "default": 10
                    }
                },
                "required": ["namespace"]
            }
        },
        {
            "name": "list_ingresses",
            "description": "List all Kubernetes Ingresses across all namespaces or in a specific namespace. Shows hosts, paths, and backend services.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Optional: specific namespace to query. If not provided, lists ingresses from all namespaces."
                    }
                },
                "required": []
            }
        },
        {
            "name": "restart_deployment",
            "description": "Restart a Kubernetes deployment by triggering a rollout. Useful when pods need to be restarted to pick up config changes or clear issues.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace"
                    },
                    "deployment_name": {
                        "type": "string",
                        "description": "Name of the deployment to restart"
                    }
                },
                "required": ["namespace", "deployment_name"]
            }
        },
        {
            "name": "scale_deployment",
            "description": "Scale a Kubernetes deployment to a specified number of replicas. Use to scale up/down based on load or troubleshoot by scaling to 0 and back.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace"
                    },
                    "deployment_name": {
                        "type": "string",
                        "description": "Name of the deployment to scale"
                    },
                    "replicas": {
                        "type": "integer",
                        "description": "Target number of replicas (0 to stop, >0 to run)"
                    }
                },
                "required": ["namespace", "deployment_name", "replicas"]
            }
        },
        {
            "name": "delete_pod",
            "description": "Delete a specific pod. The deployment controller will automatically recreate it. Useful for forcing a pod restart or clearing stuck pods.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace"
                    },
                    "pod_name": {
                        "type": "string",
                        "description": "Name of the pod to delete"
                    }
                },
                "required": ["namespace", "pod_name"]
            }
        },
        {
            "name": "list_namespaces",
            "description": "List all Kubernetes namespaces in the cluster. Shows namespace status, age, and labels.",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "list_customers",
            "description": "List all customers in OpenLuffy platform. Returns customer ID, name, stack, and creation time. Useful for understanding who you're managing.",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "get_customer_details",
            "description": "Get detailed information about a specific customer including their GitHub repo, ArgoCD applications, and deployment status across environments.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Customer ID (e.g., 'acme-corp', 'techstart')"
                    }
                },
                "required": ["customer_id"]
            }
        },
        {
            "name": "get_platform_health",
            "description": "Get overall OpenLuffy platform health including customer count, total deployments, ArgoCD status, and any issues.",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "create_customer",
            "description": "Create a new customer in OpenLuffy with GitHub repo and ArgoCD applications. IMPORTANT: DO NOT call this tool until you have confirmed details with the user AND received both GitHub token and ArgoCD token. Show smart defaults first (ID auto-generated from name, GitHub org='lebrick07', repo='{id}-api', ArgoCD URL='http://argocd.local'), then ask user to provide tokens. Only call this tool AFTER user provides tokens.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Customer display name (e.g., 'Acme Corp')"
                    },
                    "stack": {
                        "type": "string",
                        "description": "Tech stack: 'nodejs', 'python', or 'golang'. Defaults to 'nodejs'.",
                        "enum": ["nodejs", "python", "golang"]
                    },
                    "github_token": {
                        "type": "string",
                        "description": "GitHub personal access token with repo permissions (required)"
                    },
                    "id": {
                        "type": "string",
                        "description": "Optional: Customer ID slug (e.g., 'acme-corp'). Auto-generated from name if not provided."
                    },
                    "github_org": {
                        "type": "string",
                        "description": "Optional: GitHub organization or username. Defaults to 'lebrick07'."
                    },
                    "github_repo": {
                        "type": "string",
                        "description": "Optional: GitHub repository name. Defaults to '{customer-id}-api'."
                    },
                    "argocd_url": {
                        "type": "string",
                        "description": "Optional: ArgoCD URL. Defaults to 'http://argocd.local'."
                    },
                    "argocd_token": {
                        "type": "string",
                        "description": "Optional: ArgoCD API token. If not provided, will use default from environment."
                    }
                },
                "required": ["name", "github_token"]
            }
        },
        {
            "name": "delete_customer",
            "description": "Delete a customer and destroy all their environments. This will delete ArgoCD applications, K8s namespaces, archive the GitHub repo, remove integrations, and delete the customer record. Use with caution!",
            "input_schema": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Customer ID to delete (e.g., 'acme-corp')"
                    },
                    "delete_repo": {
                        "type": "boolean",
                        "description": "If true, permanently delete the GitHub repo. If false (default), archive it instead.",
                        "default": False
                    }
                },
                "required": ["customer_id"]
            }
        }
    ]


async def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool and return results"""
    
    if tool_name == "get_pod_status":
        return await get_pod_status(
            tool_input["customer"],
            tool_input["environment"]
        )
    
    elif tool_name == "get_pod_logs":
        return await get_pod_logs(
            tool_input["namespace"],
            tool_input["pod_name"],
            tool_input.get("lines", 100),
            tool_input.get("container")
        )
    
    elif tool_name == "analyze_error":
        return await analyze_error(tool_input["error_log"])
    
    elif tool_name == "get_deployment_status":
        return await get_deployment_status(
            tool_input["namespace"],
            tool_input["deployment_name"]
        )
    
    elif tool_name == "list_recent_events":
        return await list_recent_events(
            tool_input["namespace"],
            tool_input.get("limit", 10)
        )
    
    elif tool_name == "list_ingresses":
        return await list_ingresses(
            tool_input.get("namespace")
        )
    
    elif tool_name == "restart_deployment":
        return await restart_deployment(
            tool_input["namespace"],
            tool_input["deployment_name"]
        )
    
    elif tool_name == "scale_deployment":
        return await scale_deployment(
            tool_input["namespace"],
            tool_input["deployment_name"],
            tool_input["replicas"]
        )
    
    elif tool_name == "delete_pod":
        return await delete_pod(
            tool_input["namespace"],
            tool_input["pod_name"]
        )
    
    elif tool_name == "list_namespaces":
        return await list_namespaces()
    
    elif tool_name == "list_customers":
        return await list_customers()
    
    elif tool_name == "get_customer_details":
        return await get_customer_details(tool_input["customer_id"])
    
    elif tool_name == "get_platform_health":
        return await get_platform_health()
    
    elif tool_name == "create_customer":
        return await create_customer(tool_input)
    
    elif tool_name == "delete_customer":
        return await delete_customer(
            tool_input["customer_id"],
            tool_input.get("delete_repo", False)
        )
    
    else:
        return {"error": f"Unknown tool: {tool_name}"}


async def get_pod_status(customer: str, environment: str) -> Dict[str, Any]:
    """Get pod status for customer and environment"""
    namespace = f"{customer}-{environment}"
    
    try:
        pods = v1.list_namespaced_pod(namespace)
        
        pod_list = []
        for pod in pods.items:
            pod_info = {
                "name": pod.metadata.name,
                "status": pod.status.phase,
                "ready": f"{sum(1 for c in pod.status.container_statuses if c.ready)}/{len(pod.status.container_statuses)}" if pod.status.container_statuses else "0/0",
                "restarts": sum(c.restart_count for c in pod.status.container_statuses) if pod.status.container_statuses else 0,
                "age": str(pod.metadata.creation_timestamp),
            }
            
            # Add container statuses
            if pod.status.container_statuses:
                for container in pod.status.container_statuses:
                    if container.state.waiting:
                        pod_info["waiting_reason"] = container.state.waiting.reason
                    elif container.state.terminated:
                        pod_info["terminated_reason"] = container.state.terminated.reason
            
            pod_list.append(pod_info)
        
        return {
            "namespace": namespace,
            "pod_count": len(pod_list),
            "pods": pod_list
        }
    
    except ApiException as e:
        return {"error": f"Failed to get pods: {e.reason}"}


async def get_pod_logs(namespace: str, pod_name: str, lines: int = 100, container: str = None) -> Dict[str, Any]:
    """Get logs from a pod"""
    try:
        logs = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container,
            tail_lines=lines
        )
        
        return {
            "pod_name": pod_name,
            "namespace": namespace,
            "container": container or "default",
            "lines": lines,
            "logs": logs
        }
    
    except ApiException as e:
        return {"error": f"Failed to get logs: {e.reason}"}


async def analyze_error(error_log: str) -> Dict[str, Any]:
    """Analyze error using triage engine"""
    from triage import triage_engine
    
    result = triage_engine(error_log)
    
    return {
        "category": result.category.value,
        "severity": result.severity.value,
        "confidence": result.confidence,
        "reasoning": result.reasoning,
        "evidence": result.evidence,
        "responsible_team": result.responsible_team,
        "suggested_actions": result.suggested_actions
    }


async def get_deployment_status(namespace: str, deployment_name: str) -> Dict[str, Any]:
    """Get deployment status"""
    try:
        deployment = apps_v1.read_namespaced_deployment(deployment_name, namespace)
        
        return {
            "name": deployment_name,
            "namespace": namespace,
            "replicas": deployment.spec.replicas,
            "ready_replicas": deployment.status.ready_replicas or 0,
            "available_replicas": deployment.status.available_replicas or 0,
            "updated_replicas": deployment.status.updated_replicas or 0,
            "conditions": [
                {
                    "type": c.type,
                    "status": c.status,
                    "reason": c.reason,
                    "message": c.message
                }
                for c in (deployment.status.conditions or [])
            ]
        }
    
    except ApiException as e:
        return {"error": f"Failed to get deployment: {e.reason}"}


async def list_recent_events(namespace: str, limit: int = 10) -> Dict[str, Any]:
    """List recent events in namespace"""
    try:
        events = v1.list_namespaced_event(namespace)
        
        # Sort by timestamp, most recent first
        sorted_events = sorted(
            events.items,
            key=lambda e: e.last_timestamp or e.event_time,
            reverse=True
        )[:limit]
        
        event_list = []
        for event in sorted_events:
            event_list.append({
                "type": event.type,
                "reason": event.reason,
                "message": event.message,
                "object": f"{event.involved_object.kind}/{event.involved_object.name}",
                "count": event.count,
                "timestamp": str(event.last_timestamp or event.event_time)
            })
        
        return {
            "namespace": namespace,
            "events": event_list
        }
    
    except ApiException as e:
        return {"error": f"Failed to get events: {e.reason}"}


async def list_ingresses(namespace: str = None) -> Dict[str, Any]:
    """List ingresses across all namespaces or in a specific namespace"""
    try:
        if namespace:
            ingresses = networking_v1.list_namespaced_ingress(namespace)
        else:
            ingresses = networking_v1.list_ingress_for_all_namespaces()
        
        ingress_list = []
        for ing in ingresses.items:
            ingress_info = {
                "name": ing.metadata.name,
                "namespace": ing.metadata.namespace,
                "class": ing.spec.ingress_class_name,
                "rules": []
            }
            
            # Parse rules
            if ing.spec.rules:
                for rule in ing.spec.rules:
                    rule_info = {
                        "host": rule.host or "*",
                        "paths": []
                    }
                    
                    if rule.http and rule.http.paths:
                        for path in rule.http.paths:
                            path_info = {
                                "path": path.path,
                                "path_type": path.path_type,
                                "backend_service": path.backend.service.name if path.backend.service else None,
                                "backend_port": path.backend.service.port.number if path.backend.service and path.backend.service.port else None
                            }
                            rule_info["paths"].append(path_info)
                    
                    ingress_info["rules"].append(rule_info)
            
            # Get load balancer IPs if any
            if ing.status.load_balancer and ing.status.load_balancer.ingress:
                ingress_info["addresses"] = [
                    lb.ip or lb.hostname
                    for lb in ing.status.load_balancer.ingress
                ]
            
            ingress_list.append(ingress_info)
        
        return {
            "scope": f"namespace: {namespace}" if namespace else "all namespaces",
            "count": len(ingress_list),
            "ingresses": ingress_list
        }
    
    except ApiException as e:
        return {"error": f"Failed to list ingresses: {e.reason}"}


async def restart_deployment(namespace: str, deployment_name: str) -> Dict[str, Any]:
    """Restart a deployment by adding a timestamp annotation"""
    try:
        # Patch deployment with restart annotation
        now = datetime.now().isoformat()
        body = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "kubectl.kubernetes.io/restartedAt": now
                        }
                    }
                }
            }
        }
        
        apps_v1.patch_namespaced_deployment(
            name=deployment_name,
            namespace=namespace,
            body=body
        )
        
        return {
            "status": "success",
            "message": f"Deployment {deployment_name} in {namespace} restarted",
            "timestamp": now
        }
    
    except ApiException as e:
        return {"error": f"Failed to restart deployment: {e.reason}"}


async def scale_deployment(namespace: str, deployment_name: str, replicas: int) -> Dict[str, Any]:
    """Scale a deployment to specified number of replicas"""
    try:
        # Patch deployment replicas
        body = {
            "spec": {
                "replicas": replicas
            }
        }
        
        apps_v1.patch_namespaced_deployment_scale(
            name=deployment_name,
            namespace=namespace,
            body=body
        )
        
        return {
            "status": "success",
            "message": f"Deployment {deployment_name} in {namespace} scaled to {replicas} replicas"
        }
    
    except ApiException as e:
        return {"error": f"Failed to scale deployment: {e.reason}"}


async def delete_pod(namespace: str, pod_name: str) -> Dict[str, Any]:
    """Delete a pod (useful for forcing restart)"""
    try:
        v1.delete_namespaced_pod(
            name=pod_name,
            namespace=namespace
        )
        
        return {
            "status": "success",
            "message": f"Pod {pod_name} in {namespace} deleted (will be recreated by controller)"
        }
    
    except ApiException as e:
        return {"error": f"Failed to delete pod: {e.reason}"}


async def list_namespaces() -> Dict[str, Any]:
    """List all namespaces in the cluster"""
    try:
        namespaces = v1.list_namespace()
        
        ns_list = []
        for ns in namespaces.items:
            ns_list.append({
                "name": ns.metadata.name,
                "status": ns.status.phase,
                "age": str(ns.metadata.creation_timestamp),
                "labels": ns.metadata.labels or {}
            })
        
        return {
            "count": len(ns_list),
            "namespaces": ns_list
        }
    
    except ApiException as e:
        return {"error": f"Failed to list namespaces: {e.reason}"}


async def list_customers() -> Dict[str, Any]:
    """List all customers in OpenLuffy"""
    try:
        # Import here to avoid circular dependencies
        from database import SessionLocal, Customer
        
        db = SessionLocal()
        try:
            customers = db.query(Customer).all()
            
            customer_list = []
            for customer in customers:
                customer_list.append({
                    "id": customer.id,
                    "name": customer.name,
                    "stack": customer.stack,
                    "created_at": str(customer.created_at)
                })
            
            return {
                "count": len(customer_list),
                "customers": customer_list
            }
        finally:
            db.close()
    
    except Exception as e:
        return {"error": f"Failed to list customers: {str(e)}"}


async def get_customer_details(customer_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific customer"""
    try:
        # Import here to avoid circular dependencies
        from database import SessionLocal, Customer, Integration
        
        db = SessionLocal()
        try:
            # Get customer
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return {"error": f"Customer '{customer_id}' not found"}
            
            # Get integrations
            integrations = db.query(Integration).filter(Integration.customer_id == customer_id).all()
            
            integration_data = {}
            for integration in integrations:
                integration_data[integration.type] = integration.config
            
            # Get ArgoCD application status
            custom_api = client.CustomObjectsApi()
            argocd_apps = []
            
            for env in ['dev', 'preprod', 'prod']:
                app_name = f"{customer_id}-{env}"
                try:
                    app = custom_api.get_namespaced_custom_object(
                        group='argoproj.io',
                        version='v1alpha1',
                        namespace='argocd',
                        plural='applications',
                        name=app_name
                    )
                    
                    argocd_apps.append({
                        "name": app_name,
                        "environment": env,
                        "sync_status": app.get('status', {}).get('sync', {}).get('status'),
                        "health_status": app.get('status', {}).get('health', {}).get('status'),
                        "repo": app.get('spec', {}).get('source', {}).get('repoURL')
                    })
                except:
                    argocd_apps.append({
                        "name": app_name,
                        "environment": env,
                        "status": "not_found"
                    })
            
            # Get deployment status
            deployments = []
            for env in ['dev', 'preprod', 'prod']:
                namespace = f"{customer_id}-{env}"
                try:
                    deploys = apps_v1.list_namespaced_deployment(namespace)
                    for deploy in deploys.items:
                        deployments.append({
                            "name": deploy.metadata.name,
                            "environment": env,
                            "replicas": {
                                "desired": deploy.spec.replicas,
                                "ready": deploy.status.ready_replicas or 0,
                                "available": deploy.status.available_replicas or 0
                            }
                        })
                except:
                    pass
            
            return {
                "customer": {
                    "id": customer.id,
                    "name": customer.name,
                    "stack": customer.stack,
                    "created_at": str(customer.created_at)
                },
                "integrations": integration_data,
                "argocd_applications": argocd_apps,
                "deployments": deployments
            }
        
        finally:
            db.close()
    
    except Exception as e:
        return {"error": f"Failed to get customer details: {str(e)}"}


async def get_platform_health() -> Dict[str, Any]:
    """Get overall OpenLuffy platform health"""
    try:
        # Import here to avoid circular dependencies
        from database import SessionLocal, Customer
        
        db = SessionLocal()
        try:
            # Count customers
            customer_count = db.query(Customer).count()
            
            # Get ArgoCD applications
            custom_api = client.CustomObjectsApi()
            argocd_apps = custom_api.list_namespaced_custom_object(
                group='argoproj.io',
                version='v1alpha1',
                namespace='argocd',
                plural='applications'
            )
            
            apps_total = len(argocd_apps.get('items', []))
            apps_synced = 0
            apps_healthy = 0
            apps_degraded = 0
            
            for app in argocd_apps.get('items', []):
                sync_status = app.get('status', {}).get('sync', {}).get('status')
                health_status = app.get('status', {}).get('health', {}).get('status')
                
                if sync_status == 'Synced':
                    apps_synced += 1
                if health_status == 'Healthy':
                    apps_healthy += 1
                elif health_status == 'Degraded':
                    apps_degraded += 1
            
            # Get overall pod count
            all_pods = v1.list_pod_for_all_namespaces()
            pods_running = sum(1 for p in all_pods.items if p.status.phase == 'Running')
            pods_total = len(all_pods.items)
            
            # Check for issues
            issues = []
            if apps_degraded > 0:
                issues.append(f"{apps_degraded} ArgoCD applications are degraded")
            if apps_synced < apps_total:
                issues.append(f"{apps_total - apps_synced} ArgoCD applications are out of sync")
            if pods_running < pods_total:
                issues.append(f"{pods_total - pods_running} pods are not running")
            
            return {
                "status": "healthy" if len(issues) == 0 else "degraded",
                "customers": {
                    "total": customer_count
                },
                "argocd": {
                    "total": apps_total,
                    "synced": apps_synced,
                    "healthy": apps_healthy,
                    "degraded": apps_degraded
                },
                "pods": {
                    "total": pods_total,
                    "running": pods_running
                },
                "issues": issues
            }
        
        finally:
            db.close()
    
    except Exception as e:
        return {"error": f"Failed to get platform health: {str(e)}"}


async def create_customer(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new customer via backend API with smart defaults"""
    try:
        import httpx
        import os
        
        # Validate required fields
        customer_name = params.get("name")
        if not customer_name:
            return {
                "success": False,
                "error": "Customer name is required. Please provide it and try again."
            }
        
        github_token = params.get("github_token")
        if not github_token:
            return {
                "success": False,
                "error": "GitHub token is required. I cannot create the customer without it. Please provide a GitHub Personal Access Token with repo permissions."
            }
        
        # Auto-generate ID from name if not provided
        if "id" not in params or not params["id"]:
            customer_id = customer_name.lower().replace(" ", "-").replace("_", "-")
            # Remove special characters
            customer_id = ''.join(c for c in customer_id if c.isalnum() or c == '-')
            # Remove duplicate hyphens
            while '--' in customer_id:
                customer_id = customer_id.replace('--', '-')
            # Strip leading/trailing hyphens
            customer_id = customer_id.strip('-')
        else:
            customer_id = params["id"]
        
        # Default values
        stack = params.get("stack", "nodejs")
        github_org = params.get("github_org", "lebrick07")
        github_repo = params.get("github_repo", f"{customer_id}-api")
        argocd_url = params.get("argocd_url", "http://argocd.local")
        
        # ArgoCD token - try to get from env if not provided
        argocd_token = params.get("argocd_token")
        if not argocd_token:
            argocd_token = os.getenv("ARGOCD_TOKEN", "")
            if not argocd_token:
                return {
                    "success": False,
                    "error": "ArgoCD token is required. Please provide it or ensure ARGOCD_TOKEN environment variable is set."
                }
        
        # Build payload
        payload = {
            "name": customer_name,
            "id": customer_id,
            "stack": stack,
            "github": {
                "org": github_org,
                "repo": github_repo,
                "token": github_token,
                "branch": "main"
            },
            "argocd": {
                "url": argocd_url,
                "token": argocd_token
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/customers/create",
                json=payload,
                timeout=60.0
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Generate application URLs
                urls = {
                    "dev": f"http://dev.{customer_id}.local",
                    "preprod": f"http://preprod.{customer_id}.local",
                    "prod": f"http://{customer_id}.local"
                }
                
                return {
                    "success": True,
                    "message": f"Customer '{customer_name}' created successfully",
                    "customer_id": customer_id,
                    "urls": urls,
                    "details": result
                }
            else:
                error_data = response.json()
                return {
                    "success": False,
                    "error": error_data.get("error", "Unknown error")
                }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create customer: {str(e)}"
        }


async def delete_customer(customer_id: str, delete_repo: bool = False) -> Dict[str, Any]:
    """Delete a customer via backend API"""
    try:
        import httpx
        
        # Call the backend delete customer endpoint
        params = {
            "confirm": customer_id,
            "delete_repo": "true" if delete_repo else "false"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"http://localhost:8000/customers/{customer_id}",
                params=params,
                timeout=60.0
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    return {
                        "success": True,
                        "message": f"Customer '{customer_id}' deleted successfully",
                        "deleted": result.get("deleted", {}),
                        "errors": result.get("errors", [])
                    }
                else:
                    return {
                        "success": False,
                        "error": "Deletion completed with errors",
                        "errors": result.get("errors", [])
                    }
            else:
                error_data = response.json()
                return {
                    "success": False,
                    "error": error_data.get("error", "Unknown error")
                }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to delete customer: {str(e)}"
        }
