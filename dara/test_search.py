#!/usr/bin/env python3
"""
Test script to verify the research agent with MCPToolset search integration.
"""

import asyncio
from agent import call_research_agent, research_agent, FINANCIAL_SOURCES
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

async def test_search():
    """Test the research agent with MCPToolset search functionality."""
    print("Testing Research Agent with MCPToolset search integration...")
    
    # Setup session and runner
    session_service = InMemorySessionService()
    APP_NAME = "test_research_app"
    USER_ID = "test_user"
    SESSION_ID = "test_session"
    
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        state={"research_sources": FINANCIAL_SOURCES}
    )
    
    runner = Runner(
        agent=research_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )
    
    # Test 1: Search for Apple financial information
    print("\n1. Testing research for Apple:")
    query1 = "Research Apple's revenue and industry type. Provide the information in JSON format with keys: company_name, revenue_millions, industry_type, justification."
    result1 = await call_research_agent(query1, runner, USER_ID, SESSION_ID)
    print(f"Query: {query1}")
    print(f"Result: {result1}")
    
    # Test 2: Search for Microsoft
    print("\n" + "="*80)
    print("\n2. Testing research for Microsoft:")
    query2 = "Find Microsoft's annual revenue in millions and what industry they operate in."
    result2 = await call_research_agent(query2, runner, USER_ID, SESSION_ID)
    print(f"Query: {query2}")
    print(f"Result: {result2}")

if __name__ == "__main__":
    asyncio.run(test_search())
