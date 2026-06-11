"""Orchestrator - Coordinates multi-agent reasoning and synthesizes results."""

from typing import Dict, Any, List
from agents.scope_evaluator import ScopeEvaluatorAgent
from agents.decision_reasoner import DecisionReasonerAgent
from agents.planner_agent import PlannerAgent

class KISSOrchestrator:
    """Orchestrates all reasoning agents."""
    
    def __init__(self, knowledge: Dict[str, Any]):
        self.knowledge = knowledge
        self.agents = [
            ScopeEvaluatorAgent(knowledge),
            DecisionReasonerAgent(knowledge),
            PlannerAgent(knowledge),
        ]
    
    def process_request(self, request: str, context: str) -> Dict[str, Any]:
        """
        Process user request through multi-agent reasoning.
        Each agent reasons independently, then results are synthesized.
        """
        
        context_dict = {"user_context": context}
        
        # Run all agents in parallel (conceptually)
        agent_results = []
        for agent in self.agents:
            result = agent.reason(request, context_dict)
            agent_results.append({
                "agent": agent.name,
                **result
            })
        
        # Synthesize results
        synthesis = self._synthesize(request, agent_results)
        
        return synthesis
    
    def _synthesize(self, request: str, agent_results: List[Dict]) -> Dict[str, Any]:
        """Combine agent reasoning into final recommendation."""
        
        # Extract key insights
        scope_result = next((r for r in agent_results if r["agent"] == "Scope Evaluator"), {})
        decision_result = next((r for r in agent_results if r["agent"] == "Decision Reasoner"), {})
        planner_result = next((r for r in agent_results if r["agent"] == "Planner"), {})
        
        scope_tier = scope_result.get("decision", "Unknown")
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            scope_tier, 
            decision_result.get("decision", ""),
            planner_result.get("decision", "")
        )
        
        # Aggregate reasoning
        full_reasoning = "\n".join([
            f"📊 {r['agent']}: {r['reasoning']}"
            for r in agent_results
        ])
        
        all_citations = []
        for r in agent_results:
            all_citations.extend(r.get("citations", []))
        
        return {
            "request": request,
            "decision": scope_tier,
            "reasoning": full_reasoning,
            "recommendation": recommendation,
            "agent_results": agent_results,
            "citations": all_citations
        }
    
    def _generate_recommendation(self, scope: str, decision_context: str, effort: str) -> str:
        """Generate actionable recommendation based on all agent reasoning."""
        
        if "Tier 1" in scope:
            return f"✅ This is in scope. Proceed with {effort.lower()}. {decision_context}"
        elif "Tier 2" in scope:
            return f"⚠️ This is Tier 2 (future work). Park it in DECISIONS.md instead of building now. {decision_context}"
        else:
            return f"🎯 This is visionary. Document in long-term planning. {decision_context}"
