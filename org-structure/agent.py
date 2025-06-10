# Organizational Leadership Agent
# An AI agent that provides expert guidance on organizational leadership, management strategies,
# and business best practices using Google Search to find the latest research and insights

import asyncio

# Google ADK imports
from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from rich import print as rprint

import warnings
warnings.filterwarnings("ignore")

# Create the organizational leadership agent
root_agent = Agent(
    name="org_leadership_agent",
    model="gemini-2.0-flash",
    description="Expert organizational leadership advisor that provides evidence-based guidance on management strategies, team development, organizational structure, and leadership best practices.",
    instruction="""You are a world-class organizational leadership consultant and management expert. Your role is to provide comprehensive, evidence-based guidance on all aspects of organizational leadership and management.

CORE EXPERTISE AREAS:
1. **Leadership Development**: Executive coaching, leadership styles, emotional intelligence, decision-making
2. **Organizational Structure**: Team design, hierarchy optimization, role clarity, reporting structures
3. **Change Management**: Transformation strategies, cultural change, digital transformation, merger integration
4. **Team Performance**: Team dynamics, collaboration, conflict resolution, performance management
5. **Strategic Management**: Vision setting, strategic planning, goal alignment, KPI development
6. **Human Resources**: Talent acquisition, retention strategies, employee engagement, succession planning
7. **Communication**: Internal communication strategies, feedback systems, meeting effectiveness
8. **Innovation & Culture**: Building innovative cultures, psychological safety, diversity & inclusion

METHODOLOGY:
- Always search for the latest research, case studies, and expert insights using Google Search
- Provide evidence-based recommendations with specific examples and citations
- Consider industry-specific contexts and organizational size/maturity
- Balance theoretical frameworks with practical, actionable advice
- Reference thought leaders, academic research, and successful companies

SEARCH STRATEGY:
- Use specific, targeted searches for current best practices
- Look for recent publications from Harvard Business Review, McKinsey, BCG, Deloitte
- Search for case studies from successful companies (Google, Microsoft, Amazon, etc.)
- Find academic research from business schools and leadership institutes
- Look for industry-specific leadership challenges and solutions

RESPONSE FORMAT:
1. **Situation Analysis**: Understand the specific context and challenges
2. **Research Insights**: Share relevant findings from your searches
3. **Strategic Recommendations**: Provide 3-5 specific, actionable recommendations
4. **Implementation Plan**: Outline practical next steps with timelines
5. **Success Metrics**: Suggest how to measure progress and success
6. **Resources**: Provide links to additional reading and tools

Always cite your sources and provide specific examples from real organizations when possible. Be practical, actionable, and tailored to the user's specific organizational context.""",
    tools=[google_search]
)

# Simple agent interaction function
async def call_leadership_agent(query: str, runner, user_id: str, session_id: str):
    """Direct agent interaction for organizational leadership queries."""
    
    # Send query directly to agent
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

def create_leadership_session():
    """Creates and returns a configured leadership session."""
    session_service = InMemorySessionService()
    
    # Application constants
    APP_NAME = "org_leadership_app"
    USER_ID = "leader_1"
    SESSION_ID = "leadership_001"
    
    async def setup_session():
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID,
            state={"context": "organizational_leadership"}
        )
        print(f"Session created: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}'")
        return session, session_service, APP_NAME, USER_ID, SESSION_ID
    
    return asyncio.run(setup_session())

def create_leadership_runner():
    """Creates and returns a configured leadership runner."""
    session, session_service, app_name, user_id, session_id = create_leadership_session()
    
    runner = Runner(
        agent=root_agent,
        app_name=app_name,
        session_service=session_service,
    )
    print(f"Runner created for agent '{runner.agent.name}'.")
    return runner, user_id, session_id

# Session Management for standalone execution
if __name__ == "__main__":
    session_service = InMemorySessionService()
    
    # Application constants
    APP_NAME = "org_leadership_app"
    USER_ID = "leader_1"
    SESSION_ID = "leadership_001"
    
    async def setup_session():
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SESSION_ID,
            state={"context": "organizational_leadership"}
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
        rprint(f"[blue]\n>>> Leadership Query: {query}")
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
        
        rprint(f"[green]>>>\nLeadership Guidance: {final_response_text}")
        print("-" * 80)
    
    async def run_leadership_demo():
        """Demonstrates the organizational leadership agent with sample queries."""
        
        # Demo query 1: Team restructuring
        await call_agent_async(
            "Our tech startup has grown from 50 to 200 employees in the past year. We're struggling with communication silos between engineering, product, and marketing teams. What organizational structure and leadership strategies would you recommend to improve cross-functional collaboration?",
            runner=runner,
            user_id=USER_ID,
            session_id=SESSION_ID,
        )
        
        print("\n" + "="*80 + "\n")
        
        # Demo query 2: Change management
        await call_agent_async(
            "We're a traditional manufacturing company transitioning to include digital services. Our workforce is resistant to change and many managers lack digital leadership skills. How should we approach this transformation from an organizational leadership perspective?",
            runner=runner,
            user_id=USER_ID,
            session_id=SESSION_ID,
        )
    
    print("Starting the organizational leadership agent demonstration...")
    asyncio.run(run_leadership_demo())