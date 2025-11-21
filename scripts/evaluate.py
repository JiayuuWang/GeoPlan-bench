"""
Script to evaluate agents on tasks for GeoPlan Benchmark.
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geoplan_bench.pipeline.task_evaluation import execute_task_evaluation_pipeline


def main():
    parser = argparse.ArgumentParser(description="Evaluate agents on tasks")
    parser.add_argument(
        "--start-index",
        type=int,
        default=0,
        help="Start task index"
    )
    parser.add_argument(
        "--end-index",
        type=int,
        default=None,
        help="End task index (inclusive)"
    )
    
    args = parser.parse_args()
    
    print("Starting evaluation pipeline...")
    print(f"Task range: [{args.start_index}:{args.end_index}]")
    
    execute_task_evaluation_pipeline(
        start_from_task_index=args.start_index,
        end_to_task_index=args.end_index
    )
    
    print("Evaluation completed!")


if __name__ == "__main__":
    main()
