#!/usr/bin/env python3
"""
KISS Multi-Agent Orchestration for Track 2: Reasoning Agents
Demonstrates multi-agent reasoning about project scope, decisions, and planning.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from agents.orchestrator import KISSOrchestrator
from utils.knowledge_loader import KnowledgeLoader

load_dotenv()

def main():
    """Main entry point for KISS reasoning agents."""
    
    # Initialize knowledge base from demo project
    demo_project_path = Path(os.getenv("DEMO_PROJECT_PATH", "../demo-project/pizza-shop"))
    
    print("🧠 KISS Multi-Agent Reasoning System")
    print("=" * 50)
    print(f"Loading project knowledge from: {demo_project_path}")
    
    # Load knowledge
    loader = KnowledgeLoader(demo_project_path)
    knowledge = loader.load_all()
    
    print(f"✓ Loaded {len(knowledge)} knowledge files")
    
    # Initialize orchestrator
    orchestrator = KISSOrchestrator(knowledge)
    
    # Example scenarios
    scenarios = [
        {
            "request": "Can we add blockchain payment integration?",
            "context": "User asking about a new feature during sprint"
        },
        {
            "request": "What's our current sprint status?",
            "context": "Manager requesting project health check"
        },
        {
            "request": "Why did we decide to use TypeScript?",
            "context": "Team member asking about past decisions"
        }
    ]
    
    print("\n🔄 Running Multi-Agent Reasoning Scenarios")
    print("=" * 50)
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n[Scenario {i}] {scenario['request']}")
        print(f"Context: {scenario['context']}")
        print("-" * 50)
        
        # Get reasoning from agents
        result = orchestrator.process_request(
            request=scenario["request"],
            context=scenario["context"]
        )
        
        print(f"Decision: {result['decision']}")
        print(f"Reasoning: {result['reasoning']}")
        if result.get('recommendation'):
            print(f"Recommendation: {result['recommendation']}")
        print()

if __name__ == "__main__":
    main()
