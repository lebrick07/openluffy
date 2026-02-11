"""
Tool definitions for Luffy AI agent
"""

from typing import List, Dict, Any
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import os

# Initialize K8s client
try:
    config.load_incluster_config()
except:
    config.load_kube_config()

v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()


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
