#!/usr/bin/env python3
"""
Simple test of the agent system.
"""

import asyncio
from agent import research_agent, FINANCIAL_SOURCES
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from rich import print as rprint

async def call_research_agent(query: str, runner, user_id: str, session_id: str):
    """Simple agent interaction function for testing."""
    content = types.Content(role="user", parts=[types.Part(text=query)])
    
    final_response_text = "Agent did not produce a final response."
    
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate:
                final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
            break
        else:
            # Show intermediate responses - safely handle function calls
            if event.content and event.content.parts:
                try:
                    text_part = event.content.parts[0].text
                    if text_part:
                        rprint(f"[yellow]--- Intermediate: {text_part[:200]}...")
                except (AttributeError, IndexError):
                    rprint(f"[yellow]--- Intermediate: {str(event.content.parts[0])[:200]}...")
    
    return final_response_text

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
    result = await call_research_agent(query, runner, USER_ID, SESSION_ID)
    
    print(f"\nQuery: {query}")
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test_simple())
