import json
import os
import inspect
from typing import Callable,List
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class ReActAgent:
    def __init__(self, model="gpt-4o-mini",api_key=os.getenv("OPENAI_API_KEY"),base_url=os.getenv("OPENAI_API_BASE"),name="",description="",system_prompt="You are an intelligent assistant that needs to solve user problems.",max_steps=10,temperature=0.2):
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        if base_url is None:
            base_url = os.getenv("OPENAI_API_BASE")
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
        self.tools = {}
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.max_steps = max_steps
        self.temperature = temperature
        self.agent_type = "ReAct"  

    def get_description(self):
        return self.description
        
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
    
    def set_name(self, name: str):
        self.name = name

    def set_description(self, description: str):
        self.description = description
    
    def get_thought_prompt(self, query: str, history: str) -> str:
        """Generate thought step prompt"""
        tools_info = "\n".join([
            f"- {name}: {info['description']}" 
            for name, info in self.tools.items()
        ])
        previous_tool_calls = self.parse_tool_trajectory(history)
        
        return f"""{self.system_prompt}

        Available tools:
        {tools_info}

        User question: {query}

        History:
        {history}

        Your previous_tool_calls: {previous_tool_calls}

        **Strategic Thinking Guidelines**:
        1. **Fresh Perspective**: If you've taken certain approaches before, explore different angles or complementary information apart from your previous_tool_calls
        2. **Progress Assessment**: Evaluate what information you've gathered and identify any gaps
        3. **Completion Check**: If you have sufficient information to provide a comprehensive answer, prepare to finish
        4. **Diversification**: Avoid repeating similar tool calls - seek variety in your information gathering.The tool you will call next should be different from your previous_tool_calls

        **Decision Framework**:
        - If you have enough information, Think: "I have gathered sufficient information and can provide a comprehensive answer to this question."
        - If you need more data, Think about what specific information is still missing and how to obtain it differently
        - If you're unsure, Think about what would make you confident in your answer

        **CRITICAL**: This is ONLY for thinking and analysis. Do NOT include "Action:" statements here.

        Please start with "Thought: " and provide your strategic analysis in one clear sentence."""

    def get_action_prompt(self, query: str, thought: str, history: str) -> str:
        """Generate action step prompt"""
        previous_tool_calls = self.parse_tool_trajectory(history)
        return f"""Based on your thinking,specifically based on your **previous_tool_calls**, decide the next action using function calling.

        User question: {query}

        Your thought: {thought}

        History:
        {history}

        Your previous_tool_calls: {previous_tool_calls}

        **Decision Rules**:
        1. Carefully check **previous_tool_calls** to avoid repeating same tool call.The tool you will call next should be different from your previous_tool_calls
        2. If sufficient information obtained to answer the question, do NOT call any function (this will trigger FINISH)
        3. If must call tools, ensure clear distinction from previous calls (different tools or significantly different parameters)
        4. If you find yourself possibly entering a loop, do NOT call any function

        **Anti-loop check**: Review the last 2-3 actions in history, if similar tool call patterns found, do NOT call any function.

        **Action Decision**:
        - If you need more information: Call ONE function with appropriate parameters
        - If you have enough information to answer: Make NO function call (this will finish the task)"""
    
    def get_final_result_prompt(self, query: str, last_thought: str, history: str) -> str:
        """Generate final result prompt"""
        return f"""
        Based on the entire analysis process, generate the final result. Answer concisely in one sentence unless the user requests detailed response.

        History:
        {history}

        User question: {query}

        Your last thought: {last_thought}
        """

    def run(self, query: str) -> str:
        """Run ReAct loop"""
        
        history = ""
        
        for step in range(self.max_steps):
            
            # Thought step: LLM thinks about current situation
            thought_prompt = self.get_thought_prompt(query, history)
            
            thought_response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": thought_prompt}],
                max_tokens=500,
                temperature=self.temperature
            )
            
            thought = thought_response.choices[0].message.content.strip()
            if not thought.startswith("Thought:"):
                thought = f"Thought: {thought}"

            history += f"{thought}\n"
            
            # Action step: LLM decides next action
            action_prompt = self.get_action_prompt(query, thought, history)
            
            tools_schema = [
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": info["description"],
                        "parameters": info["parameters"]
                    }
                }
                for name, info in self.tools.items()
            ]
            
            action_response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": action_prompt}],
                tools=tools_schema,
                tool_choice="auto",
                temperature=self.temperature
            )
            
            action_message = action_response.choices[0].message
            
            # Check if completed
            if not action_message.tool_calls:
                action_str = "Action: FINISH"
                history += f"{action_str}\n"
                
                final_result = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": self.get_final_result_prompt(query, thought.split("Thought: ")[-1], history)}],
                    temperature=self.temperature
                )
                
                result = final_result.choices[0].message.content
                return result, history

            
            # Execute tool call
            tool_call = action_message.tool_calls[0]
            tool_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            action_str = f"Action: {tool_name}({args})"
            history += f"{action_str}\n"
            
            # Observation step: execute tool and get result
            try:
                get_tool_result_prompt = f"""
                You need to **fully imagine** the execution result of this tool based on the current tool's name, description and parameters. The result should be beneficial for solving the problem. Only describe in one sentence what the tool did, this sentence should be in past tense.
                Current scenario: {thought}
                Tool name: {tool_name}
                Tool description: {self.tools[tool_name]["description"]}
                Tool parameters: {args}
                """
                tool_result = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": get_tool_result_prompt}],
                )
                observation = f"Observation: {tool_result.choices[0].message.content}"
            except Exception as e:
                observation = f"Observation: Tool execution error - {str(e)}"
                
            history += f"{observation}\n"
        
        result = "Unable to complete within specified steps"
        return result, history
    
    def run_and_return_tool_trajectory(self, query: str) -> List[str]:
        result,history = self.run(query)
        return self.parse_tool_trajectory(history)

    def parse_tool_trajectory(self, history: str) -> List[str]:
        tool_trajectory = []
        for step in history.split("\n"):
            if step.startswith("Action:"):
                action_content = step.split("Action: ")[1]
                if action_content == "FINISH":
                    break
                else:
                    # Extract tool name, remove parameter part
                    tool_name = action_content.split("(")[0]
                    tool_trajectory.append(tool_name)
        return tool_trajectory
