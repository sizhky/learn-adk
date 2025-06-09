# ./adk_agent_samples/mcp_agent/agent.py
import os # Required for path operations
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
from rich import print as rprint
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
import asyncio
from google.adk.models.lite_llm import LiteLlm

TARGET_FOLDER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "/Users/yeshwanth/Downloads")
if 1:
    model = LiteLlm(
        model="ollama_chat/gemma3",
    )
else:
    model = "gemini-2.0-flash"  # Use experimental version that supports tools

files_toolset = MCPToolset(
            connection_params=StdioServerParameters(
                command='npx',
                args=[
                    "-y",  # Argument for npx to auto-confirm install
                    "@modelcontextprotocol/server-filesystem",
                    os.path.abspath(TARGET_FOLDER_PATH),
                ],
            ),
            # Optional: Filter which tools from the MCP server are exposed
            # tool_filter=['list_directory', 'read_file']
        )

root_agent = LlmAgent(
    model=model,
    name='filesystem_assistant_agent',
    instruction='Help the user manage their files. You can list files, read files, etc. Use the tools provided to interact with the filesystem.',
    tools=[files_toolset],
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
        )
        print(f"Session created: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}'")
        return session
    
    session = asyncio.run(setup_session())
    
    # Create runner
    runner = Runner(
        agent=root_agent,
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
            "please list my files in downloads folder",
            runner=runner,
            user_id=USER_ID,
            session_id=SESSION_ID,
        )
    
    print("Starting the company research agent demonstration...")
    asyncio.run(run_research_demo())
