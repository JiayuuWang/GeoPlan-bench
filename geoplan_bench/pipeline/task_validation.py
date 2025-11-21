import json
import os
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from geoplan_bench.config.constants import DOMAIN_KEYWORDS, DOMAINS


def load_all_tasks(tasks_dir="tasks"):
    """Load all task files"""
    all_tasks = []
    for filename in os.listdir(tasks_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(tasks_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                task = json.load(f)
                all_tasks.append(task)
    return all_tasks


def is_domain_relevant(question, domain):
    """Check if question is relevant to the domain"""
    domain_keywords = DOMAIN_KEYWORDS
    
    keywords = domain_keywords.get(domain, [])
    question_lower = question.lower()
    
    # If question contains keywords for this domain, consider it relevant
    for keyword in keywords:
        if keyword in question_lower:
            return True
    return False


def is_complexity_relevant(ground_truth_tool_flow, complexity):
    """Check if tool flow is relevant to complexity"""
    if complexity == "Complex":
        if len(ground_truth_tool_flow) < 10:
            return False
    return True


def filter_tasks(task_dir="data/tasks/raw"):
    """Execute task filtering"""
    print("Starting task filtering...")
    tasks = []
    if os.path.exists(task_dir):
        for filename in os.listdir(task_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(task_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    task = json.load(f)
                    tasks.append(task)
    else:
        raise FileNotFoundError(f"Task directory not found: {task_dir}")
    # 1. Filter out "empty" strings and tasks with ground_truth_tool_flow as ["empty"]
    tool_flow_filtered = []
    for task in tasks:
        # Skip "empty" strings
        if isinstance(task, str) and task == "empty":
            continue
        # Ensure task is a dict and contains required fields
        if isinstance(task, dict) and 'ground_truth_tool_flow' in task:
            tool_flow = task['ground_truth_tool_flow']
            if tool_flow != ["empty"] and len(tool_flow) > 0:
                tool_flow_filtered.append(task)

    
    print(f"Tool flow filtering: {len(tasks)} -> {len(tool_flow_filtered)}")
    # 2. Filter out tasks where ground_truth_tool_flow doesn't match complexity
    complexity_filtered = []
    for task in tool_flow_filtered:
        if is_complexity_relevant(task['ground_truth_tool_flow'], task['complexity']) and task['domain'] in DOMAINS:
            complexity_filtered.append(task)
    
    print(f"Complexity relevance filtering: {len(tool_flow_filtered)} -> {len(complexity_filtered)}")
    
    # 3. Filter out tasks where question doesn't match domain
    domain_filtered = []
    for task in complexity_filtered:
        if is_domain_relevant(task['question'], task['domain']):
            domain_filtered.append(task)
    
    print(f"Domain relevance filtering: {len(complexity_filtered)} -> {len(domain_filtered)}")
    
    # 4. Use SentenceTransformer to filter semantically duplicate questions
    print("Loading SentenceTransformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    questions = [task['question'] for task in domain_filtered]
    print("Computing question embeddings...")
    embeddings = model.encode(questions)
    
    # Compute similarity matrix
    similarity_matrix = cosine_similarity(embeddings)
    
    # Filter semantically duplicate questions
    threshold = 0.95
    to_remove = set()
    
    for i in range(len(similarity_matrix)):
        for j in range(i + 1, len(similarity_matrix)):
            if similarity_matrix[i][j] > threshold:
                to_remove.add(j)  # Remove later duplicate items
    
    semantic_filtered = [task for i, task in enumerate(domain_filtered) if i not in to_remove]
    
    print(f"Semantic deduplication filtering: {len(domain_filtered)} -> {len(semantic_filtered)}")
    
    return semantic_filtered, {
        'original_count': len(tasks),
        'domain_filtered_count': len(domain_filtered),
        'complexity_filtered_count': len(complexity_filtered),
        'tool_flow_filtered_count': len(tool_flow_filtered),
        'final_count': len(semantic_filtered),
        'removed_by_domain': len(complexity_filtered) - len(domain_filtered),
        'removed_by_complexity': len(tool_flow_filtered) - len(complexity_filtered),
        'removed_by_tool_flow': len(tasks) - len(tool_flow_filtered),
        'removed_by_semantic': len(domain_filtered) - len(semantic_filtered)
    }


def generate_report(stats, filtered_tasks):
    """Generate filtering report"""
    report = {
        'filtering_report': {
            'timestamp': datetime.now().isoformat(),
            'statistics': stats,
            'domain_distribution': {},
            'complexity_distribution': {}
        }
    }
    
    # Count domain distribution
    for task in filtered_tasks:
        domain = task['domain']
        complexity = task['complexity']
        
        if domain not in report['filtering_report']['domain_distribution']:
            report['filtering_report']['domain_distribution'][domain] = 0
        report['filtering_report']['domain_distribution'][domain] += 1
        
        if complexity not in report['filtering_report']['complexity_distribution']:
            report['filtering_report']['complexity_distribution'][complexity] = 0
        report['filtering_report']['complexity_distribution'][complexity] += 1
    
    return report


def main():
    # Load all tasks
    all_tasks = load_all_tasks()
    print(f"Total tasks loaded: {len(all_tasks)}")
    
    # Execute filtering
    filtered_tasks, stats = filter_tasks(all_tasks)
    
    # Generate report
    report = generate_report(stats, filtered_tasks)
    
    # Save filtered tasks to tasks/filtered_tasks directory, replace existing files if any
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if not os.path.exists("data/tasks/filter_info"):
        os.makedirs("data/tasks/filter_info")
    if not os.path.exists("data/tasks/filtered"):
        os.makedirs("data/tasks/filtered")
    # Replace existing files if any
    for file in os.listdir("data/tasks/filtered"):
        os.remove(os.path.join("data/tasks/filtered", file))
    filtered_filename = f"tasks_filtered_{timestamp}.json"
    filtered_path = os.path.join("data/tasks/filtered", filtered_filename)
    with open(filtered_path, 'w', encoding='utf-8') as f:
        json.dump(filtered_tasks, f, ensure_ascii=False, indent=2)
    # Backup a copy in filter_info directory
    with open(os.path.join("data/tasks/filter_info", filtered_filename), 'w', encoding='utf-8') as f:
        json.dump(filtered_tasks, f, ensure_ascii=False, indent=2)
    
    # Save report to filter_info directory
    if not os.path.exists("data/tasks/filter_info"):
        os.makedirs("data/tasks/filter_info")
    report_filename = f"filtering_report_{timestamp}.json"
    report_filename = os.path.join("data/tasks/filter_info", report_filename)
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # Print summary report
    print("\n" + "="*60)
    print("Task Filtering Report")
    print("="*60)
    print(f"Original task count: {stats['original_count']}")
    print(f"Removed by domain: {stats['removed_by_domain']}")
    print(f"Removed by tool flow: {stats['removed_by_tool_flow']}")
    print(f"Removed by semantic similarity: {stats['removed_by_semantic']}")
    print(f"Final task count: {stats['final_count']}")
    print(f"Retention rate: {stats['final_count']/stats['original_count']*100:.1f}%")
    
    print(f"\nDomain distribution:")
    for domain, count in report['filtering_report']['domain_distribution'].items():
        print(f"  {domain}: {count}")
    
    print(f"\nComplexity distribution:")
    for complexity, count in report['filtering_report']['complexity_distribution'].items():
        print(f"  {complexity}: {count}")
    
    print(f"\nFiltered tasks saved to: {filtered_filename}")
    print(f"Detailed report saved to: {report_filename}")


if __name__ == "__main__":
    main()