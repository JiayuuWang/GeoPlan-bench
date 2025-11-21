"""
tool importance analyzer
based on global dependency graph to calculate the out-degree centrality and PageRank score of tools
"""

import json
import networkx as nx
from typing import Dict, List, Tuple
from datetime import datetime
import os
import matplotlib.pyplot as plt


class ToolImportanceAnalyzer:
    """tool importance analyzer"""
    
    def __init__(self, base_cost: float = 1.0, alpha: float = 1.0):
        """
        initialize analyzer
        
        Args:
            base_cost: base cost
            alpha: PageRank weight adjustment coefficient
        """
        self.base_cost = base_cost
        self.alpha = alpha
        self.global_graph = nx.DiGraph()
        self.dag_templates = []
        self.tool_importance_scores = {}
        self.output_dir = "data/tasks/filter_info"
        

    
    def load_templates(self, dir_path: str = "dag_templates") -> List[Dict]:
        """load DAG templates from directory"""
        self.dag_templates = []
        for file in os.listdir(dir_path):
            if file.endswith(".json"):
                with open(os.path.join(dir_path, file), "r") as f:
                    self.dag_templates.append(json.load(f))
        return self.dag_templates
    
    def load_tasks_from_directory(self, task_dir: str = "data/tasks/filtered") -> List[Dict]:
        """load tasks from directory and extract tool flows"""
        tasks = []
        if not os.path.exists(task_dir):
            print(f"Warning: Task directory not found: {task_dir}")
            return tasks
        
        for filename in os.listdir(task_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(task_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        task = json.load(f)
                        if isinstance(task, dict) and 'ground_truth_tool_flow' in task:
                            tool_flow = task['ground_truth_tool_flow']
                            if isinstance(tool_flow, list) and len(tool_flow) > 0:
                                tasks.append(task)
                except Exception as e:
                    print(f"Warning: Failed to load task from {filename}: {e}")
        
        print(f"Loaded {len(tasks)} tasks from {task_dir}")
        return tasks
    
    def build_graph_from_tool_flows(self, tasks: List[Dict]) -> nx.DiGraph:
        """build dependency graph from task tool flows"""
        print("Building dependency graph from tool flows...")
        self.global_graph = nx.DiGraph()
        
        edge_weights = {}
        
        for task in tasks:
            tool_flow = task.get('ground_truth_tool_flow', [])
            if not isinstance(tool_flow, list) or len(tool_flow) < 2:
                continue
            
            for i in range(len(tool_flow) - 1):
                source = tool_flow[i]
                target = tool_flow[i + 1]
                
                if source is None or target is None:
                    continue
                
                if not self.global_graph.has_node(source):
                    self.global_graph.add_node(source)
                if not self.global_graph.has_node(target):
                    self.global_graph.add_node(target)
                
                edge_key = (source, target)
                if edge_key not in edge_weights:
                    edge_weights[edge_key] = 0
                edge_weights[edge_key] += 1
        
        for (source, target), weight in edge_weights.items():
            self.global_graph.add_edge(source, target, weight=weight)
        
        print(f"Dependency graph built:")
        print(f"  - number of nodes: {self.global_graph.number_of_nodes()}")
        print(f"  - number of edges: {self.global_graph.number_of_edges()}")
        
        return self.global_graph
    
    def build_global_dependency_graph(self) -> nx.DiGraph:
        """
        build global dependency graph
        merge all DAG templates into a global graph
        
        Returns:
            global dependency graph
        """
        print("building global dependency graph...")
        self.global_graph = nx.DiGraph()
        
        # count the weight of edges (frequency)
        edge_weights = {}
        
        for template in self.dag_templates:
            if template is None or 'nodes' not in template or 'edges' not in template:
                continue
                
            # add nodes
            for node in template['nodes']:
                if node is not None and not self.global_graph.has_node(node):
                    self.global_graph.add_node(node)
            
            # add edges and count the weight
            for edge in template['edges']:
                if len(edge) >= 2:
                    source, target = edge[0], edge[1]
                    
                    # check if the node is None
                    if source is None or target is None:
                        continue
                        
                    edge_key = (source, target)
                    
                    # count the frequency of edges
                    if edge_key not in edge_weights:
                        edge_weights[edge_key] = 0
                    edge_weights[edge_key] += 1
            
        # add edges to the graph, the weight is the frequency
        for (source, target), weight in edge_weights.items():
            self.global_graph.add_edge(source, target, weight=weight)
        
        print(f"global dependency graph built:")
        print(f"  - number of nodes: {self.global_graph.number_of_nodes()}")
        print(f"  - number of edges: {self.global_graph.number_of_edges()}")
        
        return self.global_graph
    def visualize_global_dependency_graph(self):
        """
        visualize global dependency graph
        """
        nx.draw(self.global_graph, with_labels=True)
        plt.show()
    
    def calculate_out_degree_centrality(self) -> Dict[str, float]:
        """
        calculate out-degree centrality
        
        Returns:
            tool name to out-degree centrality mapping
        """
        print("calculating out-degree centrality...")
        
        # calculate the out-degree of each node
        out_degrees = dict(self.global_graph.out_degree())
        
        if not out_degrees:
            return {}
        
        # normalize
        max_out_degree = max(out_degrees.values()) if out_degrees.values() else 1
        normalized_out_degrees = {
            node: degree / max_out_degree 
            for node, degree in out_degrees.items()
        }
        
        print(f"out-degree centrality calculated, max out-degree: {max_out_degree}")
        return normalized_out_degrees
    
    def calculate_pagerank_centrality(self, alpha: float = 0.85, max_iter: int = 100) -> Dict[str, float]:
        """
        calculate PageRank centrality
        
        Args:
            alpha: damping factor
            max_iter: maximum number of iterations
            
        Returns:
            tool name to PageRank score mapping
        """
        print("calculating PageRank centrality...")
        
        if self.global_graph.number_of_nodes() == 0:
            return {}
        
        try:
            # use edge weights to calculate PageRank
            pagerank_scores = nx.pagerank(
                self.global_graph, 
                alpha=alpha, 
                max_iter=max_iter,
                weight='weight'
            )
            print(f"PageRank centrality calculated")
            return pagerank_scores
        except Exception as e:
            print(f"PageRank calculation failed: {e}")
            return {}
    
    def calculate_tool_importance(self) -> Dict[str, Dict[str, float]]:
        """
        calculate tool importance score
        
        Returns:
            dictionary containing various importance metrics
        """
        
        # calculate various centrality metrics
        out_degree_scores = self.calculate_out_degree_centrality()
        pagerank_scores = self.calculate_pagerank_centrality()
        
        # merge results
        all_tools = set(out_degree_scores.keys()) | set(pagerank_scores.keys())
        
        importance_scores = {}
        for tool in all_tools:
            out_degree = out_degree_scores.get(tool, 0.0)
            pagerank = pagerank_scores.get(tool, 0.0)
            
            # calculate deletion/insertion cost
            out_degree_cost = self.base_cost * (1 + out_degree)
            pagerank_cost = self.base_cost * (1 + self.alpha * pagerank)
            
            importance_scores[tool] = {
                'out_degree_centrality': out_degree,
                'pagerank_centrality': pagerank,
                'out_degree_cost': out_degree_cost,
                'pagerank_cost': pagerank_cost,
                'combined_importance': (out_degree + pagerank) / 2,  # combined importance
                'combined_cost': (out_degree_cost + pagerank_cost) / 2  # combined cost
            }
        
        self.tool_importance_scores = importance_scores
        print(f"tool importance calculated, total analyzed tools: {len(importance_scores)}")
        return importance_scores
    
    def get_top_important_tools(self, n: int = 20, metric: str = 'combined_importance') -> List[Tuple[str, float]]:
        """
        get the most important N tools
        
        Args:
            n: number of tools to return
            metric: sorting metric
            
        Returns:
            list of (tool name, importance score), sorted by importance in descending order
        """
        if not self.tool_importance_scores:
            self.calculate_tool_importance()
        
        tools_with_scores = [
            (tool, scores[metric]) 
            for tool, scores in self.tool_importance_scores.items()
        ]
        
        # sort by importance in descending order
        tools_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        return tools_with_scores[:n]
    
    def save_importance_analysis(self, filepath: str = "tool_importance_analysis.json", source: str = "dag_templates"):
        """save importance analysis result"""
        analysis_result = {
            'analysis_metadata': {
                'generated_at': datetime.now().isoformat(),
                'source': source,
                'total_templates': len(self.dag_templates) if source == "dag_templates" else 0,
                'total_tasks': len(self.dag_templates) if source == "tasks" else 0,
                'total_tools': len(self.tool_importance_scores),
                'graph_nodes': self.global_graph.number_of_nodes(),
                'graph_edges': self.global_graph.number_of_edges(),
                'base_cost': self.base_cost,
                'alpha': self.alpha
            },
            'tool_importance_scores': self.tool_importance_scores,
            'top_tools_by_combined_importance': self.get_top_important_tools(20, 'combined_importance'),
            'top_tools_by_out_degree': self.get_top_important_tools(20, 'out_degree_centrality'),
            'top_tools_by_pagerank': self.get_top_important_tools(20, 'pagerank_centrality')
        }
        filepath = os.path.join(self.output_dir, filepath)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        
        print(f"importance analysis result saved to: {filepath}")
    
    def print_analysis_summary(self):
        """Print analysis summary"""
        if not self.tool_importance_scores:
            print("Importance analysis has not been performed yet")
            return
        
        print("\n" + "="*80)
        print("Tool Importance Analysis Summary")
        print("="*80)
        
        print(f"Number of DAG templates analyzed: {len(self.dag_templates)}")
        print(f"Global graph node count: {self.global_graph.number_of_nodes()}")
        print(f"Global graph edge count: {self.global_graph.number_of_edges()}")
        print(f"Number of tools analyzed: {len(self.tool_importance_scores)}")
        
        print(f"\nTop 10 tools by combined importance:")
        for i, (tool, score) in enumerate(self.get_top_important_tools(10, 'combined_importance'), 1):
            print(f"  {i:2d}. {tool:<40} {score:.4f}")
        
        print(f"\nTop 10 tools by out-degree centrality:")
        for i, (tool, score) in enumerate(self.get_top_important_tools(10, 'out_degree_centrality'), 1):
            print(f"  {i:2d}. {tool:<40} {score:.4f}")
        
        print(f"\nTop 10 tools by PageRank:")
        for i, (tool, score) in enumerate(self.get_top_important_tools(10, 'pagerank_centrality'), 1):
            print(f"  {i:2d}. {tool:<40} {score:.4f}")

def analyze_tool_importance_from_tasks(task_dir: str = "data/tasks/filtered"):
    """analyze tool importance from filtered tasks"""
    analyzer = ToolImportanceAnalyzer(base_cost=1.0, alpha=1.0)
    tasks = analyzer.load_tasks_from_directory(task_dir)
    if not tasks:
        print(f"Warning: No tasks found in {task_dir}, skipping tool importance analysis")
        return analyzer
    
    analyzer.dag_templates = tasks
    analyzer.build_graph_from_tool_flows(tasks)
    analyzer.calculate_tool_importance()
    analyzer.save_importance_analysis(source="tasks")
    return analyzer


def main():
    """main function, analyze tool importance"""
    print("start analyze tool importance...")
    
    # create analyzer
    analyzer = ToolImportanceAnalyzer(base_cost=1.0, alpha=1.0)
    
    analyzer.load_templates(dir_path="dag_templates")

    # build global dependency graph
    analyzer.build_global_dependency_graph()
    
    
    # calculate tool importance
    analyzer.calculate_tool_importance()
    
    # save analysis result
    analyzer.save_importance_analysis()
    
    # print summary
    analyzer.print_analysis_summary()
    
    print("\n Tool importance analysis completed!")


if __name__ == "__main__":
    main()
