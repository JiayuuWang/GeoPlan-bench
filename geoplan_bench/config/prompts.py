# Prompt templates for task generation and evaluation

DAG_TEMPLATE_PROMPT = """Generate a typical task dependency template for remote sensing {domain} domain, represented as a Directed Acyclic Graph (DAG):

Domain application scope: {domain_desc}

Available tools:
{tools_str}

Requirements:
1. Select {tools_number_range} most relevant tools based on actual needs in {domain} domain
2. Define reasonable dependencies based on tool functionality and data flow
3. Form a DAG structure that follows actual remote sensing analysis workflow
4. Include complete analysis process from data acquisition to result output
5. Dependencies should reflect real remote sensing workflows
6. Focus on typical task requirements within the above domain scope

Output in JSON format:
{{
  "domain": "{domain}",
  "nodes": ["tool1", "tool2", "tool3", ...],
  "edges": [["source_tool_1", "target_tool_1"], ["source_tool_2", "target_tool_2"], ...],
  "description": "DAG template based on actual needs in {domain} domain"
}}"""

PARAMETERIZE_FLOW_PROMPT = """Complete parameters for the tool flow to generate instantiated tool calls:

Tool sequence: {tools}

Tool details:
{tools_str}

Requirements:
1. Use imagination to complete specific parameters for each tool
2. Parameters should fit remote sensing application scenarios
3. Maintain logical consistency between parameters
4. Generate realistic and credible parameter values

Output in JSON format:
{{
  "parameterized_tools": [
    {{"tool": "tool1", "params": {{"param1": "value1", "param2": "value2"}}}},
    {{"tool": "tool2", "params": {{"param1": "value1", "param2": "value2"}}}}
  ]
}}"""

GENERATE_TASK_PROMPT = """Generate a remote sensing analysis task based on the instantiated tool flow:

Tool call sequence:
{flow_str}

Requirements:
1. Question should be short and direct, focusing on one core objective
2. Leverage your imagination to generate a question that is highly contextual with specific entry point.
3. Do not explicitly mention any data sources
4. Do not mention specific technical methods or tools
5. Let agent infer what data and methods are needed
6. Question should have implicit complexity requiring deep analysis
7. Question should be specific and detailed, not a broad topic

Output concise core question as a string (one sentence):
"""

KEY_STEPS_EXTRACTION_PROMPT = """
Task question: {question}
Ground truth tool path: {ground_truth_tool_flow}

Please identify the key steps (indispensable steps) from the golden path to solve this problem.
Key steps should be core operations essential for task completion, removing optional or redundant steps.

Requirements:
1. Select the most critical steps from the given tool path
2. Key steps should be indispensable for task completion
3. Remove duplicate or redundant steps
4. Don't return an empty list

Return strictly in the following JSON format without any additional explanation:
{{
  "key_steps": ["step1", "step2", "step3"]
}}
"""

KEY_TOOLS_EXTRACTION_PROMPT="""
Task question: {question}
Agent's tool path: {agent_tool_flow}

Please identify the key tools (indispensable tools) from the agent's tool path to solve this problem.
Key tools should be core operations essential for task completion, removing optional or redundant tools.

Requirements:
1. Select the most critical different tools from the given tool path
2. Key tools should be indispensable for task completion
3. Remove duplicate or redundant tools
4. Don't return an empty list

Return strictly in the following JSON format without any additional explanation:
{{
  "key_tools": ["tool1", "tool2", "tool3"]
}}
"""

COMPLETENESS_EVALUATION_PROMPT = """
Task question: {question}

Please compare the completeness of the following two agents' tool calling paths:

Agent A ({agent_a}): {tool_flow_a}
Agent B ({agent_b}): {tool_flow_b}

Evaluation criteria:
1. Does it cover all key aspects required by the problem?
2. Are important data acquisition and processing steps missing?
3. Can it achieve the final results required by the problem?
4. Is the overall solution comprehensive?

Please choose one of the following options:
- "A": Agent A has better completeness
- "B": Agent B has better completeness
- "Tie": Both have equivalent completeness

Please **return only one string**: "A" or "B" or "Tie"
"""

# AFLOW agent prompts (from aflow.py)
REFINE_PROMPT = """
Given the problem and initial solution, output a refined tool flow as a list of tool names that can solve the problem. The output must be in the format: ['tool1_name','tool2_name',...].

Consider:
1. The logical sequence of tools
2. Required preprocessing steps
3. Necessary analysis tools
4. Data formatting and output tools

Only output the tool flow list, no other text.
"""

VERIFY_PROMPT = """
Review the current solution and ensure all essential tools for the task type are included. Consider:
1. Data acquisition tools (web_search, download_satellite_imagery)
2. Preprocessing tools (geometric_correction, atmospheric_correction)
3. Analysis tools specific to the task
4. Data formatting and reporting tools

Add any missing essential tools and maintain proper sequence.
Output only the complete tool list in format: ['tool1_name','tool2_name',...]
"""

VALIDATE_FORMAT_PROMPT = """
Validate and correct the tool list to ensure:
1. All remote sensing tasks must include download_satellite_imagery, geometric_correction, atmospheric_correction in correct order
2. Must include cloud_mask_removal after corrections if using satellite imagery
3. Must end with format_data or generate_analysis_reports
4. List must be in exact format: ['tool1_name','tool2_name',...]

Output the corrected list maintaining the exact format, no other text.
"""

FORMAT_PROMPT = """
Format the tool flow into a proper Python list string that matches the expected format.
Rules:
1. Must be in exact format: ['tool1_name','tool2_name',...]
2. No spaces between commas
3. Single quotes for strings
4. Remove any extra whitespace or newlines
5. Include essential tools like format_data or generate_analysis_reports at the end

Only output the formatted list string, no other text.
"""

ANSWER_GENERATION_PROMPT = """
You are an expert in remote sensing task planning. Your goal is to generate an appropriate sequence of tools/operations to solve the given remote sensing task.

Think step by step about what tools and operations are needed:
1. Consider the type of remote sensing task (agriculture, disaster management, environmental monitoring, etc.)
2. Think about the logical sequence of operations (data acquisition, preprocessing, analysis, output)
3. Select appropriate tools for each step

Available tool categories include:
- Data acquisition: download_satellite_imagery, web_search, recommend_satellite_platforms
- Preprocessing: geometric_correction, atmospheric_correction, cloud_mask_removal, crop_image
- Analysis: classify_land_cover, segment_water_bodies, monitor_crop_health, detect_plant_diseases, assess_disaster_damage
- Output: generate_analysis_reports, format_data, statistical_analysis

Task: {input}

In the "thought" field, explain your step-by-step reasoning process.
In the "answer" field, provide a clear sequence of tools/operations needed to complete the task.
"""

SC_ENSEMBLE_PROMPT = """
Several tool flow solutions have been generated for the same remote sensing task planning problem. They are as follows:
{solutions}

Identify the most consistent and appropriate tool flow that appears most frequently across them. Consider the logical sequence of remote sensing operations and the specific requirements of the task.

In the "thought" field, provide a detailed explanation of your analysis process. In the "solution_letter" field, output only the single letter ID (A, B, C, etc.) corresponding to the most consistent solution. Do not include any additional text or explanation in the "solution_letter" field.
"""
