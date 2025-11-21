"""
Script to generate tasks for GeoPlan Benchmark.
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geoplan_bench.pipeline.task_generation import RemoteSensingTaskPipeline


def main():
    parser = argparse.ArgumentParser(description="Generate tasks for GeoPlan Benchmark")
    parser.add_argument(
        "--num-dags",
        type=int,
        default=5,
        help="Number of DAG templates to generate per domain-complexity combination"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/tasks/raw",
        help="Output directory for generated tasks"
    )
    
    args = parser.parse_args()
    
    print("Starting task generation...")
    pipeline = RemoteSensingTaskPipeline()
    tasks = pipeline.generate_batch_tasks(num_dags=args.num_dags)
    
    output_path = pipeline.export_tasks(tasks, output_dir=args.output_dir)
    print(f"Tasks exported to: {output_path}")
    print(f"Total tasks generated: {len(tasks)}")


if __name__ == "__main__":
    main()
