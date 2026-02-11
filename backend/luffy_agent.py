"""
Luffy AI Agent - Core intelligence
"""

import os
from typing import List, Dict, Any, Optional
from anthropic import Anthropic, AsyncAnthropic
from prompts import get_system_prompt
from tools import get_tools, execute_tool


class LuffyAgent:
    """
    Captain Luffy - AI Super DevOps Engineer
    
    Uses Claude to provide intelligent troubleshooting, analysis,
    and execution of DevOps operations.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Luffy agent
        
        Args:
            api_key: Anthropic API key (falls back to ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not provided")
        
        self.client = AsyncAnthropic(api_key=self.api_key)
        self.system_prompt = get_system_prompt()
        self.tools = get_tools()
        self.model = "claude-sonnet-4-20250514"  # Default model
    
    async def chat(
        self,
        message: str,
        customer: Optional[str] = None,
        environment: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a chat message and return response
        
        Args:
            message: User's message
            customer: Active customer (optional)
            environment: Active environment (optional)
            history: Conversation history (optional)
            model: Claude model to use (optional, defaults to Sonnet 4)
        
        Returns:
            Dict with response, actions, and metadata
        """
        # Build context from customer/environment
        context_message = ""
        if customer:
            context_message = f"\n\nCurrent context: Customer={customer}"
            if environment:
                context_message += f", Environment={environment}"
        
        # Build messages list
        messages = history or []
        messages.append({
            "role": "user",
            "content": message + context_message
        })
        
        # Use provided model or default
        model_to_use = model or self.model
        
        # Call Claude with tools
        response = await self.client.messages.create(
            model=model_to_use,
            max_tokens=4096,
            system=self.system_prompt,
            messages=messages,
            tools=self.tools
        )
        
        # Process response and tool calls
        return await self._process_response(response, messages)
    
    async def _process_response(
        self,
        response: Any,
        messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Process Claude's response and execute any tool calls
        
        Args:
            response: Claude API response
            messages: Message history
        
        Returns:
            Formatted response for frontend
        """
        # Check if Claude wants to use tools
        if response.stop_reason == "tool_use":
            # Execute all tool calls
            tool_results = []
            assistant_message = {"role": "assistant", "content": response.content}
            messages.append(assistant_message)
            
            for content_block in response.content:
                if content_block.type == "tool_use":
                    tool_name = content_block.name
                    tool_input = content_block.input
                    
                    # Execute tool
                    result = await execute_tool(tool_name, tool_input)
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": str(result)
                    })
            
            # Send tool results back to Claude
            messages.append({
                "role": "user",
                "content": tool_results
            })
            
            # Get Claude's final response
            final_response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self.system_prompt,
                messages=messages,
                tools=self.tools
            )
            
            return self._format_response(final_response)
        
        else:
            # No tool use, return response directly
            return self._format_response(response)
    
    def _format_response(self, response: Any) -> Dict[str, Any]:
        """
        Format Claude's response for the frontend
        
        Args:
            response: Claude API response
        
        Returns:
            Formatted response dict
        """
        # Extract text content
        text_content = ""
        actions = []
        
        for content_block in response.content:
            if content_block.type == "text":
                text_content += content_block.text
        
        # TODO: Parse action buttons from response text
        # For now, return basic structure
        
        return {
            "response": text_content,
            "actions": actions,
            "model": self.model,
            "stop_reason": response.stop_reason
        }
    
    async def execute_action(
        self,
        action_type: str,
        action_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a confirmed action (restart, scale, etc.)
        
        Args:
            action_type: Type of action (restart, scale, rollback, etc.)
            action_data: Action parameters
        
        Returns:
            Result of action execution
        """
        # TODO: Implement action execution
        # For now, return placeholder
        return {
            "success": False,
            "message": "Action execution not yet implemented",
            "action_type": action_type,
            "action_data": action_data
        }


# Global agent instance
_agent_instance: Optional[LuffyAgent] = None


def get_agent() -> LuffyAgent:
    """Get or create the global Luffy agent instance"""
    global _agent_instance
    
    if _agent_instance is None:
        _agent_instance = LuffyAgent()
    
    return _agent_instance
