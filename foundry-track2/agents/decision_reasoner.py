"""Decision Reasoner Agent - Understands past decisions and their rationale."""

from typing import Dict, Any
from agents.base_agent import BaseAgent

class DecisionReasonerAgent(BaseAgent):
    """Reasons about project decisions and their context."""
    
    def __init__(self, knowledge: Dict[str, Any]):
        super().__init__(
            name="Decision Reasoner",
            role="Understands project history and WHY decisions were made",
            knowledge=knowledge
        )
    
    def reason(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if a similar decision already exists.
        References DECISIONS.md history.
        """
        
        decisions = self.knowledge.get("DECISIONS", {})
        past_decisions = decisions.get("decisions", [])
        
        request_lower = request.lower()
        
        # Find similar past decisions
        similar_decisions = []
        for decision in past_decisions:
            title = decision.get("title", "").lower()
            if any(word in request_lower for word in title.split()):
                similar_decisions.append(decision)
        
        reasoning = ""
        
        if similar_decisions:
            reasoning = "Found similar past decisions:\n"
            for dec in similar_decisions[:2]:  # Top 2 matches
                reasoning += f"- {dec.get('title')}: {dec.get('why', 'No rationale')[:80]}...\n"
            reasoning += "\n✓ This decision precedent should guide our answer."
        else:
            reasoning = "No similar past decisions found. This is a new decision."
        
        self._log_reasoning("decision_history", similar_decisions)
        
        return {
            "decision": f"Found {len(similar_decisions)} similar decisions",
            "confidence": 0.8 if similar_decisions else 0.5,
            "reasoning": reasoning,
            "citations": [d.get("id", "D-?") for d in similar_decisions[:2]]
        }
