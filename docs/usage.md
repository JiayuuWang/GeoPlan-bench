# GeoPlan Benchmark Usage Guide

This document provides detailed instructions on how to use GeoPlan Benchmark, including the three core functions: task generation, task filtering, and evaluation.

## Table of Contents

- [Environment Setup](#environment-setup)
- [Task Generation](#task-generation)
- [Task Filtering](#task-filtering)
- [Task Evaluation](#task-evaluation)
- [Parameter Configuration](#parameter-configuration)
- [Result Analysis](#result-analysis)

## Environment Setup

### 1. Create a Virtual Environment (Recommended)

```bash
# Create virtual environment (venv or conda):
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
pip install -e .  # Optional, for command-line tools
```

### 3. Configure Environment Variables

Create a `.env` file and configure the following environment variables:

```bash
OPENAI_API_KEY=your_openai_api_key
OPENAI_API_BASE=https://api.openai.com/v1  # Optional
GEMINI_API_KEY=your_gemini_api_key
```


## Task Generation

### Overview

The task generation module automatically creates diverse remote sensing tasks, including:
- DAG template generation: Generates task dependency graphs for each domain-complexity combination
- Tool flow extraction: Extracts linear tool calling sequences from DAGs
- Parameterization: Adds specific parameters to tool flows
- Question generation: Generates natural language questions based on parameterized tool flows

### Usage

#### Command-Line

```bash
geoplan-generate --num-dags 1 --output-dir data/tasks/raw
```

Parameters:
- `--num-dags`: Number of DAG templates to generate per domain-complexity combination (default: 1)
- `--output-dir`: Output directory (default: data/tasks/raw)

#### Python Script

```bash
python scripts/generate_tasks.py --num-dags 1 --output-dir data/tasks/raw
```

#### Programmatic Usage

```python
from geoplan_bench.pipeline.task_generation import RemoteSensingTaskPipeline

pipeline = RemoteSensingTaskPipeline()
pipeline.generate_batch_tasks(num_dags=1)
```

### Generation Process

1. **DAG Template Generation**: Uses Gemini model to generate task dependency graphs
2. **Tool Flow Extraction**: Uses NetworkX to extract longest paths from DAGs
3. **Parameterization**: Uses GPT model to add parameters to tool flows
4. **Question Generation**: Uses Gemini model to generate natural language questions

### Output Format

Generated task files are in JSON format, each task contains:

```json
{
  "task_id": "uuid",
  "dag_template_filename": "dag_template_xxx.json",
  "complexity": "Simple|Medium|Complex",
  "domain": "Domain Name",
  "question": "Natural language question",
  "ground_truth_tool_flow": ["tool1", "tool2", ...]
}
```

### Notes

- Task generation requires LLM API calls and incurs costs
- Generation time depends on the number of tasks and API response speed
- It's recommended to generate a small number of tasks first for testing before batch generation

## Task Filtering

### Overview

The task filtering module performs quality control and deduplication on generated tasks:
- Tool flow filtering: Removes empty or invalid tool flows
- Complexity filtering: Ensures tool flow length matches complexity level
- Domain filtering: Ensures questions are relevant to the domain
- Semantic deduplication: Uses SentenceTransformer to remove semantically similar tasks

### Usage

#### Command-Line

```bash
geoplan-filter --input-dir data/tasks/raw --output-dir data/tasks/filtered
```

Parameters:
- `--input-dir`: Input directory containing raw task files (default: data/tasks/raw)
- `--output-dir`: Output directory for filtered tasks (default: data/tasks/filtered)

#### Python Script

```bash
python scripts/filter_tasks.py --input-dir data/tasks/raw --output-dir data/tasks/filtered
```

#### Programmatic Usage

```python
from geoplan_bench.data.task_filter import filter_tasks
import json
import os

filtered_tasks, stats = filter_tasks('data/tasks/raw')
print(f"Original task count: {stats['original_count']}")
print(f"Filtered task count: {stats['final_count']}")
```

### Filtering Process

1. **Tool Flow Filtering**: Removes empty tool flows (`["empty"]`) or invalid tasks
2. **Complexity Filtering**: Ensures Complex tasks have tool flow length >= 10
3. **Domain Filtering**: Checks if questions contain domain keywords
4. **Semantic Deduplication**: Uses cosine similarity (threshold 0.95) to remove duplicate questions

### Output Statistics

The filtering process outputs detailed statistics:

```
Original task count: 1000
After tool flow filtering: 950
After complexity filtering: 900
After domain filtering: 850
After semantic deduplication: 800
Final task count: 800
Retention rate: 80.0%
```

### Filtering Report

After filtering, a JSON format report file is generated containing:
- Filtering statistics
- Domain distribution
- Complexity distribution

## Task Evaluation

### Overview

The task evaluation module evaluates agent performance on tasks:
- Runs 6 agents: ReAct, Plan-and-Execute, EarthAgent, Debate, CoT, AFlow
- Computes 3 evaluation metrics: Correctness, Structural, Holistic
- Saves detailed evaluation results

### Usage

#### Command-Line

```bash
geoplan-evaluate --start-index 0 --end-index 10
```

Parameters:
- `--start-index`: Starting task index (default: 0)
- `--end-index`: Ending task index (default: None, evaluates all tasks)

#### Python Script

```bash
python scripts/evaluate.py --start-index 0 --end-index 10
```

#### Programmatic Usage

```python
from geoplan_bench.pipeline.task_evaluation import execute_task_evaluation_pipeline

execute_task_evaluation_pipeline(
    start_from_task_index=0,
    end_to_task_index=10
)
```

### Evaluation Process

1. **Load Tasks**: Loads filtered tasks from `data/tasks/filtered` directory
2. **Run Agents**: Runs all 6 agents on each task
3. **Compute Metrics**: Computes correctness, structural, and holistic metrics
4. **Save Results**: Saves evaluation results to `data/eval_results` directory

### Evaluation Metrics Explained

#### 1. Correctness Metrics

- **Key Step Recall**: Proportion of key steps included in agent's tool flow
- **Key Tool Precision**: Overlap ratio between agent's key tools and ground truth key tools
- **F1 Score**: Harmonic mean of precision and recall

#### 2. Structural Metrics

- **Tool Flow Similarity**: Sequence similarity based on tool semantic similarity
- **Enhanced Edit Distance**: Edit distance considering tool importance

#### 3. Holistic Metrics

- **Completeness Score**: Elo ranking-based completeness evaluation

### Output Format

Evaluation results for each task are saved in `data/eval_results/eval_{task_id}.json`:

```json
{
  "task_info": {
    "task_id": "uuid",
    "question": "Question",
    "ground_truth_tool_flow": ["tool1", "tool2", ...]
  },
  "eval_result": {
    "ReAct": {
      "tool_trajectory": ["tool1", "tool2", ...],
      "key_steps": ["step1", "step2"],
      "key_step_recall": 0.8,
      "key_tools": ["tool1", "tool2"],
      "key_tool_precision": 0.75,
      "F1_score": 0.77,
      "enhanced_edit_distance": 2.5,
      "tool_flow_similarity": 0.85,
      "completeness_score": 1050
    },
    ...
  }
}
```

### Notes

- Evaluation requires LLM API calls and incurs costs
- Evaluation takes a long time, it's recommended to use `--start-index` and `--end-index` for batch evaluation

## Parameter Configuration

### Task Generation Parameters

- `num_dags`: Number of DAGs per domain-complexity combination
- `model`: LLM model to use (default: gpt-4o-mini)

### Task Filtering Parameters

- `similarity_threshold`: Semantic similarity threshold (default: 0.95)
- `complexity_min_length`: Minimum tool flow length for Complex tasks (default: 10)

### Evaluation Parameters

- `start_from_task_index`: Starting task index
- `end_to_task_index`: Ending task index
- `model`: LLM model to use (default: gpt-4o-mini)

## Result Analysis

### Viewing Evaluation Results

```python
import json
import os

results_dir = "data/eval_results"
for filename in os.listdir(results_dir):
    if filename.startswith('eval_'):
        with open(os.path.join(results_dir, filename), 'r') as f:
            result = json.load(f)
            print(f"Task: {result['task_info']['question']}")
            for agent_name, metrics in result['eval_result'].items():
                print(f"  {agent_name}: F1={metrics['F1_score']:.2f}")
```

### Statistical Analysis

You can write scripts to analyze:
- Average metrics for each agent
- Performance across different domains and complexities
- Metric distributions

## FAQ

### Q: What if task generation fails?

A: Check if API keys are correctly configured and network connection is normal. Try reducing the `num_dags` parameter.

### Q: Very few tasks after filtering?

A: You can adjust filtering thresholds or check the quality of generated tasks.

### Q: Evaluation is very slow?

A: Evaluation requires multiple LLM API calls, speed depends on API response time. You can evaluate in batches or use faster models. It is recommended for you to implement your asynchronous evaluation pipeline to speed up the process.

### Q: How to add custom agents?

A: Refer to `examples/example_custom_agent.py` example code.

### Q: How to add custom evaluation metrics?

A: Refer to `examples/example_custom_metric.py` example code.
