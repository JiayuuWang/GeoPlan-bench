# GeoPlan Benchmark Architecture Documentation

This document describes the system architecture, module design, and data flow of GeoPlan Benchmark.

## Table of Contents

- [System Architecture Overview](#system-architecture-overview)
- [Module Description](#module-description)
- [Data Flow](#data-flow)
- [Design Patterns](#design-patterns)

## System Architecture Overview

GeoPlan Benchmark adopts a modular design with the following core modules:

```
┌─────────────────────────────────────────────────────────────┐
│                    GeoPlan Benchmark                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Task         │  │ Task         │  │ Task         │    │
│  │ Generation   │→ │ Filtering   │→ │ Evaluation   │    │
│  │ Pipeline     │  │ Pipeline     │  │ Pipeline     │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│         │                  │                  │            │
│         └──────────────────┴──────────────────┘            │
│                            │                                │
│                   ┌────────▼────────┐                      │
│                   │  Data Storage    │                      │
│                   │      Layer       │                      │
│                   └─────────────────┘                      │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Agent      │  │  Evaluation  │  │    Tools      │    │
│  │    Layer     │  │    Layer     │  │    Layer     │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

1. **Pipeline Layer**: Pipelines for task generation, filtering, and evaluation
2. **Agent Layer**: Multiple agent architecture implementations
3. **Evaluation Layer**: Evaluation metric computation
4. **Tools Layer**: Remote sensing toolset
5. **Data Layer**: Data management and filtering

## Module Description

### 1. Pipeline Module

#### 1.1 Task Generation Pipeline (task_generation.py)

The task generation pipeline is responsible for creating diverse remote sensing tasks.

**Main Classes**:

- `DAGTaskTemplateGenerator`: DAG template generator
  - Uses Gemini model to generate task dependency graphs
  - Outputs DAG structure with nodes and edges

- `ToolFlowGenerator`: Tool flow generator
  - Extracts linear tool calling sequences from DAGs
  - Uses NetworkX to find longest paths

- `ToolFlowParameterizer`: Tool flow parameterizer
  - Adds specific parameters to tool flows
  - Ensures parameter logical consistency

- `TaskGenerator`: Task generator
  - Generates natural language questions based on parameterized tool flows
  - Uses Gemini model to generate questions

- `RemoteSensingTaskPipeline`: Main pipeline
  - Coordinates the above components to complete the full task generation process

**Data Flow**:
```
Domain + Complexity → DAG Template → Tool Flow → Parameterized Tool Flow → Task Question
```

#### 1.2 Task Evaluation Pipeline (task_evaluation.py)

The task evaluation pipeline is responsible for evaluating agent performance on tasks.

**Main Classes**:

- `RemoteSensingTaskEval`: Evaluator
  - Loads tasks
  - Runs multiple agents
  - Computes evaluation metrics
  - Saves results

**Evaluation Process**:
```
Task → Run Agents → Compute Metrics → Save Results
```

### 2. Agent Module

#### 2.1 Base Architecture

All agents inherit from the `BaseAgent` base class and implement the following interfaces:

- `run(query: str) -> str`: Run the agent and return results
- `run_and_return_tool_trajectory(query: str) -> List[str]`: Run and return tool trajectory

#### 2.2 Agent Types

**ReAct (Reasoning + Acting)**
- Reasoning-acting loop architecture
- Alternates between thinking, acting, and observing
- Suitable for tasks requiring multi-step reasoning

**Plan-and-Execute**
- Planning-execution separation architecture
- Plans first, then executes
- Suitable for tasks requiring global planning

**EarthAgent**
- Hierarchical expert architecture
- Three-layer expert system: data acquisition, preprocessing, analysis
- Optimized for remote sensing tasks

**Debate**
- Multi-agent debate architecture
- Multiple agents discuss to improve solutions
- Improves quality through debate

**CoT (Chain of Thought)**
- Zero-shot chain-of-thought architecture
- Explicit reasoning process
- Improves reasoning transparency

**AFlow (Adaptive Flow)**
- Adaptive flow architecture
- Dynamically adjusts tool calling order
- Improves flow through verification and optimization

### 3. Evaluation Module

#### 3.1 Evaluation Metrics

**CorrectnessEvaluator (Correctness Evaluation)**
- Key step extraction: Extracts key steps from ground truth tool flow
- Key tool extraction: Extracts key tools from agent tool flow
- Computes recall, precision, and F1 score

**StructuralEvaluator (Structural Evaluation)**
- Tool similarity computation: Based on tool semantic similarity
- Enhanced edit distance: Edit distance considering tool importance
- Tool flow similarity: Sequence-level similarity

**HolisticEvaluator (Holistic Evaluation)**
- Elo ranking system: Pairwise comparison of agent solutions
- LLM Judge: Uses LLM to judge solution completeness
- Completeness score: Completeness metric based on Elo rating

#### 3.2 Evaluation Process

```
Agent Tool Flow + Ground Truth Tool Flow + Question
    ↓
Extract Key Steps/Tools
    ↓
Compute Metrics
    ↓
Return Evaluation Results
```

### 4. Tools Module

#### 4.1 Tool Categories

**Data Acquisition Tools**
- `download_satellite_imagery`: Download satellite imagery
- `web_search`: Web search
- `read_database`: Read database
- `get_weather_data`: Get weather data

**Data Preprocessing Tools**
- `geometric_correction`: Geometric correction
- `atmospheric_correction`: Atmospheric correction
- `cloud_mask_removal`: Cloud mask removal
- `resize_image`: Image resizing
- `crop_image`: Image cropping

**Analysis Tools**
- `classify_land_cover`: Land cover classification
- `segment_water_bodies`: Water body segmentation
- `monitor_crop_health`: Crop health monitoring
- `detect_plant_diseases`: Plant disease detection
- `assess_disaster_damage`: Disaster damage assessment

**Output Tools**
- `generate_analysis_reports`: Generate analysis reports
- `format_data`: Format data
- `statistical_analysis`: Statistical analysis

#### 4.2 Tool Registration

Tools are defined as functions, and agents register tools through the `add_tool()` method.

### 5. Data Module

#### 5.1 Task Filtering

**Filtering Steps**:
1. Tool flow filtering: Remove empty tool flows
2. Complexity filtering: Ensure tool flow length matches complexity
3. Domain filtering: Check question relevance to domain
4. Semantic deduplication: Use SentenceTransformer to remove duplicate questions

**Filtering Statistics**:
- Records statistics for each filtering step
- Generates domain and complexity distribution reports

#### 5.2 Data Schemas

Uses Pydantic to define data schemas:
- `EloAnswerSchema`: Elo evaluation answer schema
- `ComplexityChoiceSchema`: Complexity choice schema
- `PlanSchema`: Plan schema

## Data Flow

### Task Generation Data Flow

```
1. Input: Domain, Complexity
   ↓
2. DAG Template Generation (Gemini)
   ↓
3. Tool Flow Extraction (NetworkX)
   ↓
4. Tool Flow Parameterization (GPT)
   ↓
5. Question Generation (Gemini)
   ↓
6. Output: Task JSON File
```

### Task Filtering Data Flow

```
1. Input: Raw Task Files
   ↓
2. Tool Flow Filtering
   ↓
3. Complexity Filtering
   ↓
4. Domain Filtering
   ↓
5. Semantic Deduplication (SentenceTransformer)
   ↓
6. Output: Filtered Tasks + Statistics Report
```

### Task Evaluation Data Flow

```
1. Input: Filtered Tasks
   ↓
2. Load Tasks
   ↓
3. For Each Task:
   ├─ Run ReAct Agent
   ├─ Run Plan-and-Execute Agent
   ├─ Run EarthAgent
   ├─ Run Debate Agent
   ├─ Run CoT Agent
   └─ Run AFlow Agent
   ↓
4. Compute Evaluation Metrics:
   ├─ Correctness Metrics
   ├─ Structural Metrics
   └─ Holistic Metrics
   ↓
5. Save Evaluation Results
```

## Design Patterns

### 1. Strategy Pattern

Different agents implement different strategies:
- `BaseAgent` defines the interface
- Various agents implement specific strategies

### 2. Template Method Pattern

Pipelines use the template method pattern:
- Defines algorithm skeleton
- Subclasses implement specific steps

### 3. Factory Pattern

Agent creation uses factory functions:
- `create_react_agent()`
- `create_earth_agent()`
- etc.

### 4. Observer Pattern

The evaluation process can be viewed as an observer pattern:
- Tasks are the observed objects
- Agents are observers
- Evaluation metrics are observation results

## Extensibility

### Adding New Agents

1. Inherit from `BaseAgent` base class
2. Implement `run()` and `run_and_return_tool_trajectory()` methods
3. Add creation function in `utils/arena.py`
4. Integrate in `task_evaluation.py`

### Adding New Evaluation Metrics

1. Create new evaluator class
2. Implement evaluation methods
3. Integrate in `task_evaluation.py`
4. Update result saving format

### Adding New Tools

1. Define tool function in `tools/tools.py`
2. Add docstring
3. Tools are automatically discovered and used by agents

## Performance Considerations

### 1. API Call Optimization

- Batch processing to reduce API call count
- Use progress bars to show processing progress
- Error handling and retry mechanisms

### 2. Caching Mechanism

- Cache tool similarity computation results
- Cache tool importance analysis

### 3. Concurrent Processing

- Can run multiple agents in parallel
- Can evaluate multiple tasks in parallel

## Dependencies

```
geoplan_bench
├── agents (depends on tools, config)
├── evaluation (depends on agents, config)
├── pipeline (depends on agents, evaluation, data, tools, config)
├── data (depends on config)
├── tools (no dependencies)
├── utils (depends on agents, tools)
└── config (no dependencies)
```

## Configuration Management

Configuration is centralized in the `config/` directory:
- `constants.py`: Constant definitions (domains, complexities, etc.)
- `prompts.py`: Prompt templates

Environment variables are managed through `.env` file:
- API keys
- Model selection
- Other configurations
