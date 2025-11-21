import json
import os
from typing import List
from openai import OpenAI
from dotenv import load_dotenv
from geoplan_bench.agents.ReAct import ReActAgent
from dotenv.main import logger

load_dotenv()


class EarthAgent:
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
        self.layer1_agents = {}
        self.layer2_agents = {}
        self.layer3_agents = {}
        self.agent_type = "EarthAgent"
        
    def add_agent(self, layer_num:int,agent:ReActAgent):
        """Add tool, automatically extract information from function"""
        # Get function name
        name = agent.name
        

        if layer_num == 1:
            self.layer1_agents[name] = agent
        elif layer_num == 2:
            self.layer2_agents[name] = agent
        elif layer_num == 3:
            self.layer3_agents[name] = agent
    
    def select_layer3_agent(self, query: str) -> dict:
        """Select third layer agent"""
        layer3_agents_info = "\n".join([
            f"- {name}: {agent.get_description()}" 
            for name, agent in self.layer3_agents.items()
        ])
        
        prompt = f"""You are an expert selection assistant. Select the most suitable third layer expert based on user questions.

        The third layer experts are responsible for integration and output, handling more specific domain problems. Available experts:
        {layer3_agents_info}

        User question: {query}

        Selection logic: Choose a third layer agent based on the industry and domain of the question. Select one from the third layer. For simple questions or daily Q&A, choose generalChatBotAgent.

        Please return selection result in JSON format:
        {{
            "selected_agent": "expert_name",
            "subtask": "specific subtask description that this expert needs to complete."
        }}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        
        try:
            result_text = response.choices[0].message.content
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            elif "```" in result_text:
                json_start = result_text.find("```") + 3
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            
            return json.loads(result_text)
        except Exception as e:
            logger.error(f"Layer 3 selection parsing failed: {e}")
            return {"selected_agent": "generalChatBotAgent", "subtask": query}
    
    def select_layer2_agents(self, query: str, layer3_selection: dict) -> list:
        """Select layer 2 agents"""
        layer2_agents_info = "\n".join([
            f"- {name}: {agent.get_description()}" 
            for name, agent in self.layer2_agents.items()
        ])
        
        prompt = f"""You are an expert selection assistant. Based on user questions and layer 3 expert selection, choose layer 2 experts.

        Layer 2 experts are responsible for image understanding work. Available experts:
        {layer2_agents_info}

        User question: {query}
        Layer 3 selected expert: {layer3_selection.get('selected_agent')}
        Layer 3 expert task: {layer3_selection.get('subtask')}

        Selection logic: Based on the question and layer 3 agent, think about what visual operations need to be performed on remote sensing images to solve the problem, then select 1 to 3 agents from layer 2 as needed.

        Please return selection result in JSON format:
        {{
            "selected_agents": [
                {{
                    "name": "expert_name_1",
                    "subtask": "specific subtask description this expert needs to complete."
                }},
                {{
                    "name": "expert_name_2", 
                    "subtask": "specific subtask description this expert needs to complete."
                }}
            ]
        }}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        
        try:
            result_text = response.choices[0].message.content
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            elif "```" in result_text:
                json_start = result_text.find("```") + 3
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            
            return json.loads(result_text).get("selected_agents", [])
        except Exception as e:
            logger.error(f"Layer 2 selection parsing failed: {e}")
            return []
    
    def select_layer1_agents(self, query: str, layer2_selections: list, layer3_selection: dict) -> list:
        """Select layer 1 agents"""
        layer1_agents_info = "\n".join([
            f"- {name}: {agent.get_description()}" 
            for name, agent in self.layer1_agents.items()
        ])
        
        layer2_info = ", ".join([agent.get("name", "") for agent in layer2_selections])
        
        prompt = f"""You are an expert selection assistant. Based on user questions and layer 2 & layer 3 expert selections, choose layer 1 experts.

        Layer 1 experts are responsible for data acquisition and preprocessing. Available experts:
        {layer1_agents_info}

        User question: {query}
        Layer 2 selected experts: {layer2_info}
        Layer 3 selected expert: {layer3_selection.get('selected_agent')}

        Selection logic: Combine the question with layer 2 and layer 3 agent selections, see if the question contains remote sensing data, determine whether to additionally acquire remote sensing data or images, and determine whether data preprocessing is needed (if needed, the question will hint that existing data has defects), select 1-2 layer 1 agents.

        Please return selection result in JSON format:
        {{
            "selected_agents": [
                {{
                    "name": "expert_name_1",
                    "subtask": "specific subtask description this expert needs to complete."
                }},
                {{
                    "name": "expert_name_2",
                    "subtask": "specific subtask description this expert needs to complete."
                }}
            ]
        }}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        
        try:
            result_text = response.choices[0].message.content
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            elif "```" in result_text:
                json_start = result_text.find("```") + 3
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            
            return json.loads(result_text).get("selected_agents", [])
        except Exception as e:
            logger.error(f"Layer 1 selection parsing failed: {e}")
            return []
    
    def select_layer1_agents_ablation_study(self, query: str) -> list:
        """Select layer 1 agents for ablation study"""
        layer1_agents_info = "\n".join([
            f"- {name}: {agent.get_description()}" 
            for name, agent in self.layer1_agents.items()
        ])
        
        prompt = f"""You are an expert selection assistant to choose layer 1 experts.

        Layer 1 experts are responsible for data acquisition and preprocessing. Available experts:
        {layer1_agents_info}

        User question: {query}

        Selection logic: See if the question contains remote sensing data, determine whether to additionally acquire remote sensing data or images, and determine whether data preprocessing is needed (if needed, the question will hint that existing data has defects), select 1-2 layer 1 agents.

        Please return selection result in JSON format:
        {{
            "selected_agents": [
                {{
                    "name": "expert_name_1",
                    "subtask": "specific subtask description this expert needs to complete."
                }},
                {{
                    "name": "expert_name_2",
                    "subtask": "specific subtask description this expert needs to complete."
                }}
            ]
        }}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        
        try:
            result_text = response.choices[0].message.content
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            elif "```" in result_text:
                json_start = result_text.find("```") + 3
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            
            return json.loads(result_text).get("selected_agents", [])
        except Exception as e:
            logger.error(f"Layer 1 selection parsing failed: {e}")
            return []

    def select_layer2_agents_ablation_study(self, query: str) -> list:
        """Select layer 2 agents for ablation study"""
        layer2_agents_info = "\n".join([
            f"- {name}: {agent.get_description()}" 
            for name, agent in self.layer2_agents.items()
        ])
        
        prompt = f"""You are an expert selection assistant to choose layer 2 experts.

        Layer 2 experts are responsible for image understanding work. Available experts:
        {layer2_agents_info}

        User question: {query}

        Selection logic: Think about what visual operations need to be performed on remote sensing images to solve the problem, then select 1 to 3 agents from layer 2 as needed.

        Please return selection result in JSON format:
        {{
            "selected_agents": [
                {{
                    "name": "expert_name_1",
                    "subtask": "specific subtask description this expert needs to complete."
                }},
                {{
                    "name": "expert_name_2", 
                    "subtask": "specific subtask description this expert needs to complete."
                }}
            ]
        }}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        
        try:
            result_text = response.choices[0].message.content
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            elif "```" in result_text:
                json_start = result_text.find("```") + 3
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            
            return json.loads(result_text).get("selected_agents", [])
        except Exception as e:
            logger.error(f"Layer 2 selection parsing failed: {e}")
            return []
    
    def select_layer3_agents_ablation_study(self, query: str) -> list:
        """Select third layer agent for ablation study"""
        layer3_agents_info = "\n".join([
            f"- {name}: {agent.get_description()}" 
            for name, agent in self.layer3_agents.items()
        ])
        
        prompt = f"""You are an expert selection assistant. Select the most suitable third layer expert based on user questions.

        The third layer experts are responsible for integration and output, handling more specific domain problems. Available experts:
        {layer3_agents_info}

        User question: {query}

        Selection logic: Choose a third layer agent based on the industry and domain of the question. Select one from the third layer. For simple questions or daily Q&A, choose generalChatBotAgent.

        Please return selection result in JSON format:
        {{
            "selected_agent": "expert_name",
            "subtask": "specific subtask description that this expert needs to complete."
        }}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        
        try:
            result_text = response.choices[0].message.content
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            elif "```" in result_text:
                json_start = result_text.find("```") + 3
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            
            return json.loads(result_text)
        except Exception as e:
            logger.error(f"Layer 3 selection parsing failed: {e}")
            return {"selected_agent": "generalChatBotAgent", "subtask": query}
            
    def select_agents_directly(self, query: str) -> list:
        """Select agents directly"""
        layer1_agents_info = "\n".join([
            f"- {name}: {agent.get_description()}" 
            for name, agent in self.layer1_agents.items()
        ])
        layer2_agents_info = "\n".join([
            f"- {name}: {agent.get_description()}" 
            for name, agent in self.layer2_agents.items()
        ])
        layer3_agents_info = "\n".join([
            f"- {name}: {agent.get_description()}" 
            for name, agent in self.layer3_agents.items()
        ])
        prompt = f"""You are an expert selection assistant to choose agents directly.
        Available experts:
        {layer1_agents_info}
        {layer2_agents_info}
        {layer3_agents_info}
        User question: {query}
        Selection logic: Choose the most several relevant agents based on the user question.
        Please return selection result in JSON format:
        {{
            "selected_agents": [
                {{
                    "name": "expert_name_1",
                    "subtask": "specific subtask description this expert needs to complete."
                }},
                {{
                    "name": "expert_name_2",
                    "subtask": "specific subtask description this expert needs to complete."
                }}
            ]
        }}
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        try:
            result_text = response.choices[0].message.content
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            elif "```" in result_text:
                json_start = result_text.find("```") + 3
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            return json.loads(result_text)
        except Exception as e:
            logger.error(f"Agents selection parsing failed: {e}")
            return []
    
    def run(self, query: str) -> str:
        """Run EarthAgent"""
        
        # Step 1: Layer-wise agent selection
        layer3_selection = self.select_layer3_agent(query)
        layer2_selections = self.select_layer2_agents(query, layer3_selection)
        layer1_selections = self.select_layer1_agents(query, layer2_selections, layer3_selection)
        
        # Build execution plan
        plan = {
            "plan": [
                {"layer": 1, "agents": layer1_selections},
                {"layer": 2, "agents": layer2_selections},
                {"layer": 3, "agents": [layer3_selection]}
            ]
        }
        
        # Step 2: Expert reasoning
        results = []
        
        for step in plan.get("plan", []):
            layer = step.get("layer")
            agents = step.get("agents", [])
            
            # Select corresponding agent dictionary based on layer number
            if layer == 1:
                agent_dict = self.layer1_agents
            elif layer == 2:
                agent_dict = self.layer2_agents
            elif layer == 3:
                agent_dict = self.layer3_agents
            else:
                error_msg = f"Unknown layer number: {layer}"
                results.append(error_msg)
                continue
            
            # Execute expert reasoning
            try:
                for agent_info in agents:
                    # Handle special format for layer 3
                    if layer == 3 and isinstance(agent_info, dict) and "selected_agent" in agent_info:
                        agent_name = agent_info.get("selected_agent")
                        subtask = agent_info.get("subtask", query)
                        subtask = f"Final task:{query}\n" +f"This is the subtask of the final task that you need to complete right now:{subtask} "+ "\n" + "**choose the most relevant tools to solve the subtask**"
                    elif isinstance(agent_info, dict):
                        agent_name = agent_info.get("name")
                        subtask = agent_info.get("subtask", query)
                    else:
                        agent_name = agent_info
                        subtask = query
                    
                    # Checkagent
                    if agent_name not in agent_dict:
                        error_msg = f"Agent {agent_name}  {layer} "
                        results.append(error_msg)
                        continue
                    
                    # agent1
                    agent = agent_dict[agent_name]
                    # EarthAgent
                    agent.agent_type = "EarthAgent"
                    
                    result, history = agent.run(subtask)
                    result_info = {
                        "layer": layer,
                        "agent_name": agent.name,
                        "agent_description": agent.description,
                        "subtask": subtask,
                        "result": result,
                        "history": history
                    }
                    results.append(result_info)
            except Exception as e:
                error_msg = f": {str(e)}"
                results.append(error_msg)
        
        # Step 3: Generate final result
        final_result = results[-1] if results else ""
        return final_result, results
    
    def run_and_return_tool_trajectory(self, query: str) -> List[str]:
        final_result,results = self.run(query)
        tool_trajectory=[]
        for result_info in results:
            if isinstance(result_info, dict) and "history" in result_info:
                history = result_info["history"]
                # from history parse tool calls
                for step in history.split("\n"):
                    if step.startswith("Action:"):
                        action_content = step.split("Action: ")[1]
                        if action_content == "FINISH":
                            continue
                        else:
                            # Handle different formats：tool_name(...)  tool_name, {...}  tool_name{"..."}
                            if "(" in action_content:
                                tool_name = action_content.split("(")[0]
                            elif "," in action_content:
                                tool_name = action_content.split(",")[0].strip()
                            elif "{" in action_content:
                                tool_name = action_content.split("{")[0].strip()
                            else:
                                tool_name = action_content.strip()
                            tool_trajectory.append(tool_name)
        return tool_trajectory
