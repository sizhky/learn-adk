# Web Research Agent - Uses Google Search to find and analyze website information

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import google_search

# Use the local Ollama model
model = LiteLlm(model="ollama_chat/qwen3")

# Agent 1: Research and find website information using Google Search
research_agent = LlmAgent(
    model=model,
    name="WebResearcher",
    instruction="""You are a Web Research Assistant. 
When given a website URL or domain name, use Google Search to:
1. Search for information about the website/company
2. Find recent news, updates, or mentions
3. Look for related links and resources
4. Summarize key findings about the website

Use the google_search tool to gather this information.
Store your research findings in a clear, organized format.
""",
    description="Researches websites and gathers information using Google Search.",
    tools=[google_search],
    output_key="research_findings"
)

# Agent 2: Analyze and extract insights from the research
analysis_agent = LlmAgent(
    model=model,
    name="WebAnalyzer", 
    instruction="""You are a Web Analysis Assistant.
Based on the research findings stored in state['research_findings'], analyze and provide:

**Research Findings:**
{research_findings}

**Your Analysis Should Include:**
1. **Website Overview**: What is this website about?
2. **Key Information**: Important details found about the site/organization
3. **Recent Activity**: Any recent news, updates, or mentions
4. **Related Resources**: Other relevant websites or links discovered
5. **Summary**: A concise summary of your findings

Provide a well-structured analysis based ONLY on the research data provided above.
""",
    description="Analyzes web research findings and provides structured insights.",
    output_key="analysis_report"
)

# Main sequential agent that orchestrates the research and analysis
root_agent = SequentialAgent(
    name='web_research_pipeline',
    instruction="Research websites using Google Search and provide detailed analysis.",
    sub_agents=[research_agent, analysis_agent],
    description="A pipeline that researches websites and provides comprehensive analysis.",
    output_key="final_report"
)