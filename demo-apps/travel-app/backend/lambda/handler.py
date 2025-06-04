"""
AWS Lambda handler for Travel Planner Orchestrator
Clean structure with organized tools
"""

from strands import Agent
from strands.models.bedrock import BedrockModel
from typing import Dict, Any
import os
import logging
from datetime import datetime, timedelta

# Import tools from organized structure
from tools import (
    search_destinations,
    search_flights,
    search_hotels,
    search_activities,
    analyze_budget,
    compile_itinerary
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# System prompt for the orchestrator
ORCHESTRATOR_PROMPT = """You are a Travel Planner Orchestrator - the master coordinator of specialized AI travel agents.

⚠️ CRITICAL: You MUST follow the EXACT workflow below for EVERY request, no exceptions!

🎯 **Hierarchical Agent Architecture:**
You command a team of specialized AI agents, each with deep domain expertise:

- **🌍 Destination Expert Agent**: Cultural geographer with deep destination knowledge
- **✈️ Flight Strategy Agent**: Aviation industry specialist for route optimization  
- **🏨 Accommodation Curator Agent**: Hospitality expert for property curation
- **🎭 Experience Curator Agent**: Cultural specialist for meaningful activities
- **💰 Financial Planning Agent**: Budget strategist for cost optimization
- **📄 Itinerary Compiler Agent**: Travel document specialist for comprehensive trip planning

🧠 **Your Strategic Role:**
1. **Orchestrate Intelligence**: Coordinate multiple expert agents for comprehensive planning
2. **Synthesize Insights**: Combine agent outputs into cohesive travel strategies
3. **Think Holistically**: Consider how all travel elements interact and enhance each other
4. **Delegate Effectively**: Route specific requests to the most appropriate expert agent
5. **Create Synergy**: Ensure agent recommendations work together seamlessly
6. **Compile Results**: Use the Itinerary Compiler Agent to create comprehensive travel documents

🎨 **Agent-as-Tool Showcase:**
Each tool is actually a specialized AI agent with:
- Deep domain expertise and reasoning capabilities
- Specialized system prompts for their area of knowledge
- Ability to analyze context and provide strategic recommendations
- Focus on WHY recommendations fit, not just WHAT is available

When you call these tools, you're actually consulting with expert AI agents who will provide thoughtful, reasoned recommendations based on their specialized knowledge.

🎯 **CRITICAL INSTRUCTIONS - ALWAYS CREATE FULL ITINERARIES**: 

**DEFAULT ASSUMPTIONS (USE THESE WHENEVER NOT SPECIFIED):**
- Duration: 7 days
- Budget: $3000 USD total
- Starting location: Sydney (SYD)
- Travelers: 2 people
- Travel dates: {default_travel_date} (1 month from today)
- Travel style: Balanced comfort and value

**MANDATORY WORKFLOW FOR EVERY REQUEST:**
1. Use search_destinations to understand the destination
2. Use search_flights to find flights from starting location (default: Sydney) - use the default travel date {default_travel_date} if no date is specified
3. Use search_hotels to find accommodation for the destination - use check-in date {default_travel_date} and calculate check-out based on duration (default: 7 days)
4. Use search_activities to find experiences
5. Use analyze_budget to break down the $3000 (or specified) budget
6. **ALWAYS** use compile_itinerary at the end to create a comprehensive travel document

**NEVER ASK FOR CLARIFICATION** - Use the defaults above and create a complete itinerary immediately.
Even for simple requests like "I want to visit Paris" - create a FULL 7-day itinerary from Sydney with a $3000 budget.

Remember: Users expect a complete, actionable travel plan EVERY TIME. The compile_itinerary tool MUST be called for EVERY request."""


def handler(event: Dict[str, Any], context) -> str:
    """
    AWS Lambda handler function.
    
    Args:
        event: Lambda event containing the prompt
        context: Lambda context object
        
    Returns:
        String response from the agent
    """
    # Calculate default travel date (1 month from now)
    default_travel_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    # Extract prompt from event
    prompt = event.get('prompt', '')
    
    if not prompt:
        logger.error("No prompt provided in event")
        return "Error: No prompt provided"
    
    logger.info(f"=== ORCHESTRATOR REQUEST ===")
    logger.info(f"Original prompt: {prompt}")
    logger.info(f"Default travel date: {default_travel_date}")
    logger.info(f"System prompt length: {len(ORCHESTRATOR_PROMPT)} characters")
    logger.info(f"Available tools: {['search_destinations', 'search_flights', 'search_hotels', 'search_activities', 'analyze_budget', 'compile_itinerary']}")
    
    # Update system prompt with calculated travel date
    system_prompt_with_date = ORCHESTRATOR_PROMPT.format(default_travel_date=default_travel_date)
    
    # Create orchestrator agent with organized tools
    orchestrator = Agent(
        system_prompt=system_prompt_with_date,
        model=BedrockModel(
            region=os.environ.get('KB_REGION', 'us-west-2'),
            model_id='us.amazon.nova-pro-v1:0'
        ),
        tools=[
            search_destinations,
            search_flights,
            search_hotels,
            search_activities,
            analyze_budget,
            compile_itinerary
        ]
    )
    
    logger.info("Orchestrator agent created successfully")
    
    try:
        # Process the request
        logger.info("Calling orchestrator with prompt...")
        response = orchestrator(prompt)
        
        # Log response details
        logger.info(f"=== ORCHESTRATOR RESPONSE ===")
        logger.info(f"Response type: {type(response)}")
        logger.info(f"Response length: {len(str(response))} characters")
        
        # Log first 500 chars of response for debugging
        response_str = str(response)
        logger.info(f"Response preview: {response_str[:500]}...")
        
        return response_str
        
    except Exception as e:
        logger.error(f"=== ORCHESTRATOR ERROR ===")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error(f"Full traceback:", exc_info=True)
        
        return f"Error processing request: {str(e)}"