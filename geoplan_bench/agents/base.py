"""
Base Agent interface for GeoPlan Benchmark.
"""

from abc import ABC, abstractmethod
from typing import List, Callable, Optional, Dict, Any
import inspect


class BaseAgent(ABC):
    """Base class for all agents in GeoPlan Benchmark."""
    
    def __init__(self, model: str = "gpt-4o-mini", agent_type: str = ""):
        """
        Initialize base agent.
        
        Args:
            model: Model name to use
            agent_type: Type identifier for the agent
        """
        self.model = model
        self.agent_type = agent_type
        self.tools: Dict[str, Dict[str, Any]] = {}
    
    @abstractmethod
    def run(self, query: str) -> str:
        """
        Run the agent with a query.
        
        Args:
            query: Input query string
            
        Returns:
            Result string
        """
        pass
    
    @abstractmethod
    def run_and_return_tool_trajectory(self, query: str) -> List[str]:
        """
        Run the agent and return tool trajectory.
        
        Args:
            query: Input query string
            
        Returns:
            List of tool names called during execution
        """
        pass
    
    def add_tool(self, func: Callable):
        """
        Add a tool function to the agent.
        
        Args:
            func: Tool function to add
        """
        name = func.__name__
        description = func.__doc__ or f"Execute {name} function"
        
        sig = inspect.signature(func)
        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
                
            param_type = "string"
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == float:
                    param_type = "number"
                elif param.annotation == bool:
                    param_type = "boolean"
            
            parameters["properties"][param_name] = {
                "type": param_type,
                "description": f"{param_name} parameter"
            }
            
            if param.default == inspect.Parameter.empty:
                parameters["required"].append(param_name)
        
        self.tools[name] = {
            "func": func,
            "description": description,
            "parameters": parameters
        }
    
    def parse_tool_trajectory(self, history: str) -> List[str]:
        """
        Parse tool trajectory from history string.
        
        Args:
            history: History string containing tool calls
            
        Returns:
            List of tool names
        """
        tool_trajectory = []
        for step in history.split("\n"):
            if step.startswith("Action:"):
                action_content = step.split("Action: ")[1]
                if action_content == "FINISH":
                    break
                else:
                    tool_name = action_content.split("(")[0]
                    tool_trajectory.append(tool_name)
        return tool_trajectory
