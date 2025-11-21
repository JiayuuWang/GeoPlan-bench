
"""
Enhanced Edit Distance Calculator
Edit distance calculation integrated with tool similarity and importance analysis
"""
import os
import re
import json
from typing import List, Dict, Tuple, Union

from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer


class StructuralEvaluator:
    """Structural evaluator"""
    
    def __init__(self):
        """
        Initialize evaluator
        
        Args:
        """
        self.tool_similarity_cache = {}
        self.tool_descriptions = self._extract_tool_descriptions()
        self.sentence_model = None
        self.tool_embeddings = None
        self._build_similarity_model()
        
    def _extract_tool_descriptions(self) -> Dict[str, str]:
        """Extract tool description information"""
        tool_descriptions = {}
        
        # Get all functions and their docstrings from tools module
        try:
            from geoplan_bench.tools import remote_sensing, data_processing
            import geoplan_bench.tools as tools
        except ImportError:
            try:
                import tools
            except ImportError:
                # If tools module not available, return empty dict
                return {}
        import inspect
        for name, func in inspect.getmembers(tools, inspect.isfunction):
            if not name.startswith('_') and hasattr(func, '__doc__') and func.__doc__:
                # Clean tool name and description
                clean_name = self._clean_tool_name(name)
                clean_desc = func.__doc__.strip() if func.__doc__ else ""
                tool_descriptions[name] = f"{clean_name} {clean_desc}"
        
        return tool_descriptions
    def _parse_tool_flow(self, tool_flow: Union[List[str], str]) -> List[str]:
        """Parse tool flow to list format"""
        if isinstance(tool_flow, list):
            return tool_flow
        elif isinstance(tool_flow, str):
            # If string, try to parse as JSON or split by comma
            import json
            try:
                return json.loads(tool_flow)
            except:
                return [t.strip() for t in tool_flow.split(',') if t.strip()]

    
    def _clean_tool_name(self, tool_name: str) -> str:
        """Clean tool name for semantic analysis"""
        # Replace underscores with spaces, split camelCase
        clean_name = re.sub(r'_', ' ', tool_name)
        clean_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', clean_name)
        return clean_name.lower()
    
    def _build_similarity_model(self):
        """Build tool semantic similarity model""" 
        tool_names = list(self.tool_descriptions.keys())
        descriptions = [self.tool_descriptions[name] for name in tool_names]
        self.sentence_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.tool_embeddings = self.sentence_model.encode(descriptions)
        self.tool_name_to_index = {name: i for i, name in enumerate(tool_names)}
    
    def calculate_tool_similarity(self, tool_a: str, tool_b: str) -> float:
        """
        Calculate semantic similarity between two tools
        
        Args:
            tool_a: Tool A name
            tool_b: Tool B name
            
        Returns:
            Similarity score (0-1)
        """
        if tool_a == tool_b:
            return 1.0
        
        # Check cache
        cache_key = tuple(sorted([tool_a, tool_b]))
        if cache_key in self.tool_similarity_cache:
            return self.tool_similarity_cache[cache_key]
        
        similarity = 0.0
        
        # Cosine similarity based on semantic embeddings
        if self.tool_embeddings is not None and tool_a in self.tool_name_to_index and tool_b in self.tool_name_to_index:
            idx_a = self.tool_name_to_index[tool_a]
            idx_b = self.tool_name_to_index[tool_b]
            
            embedding_a = self.tool_embeddings[idx_a].reshape(1, -1)
            embedding_b = self.tool_embeddings[idx_b].reshape(1, -1)
            
            # Calculate semantic similarity
            cos_sim = cosine_similarity(embedding_a, embedding_b)[0, 0]
            # Map similarity from [-1,1] range to [0,1] range
            similarity = max(0, (cos_sim + 1) / 2)
        
        # Cache result
        self.tool_similarity_cache[cache_key] = similarity
        return similarity
    
    def get_tool_cost(self, tool: str) -> float:
        """Get tool cost from importance analysis, with caching"""
        if not hasattr(self, '_tool_cost_cache'):
            self._tool_cost_cache = {}
            self._importance_analysis = None
        
        if tool in self._tool_cost_cache:
            return self._tool_cost_cache[tool]
        
        if self._importance_analysis is None:
            analysis_path = os.path.join("data/tasks/filter_info", 'tool_importance_analysis.json')
            if not os.path.exists(analysis_path):
                print(f"Warning: Tool importance analysis file not found at {analysis_path}")
                print("Running tool importance analysis...")
                try:
                    from geoplan_bench.utils.importance import analyze_tool_importance_from_tasks
                    analyze_tool_importance_from_tasks("data/tasks/filtered")
                except Exception as e:
                    print(f"Warning: Failed to generate tool importance analysis: {e}")
                    self._tool_cost_cache[tool] = 1.0
                    return 1.0
            
            try:
                with open(analysis_path, 'r', encoding='utf-8') as f:
                    self._importance_analysis = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load tool importance analysis: {e}")
                self._tool_cost_cache[tool] = 1.0
                return 1.0
        
        if tool not in self._importance_analysis.get('tool_importance_scores', {}):
            self._tool_cost_cache[tool] = 1.0
            return 1.0
        
        cost = self._importance_analysis['tool_importance_scores'][tool]['combined_cost']
        self._tool_cost_cache[tool] = cost
        return cost

    def calculate_tool_flow_similarity(self, agent_tool_flow: List[str], ground_truth_tool_flow: List[str]) -> Tuple[float, Dict]:
        """
        Calculate enhanced edit distance
        
        Args:
            agent_tool_flow: Sequence 1 (usually agent path)
            ground_truth_tool_flow: Sequence 2 (usually golden path)
            
        Returns:
            (similarity score, detailed info dict)
        """
        # Parse tool flows if needed
        if not isinstance(agent_tool_flow, list):
            agent_tool_flow = self._parse_tool_flow(agent_tool_flow)
        if not isinstance(ground_truth_tool_flow, list):
            ground_truth_tool_flow = self._parse_tool_flow(ground_truth_tool_flow)
        len1, len2 = len(agent_tool_flow), len(ground_truth_tool_flow)
        # Create dynamic programming matrix
        dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        # Initialize first row and column (insertion/deletion costs)
        for i in range(1, len1 + 1):
            tool = agent_tool_flow[i-1]
            dp[i][0] = dp[i-1][0] + self.get_tool_cost(tool)
        
        for j in range(1, len2 + 1):
            tool = ground_truth_tool_flow[j-1]
            dp[0][j] = dp[0][j-1] + self.get_tool_cost(tool)
        
        # Fill dynamic programming matrix
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                tool1 = agent_tool_flow[i-1]
                tool2 = ground_truth_tool_flow[j-1]
                
                if tool1 == tool2:
                    # Exact match, no cost
                    dp[i][j] = dp[i-1][j-1]
                else:
                    # Calculate costs for three operations
                    
                    # Substitution cost = 1 - similarity
                    similarity = self.calculate_tool_similarity(tool1, tool2)
                    substitution_cost = 1.0 - similarity
                    
                    # Deletion cost
                    deletion_cost = self.get_tool_cost(tool1)
                    
                    # Insertion cost
                    insertion_cost = self.get_tool_cost(tool2)
                    
                    # Choose minimum cost operation
                    dp[i][j] = min(
                        dp[i-1][j-1] + substitution_cost,  # substitution
                        dp[i-1][j] + deletion_cost,        # deletion
                        dp[i][j-1] + insertion_cost         # insertion
                    )
        
        enhanced_edit_distance = dp[len1][len2]
        max_possible_cost = max(len1, len2) * 1.5
        similarity_score = 1 - (enhanced_edit_distance / max_possible_cost)
        return similarity_score, enhanced_edit_distance
 
    def compute_structural_score(self, agent_tool_flow, ground_truth_tool_flow):
        similarity, enhanced_edit_distance = self.calculate_tool_flow_similarity(agent_tool_flow, ground_truth_tool_flow)
        # similarity is 0-1 range
        return similarity, enhanced_edit_distance