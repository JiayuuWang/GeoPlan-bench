from openai import OpenAI
import os
import inspect
from typing import Callable, List
from dotenv import load_dotenv

load_dotenv()


class ZeroShotCoTBasedAgent:
    def __init__(self, model="gpt-4o-mini"):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE")
        )
        self.model = model
        self.tools = {}
        self.agent_type = "CoT" 
        
    def add_tool(self, func: Callable):
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
        
        self.tools[name] = {"func": func, "description": description, "parameters": parameters}
    
    def get_cot_prompt(self, query: str) -> str:
        """Generate CoT prompt"""
        tools_info = "\n".join([
            f"- {name}: {info['description']}" 
            for name, info in self.tools.items()
        ])
        return f"""
        You are an intelligent assistant that needs to solve user problems based on the tools provided.
        User question: {query}
        Available tools:
        {tools_info}
        Please think step by step,in each step,you should choose one name of these tools to call.
        Output in this format strictly:
        step1:thought_1;tool_1_name
        step2:thought_2;tool_2_name
        ...
        stepn:thought_n;tool_n_name
        """
    
    def run(self, query: str) -> str:
        """Run CoT agent"""
        cot_prompt = self.get_cot_prompt(query)
        cot_response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": cot_prompt}],
            temperature=0.2
        )
        return cot_response.choices[0].message.content

    def run_and_return_tool_trajectory(self, query: str) -> List[str]:
        """Run CoT agent and return tool trajectory"""
        result = self.run(query)
        tool_trajectory = []
        for step in result.split("\n"):
            if step.startswith("step"):
                tool_trajectory.append(step.split(";")[1].strip())
        return tool_trajectory
