import os
import json
import re
from tqdm import tqdm

from openai import OpenAI
from dotenv import load_dotenv
from dotenv.main import logger

from geoplan_bench.evaluation.metrics import CorrectnessEvaluator, HolisticEvaluator, StructuralEvaluator
from geoplan_bench.utils.arena import (create_react_agent, create_earth_agent, create_plan_and_execute_agent,
    create_debate_agent, create_zero_shot_cot_based_agent, create_aflow_agent)
from geoplan_bench.pipeline.task_generation import RemoteSensingTaskPipeline

load_dotenv()


class RemoteSensingTaskEval:
    def __init__(self, model="gpt-4o-mini"):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"), 
            base_url=os.getenv("OPENAI_API_BASE")
        )
        self.model = model
        self.pipeline = RemoteSensingTaskPipeline(model)
        self.correctness_evaluator = CorrectnessEvaluator(model)
        self.holistic_evaluator = HolisticEvaluator(model)
        self.structural_evaluator = StructuralEvaluator()
    
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
    
    def evaluate_task(self,task):
        task_id = task.get('task_id', 'unknown_task')
        question = task['question']
        ground_truth_tool_trajectory=task['ground_truth_tool_flow']


        react_agent = create_react_agent()
        plan_and_execute_agent = create_plan_and_execute_agent()
        earth_agent = create_earth_agent()
        debate_agent = create_debate_agent()
        zero_shot_cot_based_agent = create_zero_shot_cot_based_agent()
        aflow_agent = create_aflow_agent()


        react_agent_tool_trajectory = react_agent.run_and_return_tool_trajectory(question)
        plan_and_execute_agent_tool_trajectory = plan_and_execute_agent.run_and_return_tool_trajectory(question)
        earth_agent_tool_trajectory = earth_agent.run_and_return_tool_trajectory(question)
        debate_agent_tool_trajectory = debate_agent.run_and_return_tool_trajectory(question)
        zero_shot_cot_based_agent_tool_trajectory = zero_shot_cot_based_agent.run_and_return_tool_trajectory(question)
        aflow_agent_tool_trajectory = aflow_agent.run_and_return_tool_trajectory(question)
        agents_results = {
            "ReAct": react_agent_tool_trajectory,
            "Plan-and-Execute": plan_and_execute_agent_tool_trajectory,
            "EarthAgent": earth_agent_tool_trajectory,
            "Debate": debate_agent_tool_trajectory,
            "CoT": zero_shot_cot_based_agent_tool_trajectory,
            "AFlow": aflow_agent_tool_trajectory
        }

        eval_results = {}

        holistic_metric_score = self.holistic_evaluator.compute_completeness_score(agents_results, question)

        for agent_name, agent_tool_trajectory in agents_results.items():
            key_steps, key_tools, key_step_recall, key_tool_precision, F1_score = self.correctness_evaluator.compute_correctness_score(question, ground_truth_tool_trajectory, agent_tool_trajectory)
            tool_flow_similarity, enhanced_edit_distance = self.structural_evaluator.compute_structural_score(agent_tool_trajectory, ground_truth_tool_trajectory)
            # store results
            eval_results[agent_name] = {
                "tool_trajectory": agent_tool_trajectory,
                "key_steps": key_steps,
                "key_step_recall": key_step_recall,
                "key_tools": key_tools,
                "key_tool_precision": key_tool_precision,
                "F1_score": F1_score,
                "enhanced_edit_distance": enhanced_edit_distance,
                "tool_flow_similarity": tool_flow_similarity,
                "completeness_score": holistic_metric_score[agent_name],
            }

        return eval_results


def execute_task_evaluation_pipeline(start_from_task_index: int = 0, end_to_task_index: int = None):
    """eval range: [start_from_task_index:end_to_task_index]"""
    pipeline = RemoteSensingTaskEval()
    eval_results = []
    tasks = []
    # eval path
    task_dir = "data/tasks/filtered"
    if not os.path.exists(task_dir):
        raise FileNotFoundError(f"Task directory not found: {task_dir}. Please run task filtering first.")
    files = [f for f in os.listdir(task_dir) if f.endswith('.json')]
    if not files:
        raise FileNotFoundError(f"No task files found in {task_dir}")
    for filename in files:
        filepath = os.path.join(task_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            task = json.load(f)
            tasks.append(task)
    task_num = len(tasks)
    task_evaluated_num = 0
    # if end_to_task_index is not None, set end_to_task_index to the last task index
    if end_to_task_index is None:
        end_to_task_index = task_num 
    print(f"Evaluate tasks from {start_from_task_index} to {end_to_task_index}")
    print(f"Total tasks: {task_num}")
    with tqdm(total=end_to_task_index - start_from_task_index ,
              desc=f"Evaluate tasks from {start_from_task_index} to {end_to_task_index}", 
              unit="task", ncols=100) as pbar:
        
        for task_idx, task in enumerate(tasks[start_from_task_index:end_to_task_index]):
            task_id = task.get('task_id')
            domain = task.get('domain')
            complexity = task.get('complexity')
            
            # update progress bar description
            pbar.set_description(f"Evaluate {''.join(re.findall(r'[A-Z]', domain))}-{complexity}")
            try:
                eval_results = pipeline.evaluate_task(task)
            except Exception as e:
                logger.error(f"\nEvaluate task id:{task_id},index:{task_idx+start_from_task_index} failed: {e}")
                continue
            # save the result for this task
            result_data = {
                "task_info": task,
                "eval_result": eval_results,
            }
            with open(os.path.join("data/eval_results", f"eval_{task_id}.json"), 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            task_evaluated_num += 1
            pbar.set_postfix({
                'Evaluated': task_evaluated_num,
                'failed': task_idx - task_evaluated_num + 1,
                'Total': task_num
            })
            
            # update progress bar
            pbar.update(1)





