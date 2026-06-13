"""Loads project .md files as grounded knowledge for agents."""

import json
import re
from pathlib import Path
from typing import Dict, Any

class KnowledgeLoader:
    """Loads and parses KISS markdown files into structured knowledge."""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
    
    def load_all(self) -> Dict[str, Any]:
        """Load all knowledge files from project."""
        
        knowledge = {}
        
        # Load each file type
        knowledge["PROJECT_STATE"] = self._load_project_state()
        knowledge["DECISIONS"] = self._load_decisions()
        knowledge["TODO"] = self._load_todo()
        knowledge["PRODUCT_VISION"] = self._load_product_vision()
        knowledge["RISK_POLICY"] = self._load_risk_policy()
        
        return knowledge
    
    def _load_project_state(self) -> Dict[str, Any]:
        """Parse PROJECT_STATE.md"""
        
        path = self.project_path / "PROJECT_STATE.md"
        if not path.exists():
            return {}
        
        content = path.read_text()
        
        return {
            "status": self._extract_field(content, "Status"),
            "goal": self._extract_field(content, "Goal"),
            "blockers": self._extract_list_field(content, "Blockers"),
            "capacity": self._extract_field(content, "Capacity")
        }
    
    def _load_decisions(self) -> Dict[str, Any]:
        """Parse DECISIONS.md"""
        
        path = self.project_path / "DECISIONS.md"
        if not path.exists():
            return {"decisions": []}
        
        content = path.read_text()
        
        # Extract decision entries
        decisions = []
        pattern = r"## (D-\d+).*?\n.*?Title: (.*?)\n.*?Why: (.*?)\n"
        
        for match in re.finditer(pattern, content, re.DOTALL):
            decisions.append({
                "id": match.group(1),
                "title": match.group(2),
                "why": match.group(3)[:200]
            })
        
        return {"decisions": decisions}
    
    def _load_todo(self) -> Dict[str, Any]:
        """Parse TODO.md"""
        
        path = self.project_path / "TODO.md"
        if not path.exists():
            return {"tasks": []}
        
        content = path.read_text()
        
        # Extract tasks
        tasks = []
        lines = content.split("\n")
        for line in lines:
            if line.strip().startswith("- ["):
                tasks.append(line)
        
        return {"tasks": tasks}
    
    def _load_product_vision(self) -> Dict[str, Any]:
        """Parse PRODUCT_VISION.md"""
        
        path = self.project_path / "agile" / "PRODUCT_VISION.md"
        if not path.exists():
            return {}
        
        content = path.read_text()
        
        return {
            "tier_1_keywords": ["MVP", "basic", "simple", "menu", "order", "checkout"],
            "tier_2_keywords": ["analytics", "team", "delivery", "notifications", "photo"],
            "tier_3_keywords": ["multi-location", "inventory", "POS", "enterprise"]
        }
    
    def _load_risk_policy(self) -> Dict[str, Any]:
        """Parse RISK_POLICY.md"""
        
        path = self.project_path / "RISK_POLICY.md"
        if not path.exists():
            return {}
        
        content = path.read_text()
        
        return {
            "policy": "Stop Tier 2/3 features, ask Cody first",
            "authority": "Cody (client decision maker)"
        }
    
    def _extract_field(self, content: str, field: str) -> str:
        """Extract single field value from markdown."""
        
        pattern = rf"^(?:##+ +)?{field}.*?:\s*(.+?)$"
        match = re.search(pattern, content, re.MULTILINE)
        return match.group(1) if match else ""
    
    def _extract_list_field(self, content: str, field: str) -> list:
        """Extract list items under a field."""
        
        lines = content.split("\n")
        result = []
        capture = False
        
        for line in lines:
            if field.lower() in line.lower():
                capture = True
                continue
            if capture:
                if line.startswith("- "):
                    result.append(line[2:])
                elif line.startswith("## "):
                    break
        
        return result
