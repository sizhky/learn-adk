# Company Research Agent
# Researches companies to find: company name, revenue in millions, and industry type
# Uses DuckDuckGo Search via MCP client to gather information from financial sources

import os
import asyncio
from typing import Any, Dict

# Google ADK imports
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from rich import print as rprint

# MCP client imports
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

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


# Custom DuckDuckGo Search Tool using MCP Client
class DuckDuckGoSearchTool:
    """Custom search tool that uses DuckDuckGo MCP server via client connection."""
    
    def __init__(self):
        self.server_params = StdioServerParameters(
            command="/Users/yeshwanth/.local/bin/uv",
            args=["run", "mcp-duckduckgo"],
            env=None
        )
    
    async def search(self, query: str, count: int = 10) -> Dict[str, Any]:
        """
        Perform DuckDuckGo search using MCP client.
        
        Args:
            query: Search query string
            count: Number of results to return (1-20)
            
        Returns:
            Dictionary containing search results
        """
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the connection
                    await session.initialize()
                    
                    # Call the DuckDuckGo search tool
                    result = await session.call_tool("duckduckgo_web_search", {
                        "query": query,
                        "count": count
                    })
                    
                    return {
                        "success": True,
                        "query": query,
                        "results": result.content[0].text if result.content else "No results found"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": "Search failed"
            }

# Create global search tool instance
search_tool = DuckDuckGoSearchTool()

# Custom search function for the agent
async def search_financial_data(company_name: str, search_query: str = None, count: int = 10) -> str:
    """
    Search for financial data using DuckDuckGo MCP client.
    Formats results specifically for financial research.
    """
    # Use provided search query or create enhanced query
    if search_query is None:
        enhanced_query = f"{company_name} revenue financial report annual SEC filing"
    else:
        enhanced_query = search_query
    
    result = await search_tool.search(enhanced_query, count)
    
    if result["success"]:
        return f"Search Results for '{company_name}':\n{result['results']}"
    else:
        return f"Search failed for '{company_name}': {result['error']}"


# Configure the model
if 1:
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
- Use the available search function to find financial information from reputable sources
- Prioritize SEC filings, Yahoo Finance, MarketWatch, and company investor relations pages
- Focus on recent annual reports (10-K filings for US companies)
- Cross-reference data from multiple sources for accuracy
- Present findings in a clear, structured format

When researching, focus on:
- Recent annual reports (10-K filings for US companies)
- Official company financial statements
- Established financial news sources
- Investor relations materials

Always cite your sources and indicate confidence level in the data found.

You have access to a search function that can help you find financial information. Use it to search for company data.""",
    tools=[],  # We'll handle search functionality through custom implementation
)

# Add search capability by creating a wrapper
async def agent_with_search_capability(query: str, runner, user_id: str, session_id: str):
    """Enhanced agent interaction with search capability."""
    
    # Pre-process to identify if this is a research query
    if any(keyword in query.lower() for keyword in ['revenue', 'financial', 'company', 'industry', 'research']):
        # Better company name extraction
        import re
        
        # Try to extract company name more intelligently
        # Look for patterns like "research [company]'s revenue" or "find [company] financial"
        patterns = [
            r"research\s+(\w+(?:\s+\w+)?)'?s?\s+revenue",  # "research divami's revenue"
            r"research\s+(\w+(?:\s+\w+)?)\s+revenue",      # "research divami revenue"
            r"find\s+(\w+(?:\s+\w+)?)\s+(?:revenue|financial)",  # "find apple revenue"
            r"(\w+(?:\s+\w+)?)\s+revenue",                 # "apple revenue"
            r"(\w+(?:\s+\w+)?)\s+financial",               # "apple financial"
        ]
        
        company_name = ""
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                company_name = match.group(1).strip()
                break
        
        # If no pattern matches, try to extract from context
        if not company_name:
            words = query.split()
            # Skip common words and look for potential company names
            skip_words = {'please', 'research', 'find', 'revenue', 'financial', 'company', 'industry', 'type', 'in', 'the', 'form', 'of', 'a', 'json', 'object', 'with', 'keys', 'and'}
            potential_words = [word.strip("'s.:,") for word in words if word.lower() not in skip_words and len(word) > 2]
            if potential_words:
                company_name = potential_words[0]  # Take the first meaningful word
        
        if company_name:
            # Perform search with cleaner query
            search_query = f"{company_name} company revenue financial information annual report"
            search_results = await search_financial_data(company_name, search_query)
            enhanced_query = f"{query}\n\nSearch Results for {company_name}:\n{search_results}"
        else:
            enhanced_query = query
    else:
        enhanced_query = query
    
    # Send enhanced query to agent
    content = types.Content(role="user", parts=[types.Part(text=enhanced_query)])
    
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
        """Sends a query to the agent using the enhanced search capability."""
        rprint(f"[blue]\n>>> User Query: {query}")
        
        # Use the enhanced agent function with search capability
        final_response_text = await agent_with_search_capability(query, runner, user_id, session_id)
        
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
