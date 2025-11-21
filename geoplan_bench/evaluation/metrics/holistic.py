import os
from openai import OpenAI
from geoplan_bench.config.prompts import COMPLETENESS_EVALUATION_PROMPT
from geoplan_bench.data.schemas import EloAnswerSchema


class HolisticEvaluator:
    def __init__(self, model="gpt-4o-mini"):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE")
        )
        self.model = model

    def evaluate_completeness_elo(self, agents_data, question, k_factor=32):
        """use Elo ranking system to evaluate completeness"""
        import random
        import itertools
        
        # step 1: initialize
        agent_names = list(agents_data.keys())
        ratings = {name: 1000 for name in agent_names}
        
        # step 2: create all possible pairs
        battles = []
        for agent_a, agent_b in itertools.combinations(agent_names, 2):
            battles.append((agent_a, agent_b))
        
        # shuffle battles randomly
        random.shuffle(battles)
        
        # step 3: pairwise comparison
        for battle in battles:
            agent_a, agent_b = battle
            tool_flow_a = agents_data[agent_a]
            tool_flow_b = agents_data[agent_b]
            
            # LLM Judge comparison
            prompt = COMPLETENESS_EVALUATION_PROMPT.format(
                question=question,
                agent_a=agent_a,
                tool_flow_a=tool_flow_a,
                agent_b=agent_b,
                tool_flow_b=tool_flow_b
            )
            
            response = self.client.beta.chat.completions.parse(
                model= self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format=EloAnswerSchema,
            )
            
            winner = response.choices[0].message.parsed


            # step 4: update Elo scores
            self._update_elo_ratings(ratings, agent_a, agent_b, winner.answer, k_factor)
        
        return ratings

    def _update_elo_ratings(self, ratings, agent_a, agent_b, winner, k_factor):
        """update Elo scores"""
        # get current scores
        r_a = ratings[agent_a]
        r_b = ratings[agent_b]
        
        # calculate expected scores
        e_a = 1 / (1 + 10**((r_b - r_a) / 400))
        e_b = 1 / (1 + 10**((r_a - r_b) / 400))
        
        # determine actual scores
        if winner == "A":
            s_a, s_b = 1, 0
        elif winner == "B":
            s_a, s_b = 0, 1
        else:  # Tie
            s_a, s_b = 0.5, 0.5
        
        # update scores
        ratings[agent_a] = r_a + k_factor * (s_a - e_a)
        ratings[agent_b] = r_b + k_factor * (s_b - e_b)
    
    def compute_completeness_score(self, agents_data, question):
        """evaluate completeness of the agent's tool flow"""
        ratings = self.evaluate_completeness_elo(agents_data, question)
        return ratings