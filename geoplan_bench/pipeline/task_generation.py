"""
Task generation pipeline for GeoPlan Benchmark.
"""

import os
import json
import re
import inspect
from tqdm import tqdm
from uuid import uuid4
from datetime import datetime
import networkx as nx
from openai import OpenAI
from google import genai

import geoplan_bench.tools as tools
from geoplan_bench.config.constants import (
    DOMAINS, EMPTY_DAG_TEMPLATE, EMPTY_TOOL_FLOW, EMPTY_PARAMETERIZED_TOOL_FLOW, DOMAIN_DESCRIPTIONS)
from geoplan_bench.config.prompts import DAG_TEMPLATE_PROMPT, PARAMETERIZE_FLOW_PROMPT, GENERATE_TASK_PROMPT


class DAGTaskTemplateGenerator:
    def __init__(self, model="gemini-2.5-pro"):
        self.client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY")
        )
        self.model = model
        self.tools_info = self._get_all_tools()
    
    def _get_all_tools(self):
        tool_info = []
        for name, obj in inspect.getmembers(tools):
            if inspect.isfunction(obj) and not name.startswith('_'):
                doc = obj.__doc__ or f"Execute {name} function"
                tool_info.append(f"{name}: {doc.strip()}")
        return tool_info
    
    def _parse_json_response(self, content):
        try:
            if "```json" in content:
                json_str = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL).group(1)
            elif "```" in content:
                json_str = re.search(r'```\s*(\{.*?\})\s*```', content, re.DOTALL).group(1)
            else:
                json_str = content
            return json.loads(json_str)
        except:
            return None
    
    def generate_dag_template(self, domain, complexity, output_dir="data/tasks/dag_templates"):
        tools_str = "\n".join(self.tools_info)

        if complexity == "Simple":
            tools_number_range = "10-30"
        elif complexity == "Complex":
            tools_number_range = "40-60"
        else:
            tools_number_range = "30-40"
        
        # get domain description
        domain_desc = DOMAIN_DESCRIPTIONS.get(domain, "")
        
        prompt = DAG_TEMPLATE_PROMPT.format(
            domain=domain,
            domain_desc=domain_desc,
            tools_str=tools_str,
            tools_number_range=tools_number_range
        )
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=[prompt]
        )
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        template_id = str(uuid4())
        filename = f"dag_template_{domain}_{complexity}_{template_id}.json"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self._parse_json_response(response.text), f, ensure_ascii=False, indent=2)
        return self._parse_json_response(response.text), filename


class ToolFlowGenerator:
    def __init__(self, model="gpt-4o-mini"):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"), 
            base_url=os.getenv("OPENAI_API_BASE")
        )
        self.model = model
    
    def _parse_json_response(self, content):
        try:
            if "```json" in content:
                json_str = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL).group(1)
            elif "```" in content:
                json_str = re.search(r'```\s*(\{.*?\})\s*```', content, re.DOTALL).group(1)
            else:
                json_str = content
            return json.loads(json_str)
        except:
            return None
    
    def _find_longest_paths_with_networkx(self, dag_template):
        """Use NetworkX to find longest paths in DAG"""
        try:
            G = nx.DiGraph()
            G.add_nodes_from(dag_template['nodes'])
            G.add_edges_from(dag_template['edges'])
            
            # Find all source nodes (in-degree = 0) and sink nodes (out-degree = 0)
            source_nodes = [n for n in G.nodes() if G.in_degree(n) == 0]
            sink_nodes = [n for n in G.nodes() if G.out_degree(n) == 0]
            
            longest_paths = []
            
            # Method 1: use nx.dag_longest_path to find longest path in the whole graph
            try:
                overall_longest = nx.dag_longest_path(G)
                if len(overall_longest) > 5:
                    longest_paths.append(overall_longest)
            except:
                pass
            
            # Method 2: use nx.all_simple_paths to find all simple paths
            for source in source_nodes[:2]:
                for sink in sink_nodes[:2]:
                    try:
                        simple_paths = list(nx.all_simple_paths(G, source, sink, cutoff=15))
                        simple_paths.sort(key=len, reverse=True)
                        longest_paths.extend(simple_paths[:3])
                    except:
                        continue
            
            # Remove duplicates and sort by length
            unique_paths = []
            seen = set()
            for path in longest_paths:
                path_tuple = tuple(path)
                if path_tuple not in seen and len(path) > 3:
                    seen.add(path_tuple)
                    unique_paths.append(path)
            
            unique_paths.sort(key=len, reverse=True)
            return unique_paths[:5]
            
        except Exception as e:
            print(f"NetworkX path finding failed: {e}")
            return []
    
    def extract_linear_flows(self, dag_template):
        try:
            longest_paths = self._find_longest_paths_with_networkx(dag_template)
            
            if not longest_paths:
                # If NetworkX fails, return empty list
                return []
            
            flows = []
            for path in longest_paths[:5]:
                flows.append(path)
            
            return flows
            
        except Exception as e:
            print(f"Algorithm path extraction failed: {e}")
            return []


class ToolFlowParameterizer:
    def __init__(self, model="gpt-4o-mini"):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"), 
            base_url=os.getenv("OPENAI_API_BASE")
        )
        self.model = model
        self.tools_info = self._get_all_tools()
    
    def _get_all_tools(self):
        tool_funcs = {}
        for name, obj in inspect.getmembers(tools):
            if inspect.isfunction(obj) and not name.startswith('_'):
                sig = inspect.signature(obj)
                params = {p.name: p.annotation for p in sig.parameters.values()}
                tool_funcs[name] = {
                    "doc": obj.__doc__ or f"Execute {name} function",
                    "params": params
                }
        return tool_funcs
    
    def _parse_json_response(self, content):
        try:
            if "```json" in content:
                json_str = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL).group(1)
            elif "```" in content:
                json_str = re.search(r'```\s*(\{.*?\})\s*```', content, re.DOTALL).group(1)
            else:
                json_str = content
            return json.loads(json_str)
        except:
            return None
    
    def parameterize_flow(self, flow):
        tools_details = []
        for tool_name in flow:
            if tool_name in self.tools_info:
                tools_details.append(f"{tool_name}: {self.tools_info[tool_name]['doc']}")
        
        tools_str = "\n".join(tools_details)
        
        prompt = PARAMETERIZE_FLOW_PROMPT.format(
            tools=flow,
            tools_str=tools_str
        )
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return self._parse_json_response(response.choices[0].message.content)


class TaskGenerator:
    def __init__(self, model="gemini-2.5-pro"):
        self.client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY")
        )
        self.model = model
    
    def generate_task_from_flow(self, parameterized_flow):
        flow_description = []
        for tool_call in parameterized_flow['parameterized_tools']:
            flow_description.append(f"{tool_call['tool']}: {tool_call['params']}")
        
        flow_str = "\n".join(flow_description)
        
        prompt = GENERATE_TASK_PROMPT.format(flow_str=flow_str)
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=[prompt]
        )
        
        return response.text


class RemoteSensingTaskPipeline:
    def __init__(self, model="gpt-4o-mini"):
        self.dag_generator = DAGTaskTemplateGenerator(model="gemini-2.5-pro")
        self.flow_generator = ToolFlowGenerator(model)
        self.parameterizer = ToolFlowParameterizer(model)
        self.task_generator = TaskGenerator(model="gemini-2.5-pro")
    
    def generate_task_with_ground_truth(self, complexity, domain):
        # 1. Generate DAG template
        dag_template, filename = self.dag_generator.generate_dag_template(domain, complexity)
        if not dag_template:
            return EMPTY_DAG_TEMPLATE
        
        # 2. Extract tool flow
        tool_flows = self.flow_generator.extract_linear_flows(dag_template)
        if not tool_flows:
            return EMPTY_TOOL_FLOW
        
        # 3. Parameterize all tool flows
        parameterized_flows = []
        for flow in tool_flows:
            parameterized_flow = self.parameterizer.parameterize_flow(flow)
            if not parameterized_flow:
                return EMPTY_PARAMETERIZED_TOOL_FLOW
            parameterized_flows.append(parameterized_flow)
        
        # 4. Generate task based on parameterized tool flows
        questions = []
        for parameterized_flow in parameterized_flows:
            question = self.task_generator.generate_task_from_flow(parameterized_flow)
            questions.append(question)

        # 5. Package complete result
        tasks = []
        for i, question in enumerate(questions):
            flow = tool_flows[i]
            task_id = str(uuid4())
            tasks.append({
                "task_id": task_id,
                "dag_template_filename": filename,
                "complexity": complexity,
                "domain": domain,
                "question": question,
                "ground_truth_tool_flow": flow,
            })
        
        return tasks
    
    def generate_batch_tasks(self, num_dags=5):
        "Generate and Save"
        domains = DOMAINS
        complexities = ["Simple", "Medium", "Complex"]
        
        total_dag_num = len(domains) * num_dags * len(complexities)
        
        with tqdm(total=total_dag_num, desc="Generating DAG templates and tasks", 
                  unit="task", ncols=100) as pbar:
            
            for domain_idx, domain in enumerate(domains):
                for dag_idx in range(num_dags):
                    for complexity_idx, complexity in enumerate(complexities):
                        pbar.set_description(f"{domain}-{complexity} (DAG {dag_idx+1}/{num_dags})")
                        
                        tasks = self.generate_task_with_ground_truth(complexity, domain)
                        if not tasks:
                            continue
                        # save tasks to file
                        self.export_tasks(tasks, output_dir="data/tasks/raw")
                        
                        pbar.update(1)
        
        print(f"\nTasks generated successfully!")
    
    def export_tasks(self, tasks, output_dir="data/tasks/raw"):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        for task in tasks:
            domain = task['domain']
            complexity = task['complexity']
            task_id = task['task_id']
            filename = f"task_{domain}_{complexity}_{task_id}.json"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(task, f, ensure_ascii=False, indent=2)
        return filepath

