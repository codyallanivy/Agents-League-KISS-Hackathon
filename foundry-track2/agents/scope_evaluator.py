"""Scope Evaluator Agent - Determines if request is in scope (Tier 1/2/3)."""

from typing import Dict, Any
from agents.base_agent import BaseAgent

class ScopeEvaluatorAgent(BaseAgent):
    """Evaluates requests against project scope tiers."""
    
    def __init__(self, knowledge: Dict[str, Any]):
        super().__init__(
            name="Scope Evaluator",
            role="Determines if features are Tier 1, 2, or 3",
            knowledge=knowledge
        )
    
    def reason(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate if request matches project scope.
        References PRODUCT_VISION.md tiers.
        """
        
        product_vision = self.knowledge.get("PRODUCT_VISION", {})
        tier_1_keywords = product_vision.get("tier_1_keywords", [])
        tier_2_keywords = product_vision.get("tier_2_keywords", [])
        
        request_lower = request.lower()
        
        # Determine tier
        tier = "unknown"
        confidence = 0.0
        
        for keyword in tier_1_keywords:
            if keyword.lower() in request_lower:
                tier = "1"
                confidence = 0.9
                break
        
        if tier == "unknown":
            for keyword in tier_2_keywords:
                if keyword.lower() in request_lower:
                    tier = "2"
                    confidence = 0.85
                    break
        
        if tier == "unknown":
            tier = "3"  # Vision/future
            confidence = 0.7
        
        decision = f"Tier {tier}"
        reasoning = f"Request matches Tier {tier} scope criteria."
        
        if tier == "1":
            reasoning += " ✅ This is in scope for MVP."
        elif tier == "2":
            reasoning += " ⚠️ This is Tier 2 (future). Can be parked for after MVP."
        else:
            reasoning += " 🎯 This is visionary. Document for long-term planning."
        
        self._log_reasoning("scope_evaluation", decision)
        
        return {
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning,
            "citations": [f"PRODUCT_VISION.md - Tier {tier} definition"]
        }
