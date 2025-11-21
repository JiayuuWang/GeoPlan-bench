"""
Script to filter tasks for GeoPlan Benchmark.
"""

import os
import sys
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geoplan_bench.pipeline.task_validation import filter_tasks
from geoplan_bench.utils.importance import analyze_tool_importance_from_tasks


def main():
    parser = argparse.ArgumentParser(description="Filter tasks for GeoPlan Benchmark")
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/tasks/raw",
        help="Input directory containing task files"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/tasks/filtered",
        help="Output directory for filtered tasks"
    )
    
    args = parser.parse_args()
    
    print("Filtering tasks...")
    filtered_tasks, stats = filter_tasks(args.input_dir)
    print(f"Filtered to {len(filtered_tasks)} tasks")
    
    # Save filtered tasks
    os.makedirs(args.output_dir, exist_ok=True)
    # replace existing files if any in the output directory
    for file in os.listdir(args.output_dir):
        if file.endswith('.json'):
            os.remove(os.path.join(args.output_dir, file))
    # save filtered tasks to the output directory
    for task in filtered_tasks:
        domain = task['domain']
        complexity = task['complexity']
        task_id = task['task_id']
        filename = f"task_{domain}_{complexity}_{task_id}.json"
        filepath = os.path.join(args.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(task, f, ensure_ascii=False, indent=2)
    
    # Run tool importance analysis on filtered tasks
    print("\nAnalyzing tool importance from filtered tasks...")
    try:
        analyze_tool_importance_from_tasks(args.output_dir)
        print("Tool importance analysis completed!")
    except Exception as e:
        print(f"Warning: Tool importance analysis failed: {e}")

if __name__ == "__main__":
    main()

