"""Planner Agent - Estimates effort and identifies blockers."""

from typing import Dict, Any
from agents.base_agent import BaseAgent

class PlannerAgent(BaseAgent):
    """Plans work scope and effort estimation."""
    
    def __init__(self, knowledge: Dict[str, Any]):
        super().__init__(
            name="Planner",
            role="Estimates effort and identifies blockers",
            knowledge=knowledge
        )
    
    def reason(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate work complexity and blockers.
        References TODO.md and PROJECT_STATE.md.
        """
        
        todos = self.knowledge.get("TODO", {})
        project_state = self.knowledge.get("PROJECT_STATE", {})
        
        blockers = project_state.get("blockers", [])
        current_capacity = project_state.get("capacity", "unknown")
        
        # Estimate complexity
        complexity = "medium"  # Default
        if any(word in request.lower() for word in ["integrate", "connect", "api"]):
            complexity = "heavy"
        elif any(word in request.lower() for word in ["fix", "minor", "update"]):
            complexity = "light"
        
        reasoning = f"Estimated complexity: {complexity}\n"
        
        if blockers:
            reasoning += f"⚠️ Current blockers: {', '.join(blockers)}\n"
            reasoning += "Recommend resolving blockers first."
        else:
            reasoning += "✓ No current blockers."
        
        reasoning += f"\nCurrent capacity: {current_capacity}"
        
        self._log_reasoning("planning", {"complexity": complexity, "blockers": blockers})
        
        return {
            "decision": f"{complexity.capitalize()} effort required",
            "confidence": 0.75,
            "reasoning": reasoning,
            "citations": ["TODO.md", "PROJECT_STATE.md"]
        }
