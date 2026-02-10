import os
import asyncio
import httpx
import requests
import chainlit as cl
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv

# OpenAI Agents SDK Imports
from agents import (
    Agent, Runner, RunConfig, OpenAIChatCompletionsModel,
    function_tool, handoff, set_default_openai_key,
    enable_verbose_stdout_logging, set_tracing_disabled
)

# 1. SETUP & CONFIGURATION
load_dotenv(find_dotenv())
set_tracing_disabled(True)
enable_verbose_stdout_logging()

# Set OpenAI Key for the SDK
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    set_default_openai_key(openai_api_key)

# Configure the Nano Model
target_model = "gpt-4o-mini"
run_config = RunConfig(model=target_model)


# 3. TOOLS
import requests
from typing import Optional

# Requires `requests` library: pip install requests
# Also assumes this runs in an async environment, otherwise remove `async`/`await`

@function_tool()
async def search_tool(query: str) -> str:
    # Use the full endpoint URL for the Realtime API
    endpoint = 'https://realtime.oxylabs.io/v1/queries'
    
    # Payload for the POST request
    payload = {
        'source': 'google_search',
        'query': query,
        'geo_location': 'United Arab Emirates',
        'parse': True,
        'limit': 10
    }
    
    # Credentials (Replace with secure environment variables in production)
    # Based on {Link: Oxylabs documentation https://developers.oxylabs.io/help-center/getting-started/start-using-web-scraper-api}
    username = 'Hassan_Yb7vy'
    password = 'Private=12364' # Password shown in prompt
    
    # Send request to Oxylabs
    response = requests.post(
        endpoint,
        auth=(username, password),
        json=payload,
        timeout=60
    )
    
    data = response.json()
    
    # Path: results[0] -> content -> results -> organic
    if 'results' in data and len(data['results']) > 0:
        content = data['results'][0].get('content', {})
        organic = content.get('results', {}).get('organic', [])
        
        # Format the top 3 results
        return "\n\n".join([
            f"Title: {r.get('title')}\nLink: {r.get('url')}\nSnippet: {r.get('desc')}"
            for r in organic[:3]
        ])
        
    return "No organic results found."


@function_tool()
async def keyword_data_tool(keyword: str) -> str:
    # Cheaper and more data-rich for single lookups
    endpoint = "https://api.dataforseo.com"
    
    payload = [{
        "location_code": 2710, # UAE
        "language_code": "en",
        "keyword": keyword # Note: Labs uses 'keyword' (string), not 'keywords' (list)
    }]
    
    # Use your existing credentials
    response = requests.post(endpoint, auth=('jotibif558@desiys.com', '36c699a9406e38e5'), json=payload)
    data = response.json()
    
    try:
        item = data['tasks'][0]['result'][0]['items'][0]
        vol = item.get('keyword_info', {}).get('search_volume', 'N/A')
        intent = item.get('search_intent_info', {}).get('label', 'N/A')
        
        return f"Keyword: {keyword} | Vol: {vol} | Intent: {intent}"
    except (KeyError, IndexError):
        return f"No data found for '{keyword}'."



class FinalBlogPost(BaseModel):
    title: str
    meta_description: str
    content: str
    key_takeaways: list[str]



seo_wordsmith = Agent(
    name="SEO Wordsmith",
    instructions="""
    You are a Master Content Writer who writes like a helpful friend, not a manual.
    
    CHOOSE ANY ONE WRITING STYLE ACCORDING to RESEARCH DATA:
    - ANGLE: Don't just list features. Start with a relatable struggle .
    - COMPARISONS: Use the competition data found by the Scout to show why this product wins (or where it loses).
    - HONESTY: Include a 'Pros & Cons' section based on the 'Pain Points' identified. Humans trust reviews that mention flaws.


    STRUCTURE:
    1. Catchy H1 ACCORDING to Product Persona And Research of Scout.
    2. PAS Framework Intro (Problem, Agitation, Solution). USE IT according to product dont paste these headings
     ********* DONT JUST COPY HEADINGS . DO REASONING AND USE Headings according to "PRODUCT". *********
    3. 'The Competition' H2: How it stacks up against the rivals found in research.
     ********* DONT JUST COPY HEADINGS . DO REASONING AND USE Headings according to "PRODUCT". *********
    4. 'Real Talk' H2: Address the common problems and how to fix them.
     ********* DONT JUST COPY HEADINGS . DO REASONING AND USE Headings according to "PRODUCT". *********
    5. Final Verdict: A clear "Buy this if..." or "Skip this if..." conclusion.
     ********* DONT JUST COPY HEADINGS . DO REASONING AND USE Headings according to "PRODUCT". *********

    ********* DONT JUST COPY HEADINGS . DO REASONING AND USE Headings according to "PRODUCT" AND TOPIC. *********

    CRITICAL: 
    - Do not just 'confirm' the handoff. 
    - Do not say 'I am working on it'. 
    - Your response MUST be the full, finished blog post content. 
    - Use the Problem-Agitation-Solution (PAS) framework.
    
    """,
    model=target_model,
    # output_type=FinalBlogPost
)


topical_architect = Agent(
    name="Topical Architect",
    instructions="""
    You are the Decision Maker. Your goal is to move the research into a blog structure IMMEDIATELY.

    1. DATA REVIEW: Look at the search results provided by the Scout (Common problems, UAE brands, and reviews).
    2. IGNORE MISSING DATA: If keyword volume is 'unavailable', do NOT ask for more searches. Use the existing search snippets.
    3. SELECT ANGLE: Choose one:
       - 'The Ultimate Maintenance Guide' (focus on the problems/fixes found)
       - 'Samsung vs LG/Panasonic: The Battle' (focus on the brands found)
    4. HANDOFF: Provide your chosen Title and the Reasoning to the Content Strategist.
    
    ***Do NOT ANSWER to user***
    CRITICAL: You must handoff to `seo_wordsmith`NOW. Do not give any excuses.
    """,
    model=target_model,
    handoffs=[handoff(seo_wordsmith)]
)

discovery_agent = Agent(
    name="Trend Scout",
    instructions="""
    You are a Consumer Behavior Specialist. Your goal is to find out what REAL humans think about the product. 
    Do not just look for specs; look for the 'vibe' and the 'friction.'

    WORKFLOW:
    1. BROAD SEARCH: Start with the product name to identify the main category.
    2. HUMAN QUERIES: Call the `search_tool` with 'human-style' queries like:
       - "[Product Name] real world review reddit"
       - "[Product Name] vs" (to find competitors)
       - "Common problems with [Product Name]"
       - "Is [Product Name] worth it for [Target Audience]?"
    3. KEYWORD DATA: Call `keyword_data_tool` for broad terms like brands (e.g., if it's a Mastela Swing, search 'electric baby swing' or 'baby bassinet').
    4. ANALYSIS: Identify:
       - PRAISES: What do people love? (e.g., 'saved my sleep').
       - PAIN POINTS: What sucks? (e.g., 'motor is loud', 'short cord').
       - COMPETITION: Who is the main rival?
    5. HANDOFF: Summarize these 'Human Insights' and hand off to the "Topical Architect" or "SEO Wordsmith".
    
    CRITICAL: 
    - Do NOT ANSWER to user.
    - Your FINAL ACTION in every run MUST be calling the handoff tool to 'topical_architect'.
    """,
    tools=[search_tool, keyword_data_tool],
    model=target_model,
    handoffs=[handoff(agent=topical_architect)], # Ensure this points to the Architect
)



@cl.on_chat_start
async def handle_chat_start():
    cl.user_session.set("history", [])
    await cl.Message(content="Hello! I'm the gpt-4.1-nano SEO Agent. How can I help?").send()

@cl.on_message
async def handle_message(message: cl.Message):
    history = cl.user_session.get("history") or []
    history.append({"role": "user", "content": message.content})

    result = await Runner.run(
        discovery_agent,
        input=history,
        run_config=run_config
    )

    history.append({"role": "assistant", "content": result.final_output})
    cl.user_session.set("history", history)

    await cl.Message(content=result.final_output).send()
