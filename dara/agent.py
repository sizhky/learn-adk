# Company Research Agent
# Researches companies to find: company name, revenue in millions, and industry type
# Uses DuckDuckGo Search via MCP client to gather information from financial sources

import os
import asyncio

# Google ADK imports
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from rich import print as rprint

# MCP Toolset imports
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

import warnings
warnings.filterwarnings("ignore")

# Configuration
OLLAMA_API_BASE = "http://localhost:11434"
os.environ["OLLAMA_API_BASE"] = OLLAMA_API_BASE

# Financial data sources for research
FINANCIAL_SOURCES = [
    "sec.gov/edgar",
    "finance.yahoo.com",
    "marketwatch.com", 
    "google.com/finance",
    "companies-house.gov.uk",
    "sedar.com",
    "factset.com",
    "morningstar.com",
    "finchat.io",
    "ycharts.com",
    "stockrover.com",
    "investingpro.com"
]


# Create MCPToolset for DuckDuckGo search
duckduckgo_toolset = MCPToolset(
    connection_params=StdioServerParameters(
        command="uvx",
        args=["duckduckgo-mcp-server"],
        env=None
    ),
)

# Configure the model
if 0:
    model = LiteLlm(
        model="ollama_chat/granite3.3",
    )
else:
    model = "gemini-2.0-flash"  # Use experimental version that supports tools

# Create the research agent
research_agent = Agent(
    name="company_research_agent_v1",
    model=model,
    description="Researches companies to find company name, revenue in millions, and industry type using financial data sources via DuckDuckGo search.",
    instruction="""You are a professional financial research analyst. Your task is to research companies and extract three key pieces of information:

1. Company Name (verified and complete)
2. Annual Revenue in Millions USD
3. Type of Industry/Business Sector

Research Process:
- Use the duckduckgo_web_search tool to find financial information from reputable sources
- Prioritize SEC filings, Yahoo Finance, MarketWatch, and company investor relations pages
- Focus on recent annual reports (10-K filings for US companies)
- Cross-reference data from multiple sources for accuracy
- Present findings in a clear, structured format

When researching, focus on:
- Recent annual reports (10-K filings for US companies)
- Official company financial statements
- Established financial news sources
- Investor relations materials

Search Strategy:
- Use specific search queries like "[company name] revenue financial report annual SEC filing"
- Search for "[company name] 10-K annual report" for US public companies
- Try "[company name] financial statements revenue" for general searches
- Cross-validate information from multiple sources

Always cite your sources and indicate confidence level in the data found.

You have access to a DuckDuckGo search tool. Use it effectively to search for company financial data.""",
    tools=[duckduckgo_toolset],  # Use MCPToolset for search functionality
)

# Simple agent interaction function
async def call_research_agent(query: str, runner, user_id: str, session_id: str):
    """Direct agent interaction using MCPToolset for search."""
    
    # Send query directly to agent - it now has access to search tools
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
            # Show intermediate responses
            if event.content and event.content.parts:
                rprint(f"[yellow]--- Intermediate: {event.content.parts[0].text[:200]}...")
    
    return final_response_text


def create_research_session():
    """Creates and returns a configured research session."""
    session_service = InMemorySessionService()
    
    # Application constants
    APP_NAME = "company_research_app"
    USER_ID = "researcher_1"
    SESSION_ID = "research_001"
    
    async def setup_session():
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID,
            state={"research_sources": FINANCIAL_SOURCES}
        )
        print(f"Session created: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}'")
        return session, session_service, APP_NAME, USER_ID, SESSION_ID
    
    return asyncio.run(setup_session())


def create_research_runner():
    """Creates and returns a configured research runner."""
    session, session_service, app_name, user_id, session_id = create_research_session()
    
    runner = Runner(
        agent=research_agent,
        app_name=app_name,
        session_service=session_service,
    )
    print(f"Runner created for agent '{runner.agent.name}'.")
    return runner, user_id, session_id


# Session Management
if __name__ == "__main__":
    session_service = InMemorySessionService()
    
    # Application constants
    APP_NAME = "company_research_app"
    USER_ID = "researcher_1"
    SESSION_ID = "research_001"
    
    async def setup_session():
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID,
            state={"research_sources": FINANCIAL_SOURCES}
        )
        print(f"Session created: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}'")
        return session
    
    session = asyncio.run(setup_session())
    
    # Create runner
    runner = Runner(
        agent=research_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )
    print(f"Runner created for agent '{runner.agent.name}'.")
    
    async def call_agent_async(query: str, runner: Runner, user_id: str, session_id: str):
        """Sends a query to the agent using MCPToolset search capability."""
        rprint(f"[blue]\n>>> User Query: {query}")
        
        # Use the research agent with MCPToolset
        final_response_text = await call_research_agent(query, runner, user_id, session_id)
        
        rprint(f"[green]>>>\nAgent Response: {final_response_text}")
        print("-" * 80)
    
    async def run_research_demo():
        """Demonstrates the research agent with sample company queries."""
        # Test with a well-known company first
        # await call_agent_async(
        #     "please research Apple's revenue and industry type. in the form of a json object with keys: company_name, revenue_millions, industry_type, justification.",
        #     runner=runner,
        #     user_id=USER_ID,
        #     session_id=SESSION_ID,
        # )
        
        # print("\n" + "="*80 + "\n")
        
        # Test with original query
        await call_agent_async(
            "please research divami's revenue and industry type. in the form of a json object with keys: company_name, revenue_millions, industry_type, justification.",
            runner=runner,
            user_id=USER_ID,
            session_id=SESSION_ID,
        )
    
    print("Starting the company research agent demonstration...")
    asyncio.run(run_research_demo())
