#!/usr/bin/env python3
"""
Simple test of the agent system.
"""

import asyncio
from agent import agent_with_search_capability, research_agent, FINANCIAL_SOURCES
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

async def test_simple():
    """Test a simple query."""
    print("Testing simple agent query...")
    
    # Create session components
    session_service = InMemorySessionService()
    APP_NAME = "company_research_app"
    USER_ID = "researcher_1"
    SESSION_ID = "research_001"
    
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        state={"research_sources": FINANCIAL_SOURCES}
    )
    print(f"Session created: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}'")
    
    runner = Runner(
        agent=research_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )
    print(f"Runner created for agent '{runner.agent.name}'.")
    
    query = "please research Apple revenue"
    result = await agent_with_search_capability(query, runner, USER_ID, SESSION_ID)
    
    print(f"\nQuery: {query}")
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test_simple())
