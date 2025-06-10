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


# Higher-order function to execute a tool with proper cleanup
async def execute_tool(tool, args):
    """Execute a single tool and handle cleanup."""
    try:
        result = await tool.run_async(args=args, tool_context=None)
        return (True, result, None)  # Success, result, no error
    except Exception as e:
        return (False, None, str(e))  # Failed, no result, error message

# Function to try tools sequentially until one succeeds
async def try_tools_sequentially(tools, args, exit_stack):
    """Try each tool in sequence until one succeeds."""
    errors = []
    
    for tool in tools:
        success, result, error = await execute_tool(tool, args)
        if success:
            return result
        errors.append(f"Tool '{tool.name}' failed: {error}")
    
    if errors:
        return f"All tools failed: {'; '.join(errors)}"
    return "No tools available"

# Create a higher-order function that handles connection and resource management
def create_mcp_tool_executor(command, args=None, env=None):
    """Create a function that connects to an MCP server and executes tools."""
    async def mcp_tool_executor(**kwargs):
        # Connect to MCP server
        tools, exit_stack = await MCPToolset.from_server(
            connection_params=StdioServerParameters(
                command=command,
                args=args or [],
                env=env or {},
            )
        )
        
        try:
            # Try all tools until one succeeds
            return await try_tools_sequentially(tools, kwargs, exit_stack)
        finally:
            # Always cleanup
            await exit_stack.aclose()
    
    return mcp_tool_executor

# Create our DuckDuckGo search function
search_duckduckgo = create_mcp_tool_executor(
    command="uvx",
    args=["duckduckgo-mcp-server"],
    env={}
)

# Add documentation for the LLM
search_duckduckgo.__name__ = "search_duckduckgo"
search_duckduckgo.__doc__ = """
Search for information on the web using DuckDuckGo.

Args:
    query: The search terms to look for (e.g., 'Apple Inc revenue 2024')
    count: Optional. Maximum number of results to return (default: 10)

Returns:
    Search results with information from various web sources including financial websites,
    SEC filings, company reports, and news articles.
"""

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
- Use the search_duckduckgo tool to find financial information from reputable sources
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
    tools=[search_duckduckgo],  # Use function tool for search functionality
)


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
        """Sends a query to the agent and prints the final response."""
        rprint(f"[blue]\n>>> User Query: {query}")
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
        
        rprint(f"[green]>>>\nAgent Response: {final_response_text}")
        print("-" * 80)
    
    async def run_research_demo():
        """Demonstrates the research agent with sample company queries."""
        await call_agent_async(
            "please research divami's revenue and industry type. in the form of a json object with keys: company_name, revenue_millions, industry_type, justification.",
            runner=runner,
            user_id=USER_ID,
            session_id=SESSION_ID,
        )
    
    print("Starting the company research agent demonstration...")
    asyncio.run(run_research_demo())
