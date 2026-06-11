"""Base agent class for all KISS reasoning agents."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseAgent(ABC):
    """Abstract base class for reasoning agents."""
    
    def __init__(self, name: str, role: str, knowledge: Dict[str, Any]):
        self.name = name
        self.role = role
        self.knowledge = knowledge
        self.reasoning_trace = []
    
    @abstractmethod
    def reason(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Core reasoning method. Must be implemented by subclasses.
        
        Returns:
            {
                "decision": str,
                "confidence": float (0-1),
                "reasoning": str,
                "citations": [str]
            }
        """
        pass
    
    def _log_reasoning(self, step: str, result: Any):
        """Log reasoning step for transparency."""
        self.reasoning_trace.append({
            "step": step,
            "result": result
        })
    
    def _cite_knowledge(self, file_name: str, content: str) -> str:
        """Create a citation to grounded knowledge."""
        return f"[{file_name}] {content[:100]}..."
