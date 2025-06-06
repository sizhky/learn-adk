# @title Import necessary libraries
import os
import asyncio
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm  # For multi-model support
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools.tool_context import ToolContext
from google.genai import types  # For creating message Content/Parts

from torch_snippets import line

import warnings

warnings.filterwarnings("ignore")

OLLAMA_API_BASE = "http://localhost:11434"
os.environ["OLLAMA_API_BASE"] = OLLAMA_API_BASE


# @title Define the get_weather Tool
def get_weather(city: str, tool_context: ToolContext) -> dict:
    """Retrieves the current weather report for a specified city.

    Args:
        city (str): The name of the city (e.g., "New York", "London", "Tokyo").
        function works only for New York, London, and Tokyo.
        if the city is not recognized, respond back with only the known cities.

    Returns:
        dict: A dictionary containing the weather information.
              Includes a 'status' key ('success' or 'error').
              If 'success', includes a 'report' key with weather details.
              If 'error', includes an 'error_message' key.
    """
    print(f"--- Tool: get_weather called for city: {city} ---")  # Log tool execution
    city_normalized = city.lower().replace(" ", "")  # Basic normalization

    # Mock weather data
    mock_weather_db = {
        "newyork": {
            "status": "success",
            "report": "The weather in New York is sunny with a temperature of 25°C.",
        },
        "london": {
            "status": "success",
            "report": "It's cloudy in London with a temperature of 15°C.",
        },
        "tokyo": {
            "status": "success",
            "report": "Tokyo is experiencing light rain and a temperature of 18°C.",
        },
    }
    preferred_unit = tool_context.state.get("user_preferred_temperature_unit", "Celsius") # Default to Celsius

    if city_normalized in mock_weather_db:
        celcius = mock_weather_db[city_normalized]
        if preferred_unit == "Fahrenheit":
            # Convert Celsius to Fahrenheit
            temp = celcius["report"].replace("°C", "°F")
            temp = temp.replace("25", str(int(25 * 9 / 5 + 32)))
            temp = temp.replace("15", str(int(15 * 9 / 5 + 32)))
            temp = temp.replace("18", str(int(18 * 9 / 5 + 32)))
        else:
            temp = celcius["report"]
        return temp
    else:
        return {
            "status": "error",
            "error_message": f"Sorry, I don't have weather information for '{city}'.",
        }


if 1:
    model = LiteLlm(
        # model="ollama_chat/qwen3:0.6b",
        model="ollama_chat/qwen3",
    )
else:
    model = "gemini-2.0-flash"

weather_agent = Agent(
    name="weather_agent_v1",
    model=model,
    description="Provides weather information for specific cities.",
    instruction="You are an extremely rude and sarcastic weather assistant /no_think",
    tools=[get_weather],  # Pass the function directly
)

print(f"Agent '{weather_agent.name}' created using model '{model}'.")

# --- Session Management ---
# Key Concept: SessionService stores conversation history & state.
# InMemorySessionService is simple, non-persistent storage for this tutorial.
session_service = InMemorySessionService()

# Define constants for identifying the interaction context
APP_NAME = "weather_tutorial_app"
USER_ID = "user_1"
SESSION_ID = "session_001"  # Using a fixed ID for simplicity


# Create the specific session where the conversation will happen
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
    agent=weather_agent,  # The agent we want to run
    app_name=APP_NAME,  # Associates runs with our app
    session_service=session_service,  # Uses our session manager
)
print(f"Runner created for agent '{runner.agent.name}'.")


async def call_agent_async(query: str, runner: Runner, user_id, session_id):
    """Sends a query to the agent and prints the final response."""
    print(f"\n>>> User Query: {query}")

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
            print(
                f"  [Intermediate] {event.content.parts[0].text if event.content else 'No content'}"
            )

    print(f"<<< Agent Response: {final_response_text}")
    line()


async def run_conversation():
    await call_agent_async(
        "What is the weather like in London?",
        runner=runner,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )

    stored_session = runner.session_service.sessions[APP_NAME][USER_ID][SESSION_ID]
    stored_session.state["user_preferred_temperature_unit"] = "Yolo"

    await call_agent_async(
        "How about Paris?", runner=runner, user_id=USER_ID, session_id=SESSION_ID
    )  # Expecting the tool's error message

    await call_agent_async(
        "Tell me the weather in New York",
        runner=runner,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )


# Execute the conversation using await in an async context (like Colab/Jupyter)
asyncio.run(run_conversation())
