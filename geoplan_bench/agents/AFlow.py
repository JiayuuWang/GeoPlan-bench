import os
import inspect
import ast
import re
from typing import Callable
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class AFlowAgent:
    def __init__(self, model="gpt-4o-mini"):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE")
        )
        self.model = model
        self.tools = {}
        self.agent_type = "AFlow"
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
    def run_and_return_tool_trajectory(self, question: str) -> str:
        """
        Implementation of the workflow
        """
        from geoplan_bench.config.prompts import (
            ANSWER_GENERATION_PROMPT, REFINE_PROMPT, VERIFY_PROMPT,
            SC_ENSEMBLE_PROMPT, VALIDATE_FORMAT_PROMPT, FORMAT_PROMPT
        )
        
        tools_info = "\n".join([
            f"- {name}: {info['description']}" 
            for name, info in self.tools.items()
        ])
        initial_prompt = question+"\nYou must choose the tools below to output the best tool flow that can solve the problen with the format:['tool1_name','tool2_name','tool3_name'......].Only output the tool flow, do not output any other text.Tools you can choose from:\n "+"\n".join(tools_info)
        # Generate initial solution
        initial_solution =self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": ANSWER_GENERATION_PROMPT.format(input=initial_prompt)}],
            temperature=0.3
        ).choices[0].message.content
        
        # Get refined solution with custom operator
        refined_solution = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": initial_prompt+f"\nInitial solution: {initial_solution}"+REFINE_PROMPT}],
            temperature=0.3
        ).choices[0].message.content
        
        # Verify essential tools
        verified_solution = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": initial_prompt+f"\nCurrent solution: {refined_solution}"+VERIFY_PROMPT}],
            temperature=0.3
        ).choices[0].message.content

        # Ensemble the solutions
        solutions = [initial_solution, refined_solution, verified_solution]
        answer_mapping = {}
        solution_text = ""
        for index, solution in enumerate(solutions):
            answer_mapping[chr(65 + index)] = index
            solution_text += f"{chr(65 + index)}: \n{str(solution)}\n\n\n"

        prompt = SC_ENSEMBLE_PROMPT.format(solutions=solution_text)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        ).choices[0].message.content
        try:
          # response format:"""
          # ...
          # **solution_letter**: A
          # """
          ensemble_solution_answer_letter = re.search(r'[ABC]', response.split("solution_letter")[-1].strip()).group()
          letter_to_index_dict={'A':0,'B':1,'C':2}
          ensemble_solution_answer_index = letter_to_index_dict[ensemble_solution_answer_letter]
          ensemble_solution_answer = solutions[ensemble_solution_answer_index]
        except:
          print("Error in ensemble solution")
          ensemble_solution_answer = verified_solution
          
        # Validate format and preprocessing steps
        validated_solution = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": f"\nCurrent solution: {ensemble_solution_answer}"+VALIDATE_FORMAT_PROMPT}],
            temperature=0.3
        ).choices[0].message.content
        
        # Final formatting
        formatted_solution = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": f"\nCurrent solution: {validated_solution}"+FORMAT_PROMPT}],
            temperature=0.3
        ).choices[0].message.content
        
        return ast.literal_eval(formatted_solution)
