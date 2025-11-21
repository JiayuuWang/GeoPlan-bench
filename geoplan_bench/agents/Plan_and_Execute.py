import json
import os
import inspect
from typing import Callable, List
from openai import OpenAI
from dotenv import load_dotenv
from geoplan_bench.data.schemas import PlanSchema

load_dotenv()


class PlanExecuteAgent:
    def __init__(self, model="gpt-4o-mini"):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE")
        )
        self.model = model
        self.tools = {}
        self.agent_type = "Plan&Execute" 
        
    def add_tool(self, func: Callable):
        """Add tool, automatically extract information from function"""
        # Get function name
        name = func.__name__
        
        # Get docstring as description
        description = func.__doc__ or f"Execute {name} function"
        
        # Get function signature
        sig = inspect.signature(func)
        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        # Analyze parameters
        for param_name, param in sig.parameters.items():
            # Skip self parameter
            if param_name == 'self':
                continue
                
            param_type = "string"  # Default type
            if param.annotation != inspect.Parameter.empty:
                # Set type based on type annotation
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
            
            # If no default value, then required parameter
            if param.default == inspect.Parameter.empty:
                parameters["required"].append(param_name)
        
        self.tools[name] = {"func": func, "description": description, "parameters": parameters}
    
    def get_planning_prompt(self, query: str) -> str:
        """Generate planning step prompt"""
        tools_info = "\n".join([
            f"- {name}: {info['description']}" 
            for name, info in self.tools.items()
        ])
        
        return f"""You are an intelligent assistant that needs to solve user problems.

        Available tools:
        {tools_info}

        User question: {query}

        Please analyze the user's question and create an execution plan. The plan is a tool chain that you need to carefully design to make the tool chain can solve the user's question properly. Decide the length of the tool chain based on the difficulty of the problem.

        Please return the plan in JSON format as follows:
        {{
            "plan": [
                {{
                    "tool": "tool_name_1",
                    "parameters": {{"param_name": "param_value"}},
                }},
                {{
                    "tool": "tool_name_2",
                    "parameters": {{"param_name": "param_value"}},
                }}
            ]
        }}

        """

    def get_final_result_prompt(self, query: str, plan: dict, results: List[str]) -> str:
        """Generate execution step prompt"""
        tools_info = "\n".join([
            f"- {name}: {info['description']}" 
            for name, info in self.tools.items()
        ])
        
        results_text = "\n".join([f"Step {i+1} result: {result}" for i, result in enumerate(results)])
        
        return f"""Execute tool calls based on the created plan.

        Available tools:
        {tools_info}

        User question: {query}

        Execution plan:
        {json.dumps(plan, ensure_ascii=False, indent=2)}

        Executed results:
        {results_text}

        Please summarize the above tool call results and generate a concise answer."""
    
    def plan(self,query:str)->str:
        planning_prompt = self.get_planning_prompt(query)
        
        planning_response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[{"role": "user", "content": planning_prompt}],
            response_format=PlanSchema
        )
        
        plan = planning_response.choices[0].message.parsed
        return plan

    def execute(self, plan: dict) -> List[str]:
        results = []
        
        for i, step in enumerate(plan.plan):
            tool_name = step.tool
            parameters = step.parameters or {}  
            
            # Check if tool exists
            if tool_name not in self.tools:
                error_msg = f"Tool {tool_name} does not exist"
                results.append(error_msg)
                continue
            
            # Execute tool call
            try:
                result = self.tools[tool_name]["func"](**parameters)
                results.append(result)
            except Exception as e:
                error_msg = f"Tool execution error: {str(e)}"
                results.append(error_msg)
        
        return results
        
    def run(self, query: str) -> str:
        plan = self.plan(query)
        results = self.execute(plan)
        final_result = self.get_final_result_prompt(query, plan, results)
        
        # Record execution results
        plan_dict = []
        for step in plan.plan:
            if hasattr(step, 'dict'):
                plan_dict.append(step.dict())
            else:
                plan_dict.append({"tool": step.tool, "parameters": step.parameters})
        
        return final_result
    
    def run_and_return_tool_trajectory(self, query: str) -> List[str]:
        plan = self.plan(query)
        
        # Convert plan to serializable format
        plan_dict = []
        for step in plan.plan:
            if hasattr(step, 'dict'):
                plan_dict.append(step.dict())
            else:
                plan_dict.append({"tool": step.tool, "parameters": step.parameters})
        
        # Extract tool trajectory
        tool_trajectory = []
        for step in plan.plan:
            tool_trajectory.append(step.tool)
        
        return tool_trajectory
