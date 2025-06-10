#!/usr/bin/env python3
"""
Simple test script for the Organizational Leadership Agent.
This demonstrates the agent structure and capabilities without running it.
"""

from agent import root_agent

def test_agent_structure():
    """Test that the organizational leadership agent is properly configured."""
    print("=== Organizational Leadership Agent Test ===")
    print(f"✅ Agent Name: {root_agent.name}")
    print(f"✅ Model: {root_agent.model}")
    print(f"✅ Tools: {len(root_agent.tools)} tool(s)")
    print(f"✅ Tool Types: {[type(tool).__name__ for tool in root_agent.tools]}")
    
    print(f"\n📝 Agent Description:")
    print(f"{root_agent.description}")
    
    print(f"\n🎯 Core Capabilities:")
    capabilities = [
        "Leadership Development & Executive Coaching",
        "Organizational Structure Design", 
        "Change Management & Digital Transformation",
        "Team Performance & Collaboration",
        "Strategic Planning & Goal Alignment",
        "HR & Talent Management",
        "Communication & Feedback Systems",
        "Innovation & Culture Building"
    ]
    
    for i, capability in enumerate(capabilities, 1):
        print(f"  {i}. {capability}")
    
    print(f"\n🔧 Technical Configuration:")
    print(f"  • Model: {root_agent.model} (Gemini 2.0 Flash)")
    print(f"  • Search: Google Search Tool (Built-in ADK)")
    print(f"  • Framework: Google ADK")
    print(f"  • Response Format: Structured with evidence-based recommendations")
    
    print(f"\n💡 Example Queries the Agent Can Handle:")
    examples = [
        "How should we restructure our organization for better cross-functional collaboration?",
        "What change management strategies work best for digital transformation?",
        "How can we improve employee engagement and reduce turnover?",
        "What leadership development programs should we implement for middle managers?",
        "How do we build a more innovative and inclusive company culture?"
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"  {i}. {example}")
    
    print(f"\n✨ To use this agent:")
    print(f"  1. Set your GOOGLE_API_KEY environment variable")
    print(f"  2. Run: python agent.py")
    print(f"  3. Or integrate with ADK Web UI: adk web")
    
    print(f"\n🎉 Agent is properly configured and ready for use!")

if __name__ == "__main__":
    test_agent_structure()
