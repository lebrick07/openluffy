"""
Luffy - AI Super DevOps Engineer
OpenClaw Integration Module
"""

import os
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime


class LuffyAgent:
    """
    Luffy is the autonomous AI DevOps Engineer.
    This class handles all AI interactions via OpenClaw.
    """
    
    def __init__(self):
        self.openclaw_url = os.getenv('OPENCLAW_URL', 'http://localhost:8080')
        self.openclaw_token = os.getenv('OPENCLAW_TOKEN', '')
        self.session_id = os.getenv('OPENCLAW_SESSION', 'main')
        
    async def chat(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to Luffy and get a response.
        
        Args:
            message: User's message
            context: Current context (customer, environment, resource)
            history: Previous messages in conversation
            
        Returns:
            Dict with 'content' and optional 'actions' list
        """
        
        # Build context-aware prompt
        system_context = self._build_context_prompt(context)
        full_message = f"{system_context}\n\n{message}"
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.openclaw_url}/api/chat",
                    json={
                        "message": full_message,
                        "session": self.session_id,
                        "history": history or []
                    },
                    headers={
                        "Authorization": f"Bearer {self.openclaw_token}"
                    } if self.openclaw_token else {}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Parse actions from response
                    actions = self._extract_actions(data.get('content', ''))
                    
                    return {
                        "content": data.get('content', 'No response from Luffy'),
                        "actions": actions,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        "content": f"Error: Luffy is unavailable (status {response.status_code})",
                        "actions": [],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
        except Exception as e:
            return {
                "content": f"Error connecting to Luffy: {str(e)}",
                "actions": [],
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _build_context_prompt(self, context: Optional[Dict[str, Any]]) -> str:
        """Build context-aware system prompt"""
        if not context:
            return "You are Luffy, an AI Super DevOps Engineer."
        
        parts = ["You are Luffy, an AI Super DevOps Engineer. Current context:"]
        
        if context.get('customer'):
            parts.append(f"- Customer: {context['customer']}")
        if context.get('environment'):
            parts.append(f"- Environment: {context['environment']}")
        if context.get('resource_type'):
            parts.append(f"- Resource: {context['resource_type']} ({context.get('resource_name', 'unknown')})")
        
        parts.append("\nYour job is to help manage this infrastructure autonomously.")
        parts.append("Propose fixes, generate configurations, and explain your reasoning.")
        
        return "\n".join(parts)
    
    def _extract_actions(self, content: str) -> List[Dict[str, str]]:
        """
        Extract actionable items from AI response.
        Look for keywords that suggest actions.
        """
        actions = []
        
        # Simple keyword matching (can be improved with better parsing)
        if "fix" in content.lower() or "patch" in content.lower():
            actions.append({"label": "Apply Fix", "action": "apply-fix"})
        
        if "rollback" in content.lower():
            actions.append({"label": "Rollback", "action": "rollback"})
        
        if "log" in content.lower() or "logs" in content.lower():
            actions.append({"label": "Show Logs", "action": "show-logs"})
        
        if "deploy" in content.lower():
            actions.append({"label": "Deploy", "action": "deploy"})
        
        if "config" in content.lower() or "manifest" in content.lower():
            actions.append({"label": "View Config", "action": "view-config"})
        
        return actions
    
    async def execute_action(
        self, 
        action: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute an action proposed by Luffy.
        
        Args:
            action: Action identifier (apply-fix, rollback, etc.)
            context: Current context
            
        Returns:
            Result of the action
        """
        
        # Action handlers
        handlers = {
            "apply-fix": self._apply_fix,
            "rollback": self._rollback,
            "show-logs": self._show_logs,
            "deploy": self._deploy,
            "view-config": self._view_config
        }
        
        handler = handlers.get(action)
        if not handler:
            return {
                "success": False,
                "message": f"Unknown action: {action}"
            }
        
        try:
            return await handler(context)
        except Exception as e:
            return {
                "success": False,
                "message": f"Action failed: {str(e)}"
            }
    
    async def _apply_fix(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply a fix to the system"""
        # TODO: Implement actual fix application
        return {
            "success": True,
            "message": "Fix applied successfully (placeholder)"
        }
    
    async def _rollback(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Rollback a deployment"""
        # TODO: Implement actual rollback
        return {
            "success": True,
            "message": "Rollback initiated (placeholder)"
        }
    
    async def _show_logs(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Fetch and return logs"""
        # TODO: Implement actual log fetching
        return {
            "success": True,
            "message": "Logs retrieved (placeholder)",
            "logs": "Sample log output..."
        }
    
    async def _deploy(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Deploy to environment"""
        # TODO: Implement actual deployment
        return {
            "success": True,
            "message": "Deployment started (placeholder)"
        }
    
    async def _view_config(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """View configuration"""
        # TODO: Implement actual config retrieval
        return {
            "success": True,
            "message": "Configuration retrieved (placeholder)",
            "config": "apiVersion: v1\nkind: Service\n..."
        }


# Singleton instance
luffy = LuffyAgent()
