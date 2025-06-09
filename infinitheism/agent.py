import asyncio
from torch_snippets import *
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

from rich import print as rprint

APP_NAME = "content extractor"
USER_ID = "user_1"
SESSION_ID = "session_001"  # Using a fixed ID for simplicity

# Use the local Ollama model
# model = LiteLlm(model="ollama_chat/qwen3")
model = LiteLlm(model="ollama_chat/deepseek-r1")
# model = 'gemini-2.0-flash'
instruction = """You are a content extraction assistant.
Your task is to remove all headers, footers, and navigation elements from the provided markdown file
and extract the main content. Focus on the core information that is relevant in the markdown file.
Use the following guidelines:
1. **Ignore Headers and Footers**: Do not include any headers, footers, or navigation links.
2. **Extract Main Content**: Focus on the main body of the text, including paragraphs, lists, and important details.
3. **Remove Unnecessary Elements**: Eliminate any elements that do not contribute to the main content, such as sidebars, image urls, advertisements, and other non-essential information.
4. **Output Clean Markdown**: Provide the cleaned markdown content without any additional formatting or comments. /no_think
"""

# Agent 1: Research and find website information using Google Search
root_agent = LlmAgent(
    model=model,
    name="ContentExtractor",
    instruction=instruction,
    # instruction="You are an extremely rude and sarcastic assistant /no_think",
    description="Extracts main content from web pages",
    output_key="cleaned_content"
)


if __name__ == "__main__":
    file = Glob('data/scraped/content/')[0]
    with open(file, 'r') as f:
        md = f.read()

    session_service = InMemorySessionService()
    async def setup_session():
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID,
            state={"user_preferred_temperature_unit": "Fahrenheit"},  # Example state
        )
        print(
            f"Session created: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}'"
        )
        return session


    session = asyncio.run(setup_session())

    # --- Runner ---
    # Key Concept: Runner orchestrates the agent execution loop.
    runner = Runner(
        agent=root_agent,  # The agent we want to run
        app_name=APP_NAME,  # Associates runs with our app
        session_service=session_service,  # Uses our session manager
    )
    print(f"Runner created for agent '{runner.agent.name}'.")


    async def call_agent_async(query: str, runner: Runner, user_id, session_id):
        """Sends a query to the agent and prints the final response."""
        rprint(f"[blue]\n>>> User Query: {query}")
        # Prepare the user's message in ADK format
        content = types.Content(role="user", parts=[types.Part(text=query)])

        final_response_text = "Agent did not produce a final response."  # Default

        # Key Concept: run_async executes the agent logic and yields Events.
        # We iterate through events to find the final answer.
        async for event in runner.run_async(
            user_id=user_id, session_id=session_id, new_message=content
        ):
            # You can uncomment the line below to see *all* events during execution
            # print(f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Content: {event.content}")

            # Key Concept: is_final_response() marks the concluding message for the turn.
            if event.is_final_response():
                if event.content and event.content.parts:
                    # Assuming text response in the first part
                    final_response_text = event.content.parts[0].text
                elif (
                    event.actions and event.actions.escalate
                ):  # Handle potential errors/escalations
                    final_response_text = (
                        f"Agent escalated: {event.error_message or 'No specific message.'}"
                    )
                # Add more checks here if needed (e.g., specific error codes)
                break  # Stop processing events once the final response is found
            else:
                # Intermediate responses can be printed or logged if needed
                rprint(
                    f"[yellow]--- Intermediate {event.content.parts[0].text if event.content else 'No content'}"
                )

        rprint(f"[green]>>>\nAgent Response: {final_response_text}")
        line()

    asyncio.run(call_agent_async(
            instruction + '\nhere is the file' + md,
            runner=runner,
            user_id=USER_ID,
            session_id=SESSION_ID,
        ))