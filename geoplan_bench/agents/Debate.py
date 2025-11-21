from dotenv.main import logger
from openai import OpenAI
import os
import inspect
from typing import Callable, List
from dotenv import load_dotenv
import json

load_dotenv()


class DebateAgent:
    def __init__(self, model="gpt-4o-mini",api_key=os.getenv("OPENAI_API_KEY"),base_url=os.getenv("OPENAI_API_BASE")):
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
        self.agent_type = "Debate"  

    def add_tool_to_debater(self, func: Callable):
        """add tool to debater"""
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

    def create_initial_prompt(self, question: str) -> str:
        """Create initial prompt for Round 0 - independent thinking"""
        tools_info = "\n".join([
            f"- {name}: {info['description']}" 
            for name, info in self.tools.items()
        ])
        
        return f"""You are participating in a multi-agent debate. In this initial round, please think independently and provide your first answer to the question without seeing other agents' responses.

        Question: {question}

        Available tools:
        {tools_info}

        Please analyze the user's question and create an execution plan and corresponding initial_tool_trajectory. The plan is a paragraph of statement,the initial_tool_trajectory is a list of tool names which can solve the question properly. Decide the length of the tool chain based on the difficulty of the problem.

        Please return the plan in JSON format as follows:
        {{
            "plan": your plan to solve the question,
            "initial_tool_trajectory": ["tool_name_1","tool_name_2",...]
        }}
        """

    def create_debate_prompt(self, question: str, conversation_history: List[str],debater_index: int,debater_num: int) -> str:
        """Create debate prompt for Round 1 to N - debate rounds"""
        tools_info = "\n".join([
            f"- {name}: {info['description']}" 
            for name, info in self.tools.items()
        ])
        
        history_str = "\n".join(conversation_history)

        former_response = conversation_history[-debater_num]
        
        return f"""You are number {debater_index} debater participating in a multi-agent debate. You have seen all previous responses and now need to provide your perspective.

        Question: {question}

        your former response: {former_response}

        Available tools:
        {tools_info}

        Debate History:
        {history_str}

        Based on the previous responses, please analyze the strengths and weaknesses of previous arguments and improve your former tool trajectory.Return a breif advice and the refined tool trajectory in JSON format as follows:
        {{  "advice": "your short advice to improve your former tool trajectory",
            "refined_tool_trajectory": ["tool_name_1","tool_name_2",...]
        }}
        """

    def create_final_prompt(self, question: str, conversation_history: List[str]) -> str:
        """Create final prompt for summary round"""
        tools_info = "\n".join([
            f"- {name}: {info['description']}" 
            for name, info in self.tools.items()
        ])
        
        history_str = "\n".join(conversation_history)
        
        return f"""You are a judge/summarizer for a multi-agent debate. Please analyze the entire debate and return a final tool trajectory.

        Original Question: {question}

        Available tools:
        {tools_info}

        Complete Debate History:
        {history_str}

        Please return a final tool_trajectory.Follow the json format strictly and do not include any other text:

        Json format:
        {{
            "final_tool_trajectory": ["tool_name_1","tool_name_2",...]
        }}

        """

    def run_and_return_tool_trajectory(self,
        question: str, 
        debater_num: int = 3,
        num_rounds: int = 2) -> str:
        """Run the complete debate process"""
        # 1. Initialize conversation history
        conversation_history = []
        
        # 2. Round 0: Independent initial responses
        
        for i in range(debater_num):
            prompt = self.create_initial_prompt(question)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
             
            conversation_history.append(f"[Round 0] number {i} debater: {response.choices[0].message.content}")

        # 3. Round 1 to N: Debate rounds
        for round_num in range(1, num_rounds + 1):      
            for i in range(debater_num):
                prompt = self.create_debate_prompt(question, conversation_history,i,debater_num)
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                )
                conversation_history.append(f"[Round {round_num}] number {i} debater: {response.choices[0].message.content}")

        # 4. Final Answer: Summary round      
        final_prompt = self.create_final_prompt(question, conversation_history)
        final_response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": final_prompt}], 
        )
        try:
            tool_trajectory = json.loads(final_response.choices[0].message.content.strip())["final_tool_trajectory"]
        except Exception as e:
            logger.error(f"Error: {e}")    
            tool_trajectory = []
          
        conversation_history.append(f"[Round {num_rounds+1}] final tool trajectory: {tool_trajectory}")

        return tool_trajectory
