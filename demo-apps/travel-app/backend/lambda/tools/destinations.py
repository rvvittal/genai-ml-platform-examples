"""
Destination Expert Agent - AI travel destination specialist with deep knowledge
"""

import os
import boto3
import logging
import time
import traceback
from strands import tool, Agent
from strands.models.bedrock import BedrockModel
from utils.status_tracker import update_agent_status

logger = logging.getLogger(__name__)


def _search_knowledge_base(query: str) -> str:
    """Helper function to search AWS Knowledge Base for destination data."""
    start_time = time.time()
    logger.info(f"[KB_SEARCH] Starting knowledge base search")
    logger.info(f"[KB_SEARCH] Query: {query}")
    logger.info(f"[KB_SEARCH] Query length: {len(query)} characters")
    
    try:
        # Track client creation time
        client_start = time.time()
        kb_client = boto3.client(
            'bedrock-agent-runtime',
            region_name=os.environ.get('KB_REGION', 'us-west-2')
        )
        client_duration = time.time() - client_start
        logger.info(f"[KB_SEARCH] KB client created in {client_duration:.3f}s")
        
        # Track retrieval time
        retrieve_start = time.time()
        kb_id = os.environ.get('KB_ID', 'TMLXOGDYXH')
        logger.info(f"[KB_SEARCH] Searching KB ID: {kb_id}")
        
        response = kb_client.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={'text': query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 5
                }
            }
        )
        retrieve_duration = time.time() - retrieve_start
        logger.info(f"[KB_SEARCH] Retrieval completed in {retrieve_duration:.3f}s")
        
        # Process results
        results = []
        result_count = len(response.get('retrievalResults', []))
        logger.info(f"[KB_SEARCH] Found {result_count} results")
        
        for idx, result in enumerate(response['retrievalResults']):
            content = result['content']['text']
            score = result.get('score', 0)
            results.append(f"[Score: {score:.2f}] {content}")
            logger.debug(f"[KB_SEARCH] Result {idx+1}: Score={score:.2f}, Length={len(content)} chars")
        
        final_result = "\n\n".join(results) if results else "No destination data found."
        total_duration = time.time() - start_time
        logger.info(f"[KB_SEARCH] Total search completed in {total_duration:.3f}s")
        logger.info(f"[KB_SEARCH] Response size: {len(final_result)} characters")
        
        return final_result
        
    except Exception as e:
        error_duration = time.time() - start_time
        logger.error(f"[KB_SEARCH] Error after {error_duration:.3f}s: {e}")
        logger.error(f"[KB_SEARCH] Stack trace:\n{traceback.format_exc()}")
        return f"Knowledge base search failed: {e}"


@tool
def kb_search(query: str) -> str:
    """Search knowledge base for destination information."""
    logger.info(f"[KB_SEARCH_TOOL] Called with query: {query}")
    result = _search_knowledge_base(query)
    logger.info(f"[KB_SEARCH_TOOL] Returning result of {len(result)} characters")
    return result


@tool
def search_destinations(query: str, travel_style: str = None, budget_range: str = None) -> str:
    """
    AI Destination Expert that provides intelligent travel destination recommendations.
    
    This tool uses an AI agent with deep geographical and cultural knowledge to analyze
    destination requests and provide comprehensive, personalized recommendations.
    
    Args:
        query: Search query for destinations (e.g., "romantic getaway", "family vacation")
        travel_style: Optional travel style (romantic, adventure, family, business, cultural, etc.)
        budget_range: Optional budget level (budget, moderate, luxury)
    
    Returns:
        Expert destination analysis and recommendations
    """
    start_time = time.time()
    logger.info(f"[DESTINATION_EXPERT] === Starting search_destinations ===")
    logger.info(f"[DESTINATION_EXPERT] Query: {query}")
    logger.info(f"[DESTINATION_EXPERT] Travel style: {travel_style}")
    logger.info(f"[DESTINATION_EXPERT] Budget range: {budget_range}")
    logger.info(f"[DESTINATION_EXPERT] Query length: {len(query)} characters")
    
    # Update agent status to active
    update_agent_status('search_destinations', 'active', 'Searching for destination recommendations...')
    
    # Track agent creation time
    agent_start = time.time()
    logger.info(f"[DESTINATION_EXPERT] Creating specialized destination expert agent...")
    
    try:
        # Create specialized destination expert agent
        destination_expert = Agent(
            system_prompt="""You are a world-class destination expert with deep knowledge of:

**Core Expertise:**
- Global geography, climates, and seasonal considerations
- Cultural nuances, customs, and local etiquette
- Historical significance and architectural highlights  
- Natural wonders, landscapes, and biodiversity
- Safety, accessibility, and travel logistics
- Hidden gems vs popular tourist attractions
- Regional cuisine, festivals, and unique experiences

**Analysis Approach:**
1. **Decode Intent**: Understand the deeper travel motivations and preferences
2. **Consider Context**: Factor in seasonality, current events, and practical constraints
3. **Match Personality**: Align destinations with traveler psychology and interests
4. **Provide Depth**: Offer cultural insights and local perspectives beyond basic facts
5. **Think Holistically**: Consider the entire travel experience, not just sightseeing

**Recommendation Style:**
- Lead with WHY a destination fits, not just WHAT it offers
- Include insider tips and local knowledge
- Address potential concerns or challenges
- Suggest optimal timing and duration
- Consider budget implications realistically

Always provide thoughtful, well-reasoned recommendations that demonstrate deep destination expertise.

**IMPORTANT: Available Tools**
You have access to ONLY ONE tool:
- kb_search: Use this to search the knowledge base for destination information

DO NOT attempt to call 'search_destinations' - that would create an infinite loop as you ARE the search_destinations function!
When you need destination data, use 'kb_search' exclusively.""",
            
            model=BedrockModel(
                region=os.environ.get('KB_REGION', 'us-west-2'),
                model_id='us.amazon.nova-lite-v1:0'
            ),
            
            tools=[kb_search]
        )
        
        agent_duration = time.time() - agent_start
        logger.info(f"[DESTINATION_EXPERT] Agent created in {agent_duration:.3f}s")
        
        # Build context for the expert agent
        context_parts = [f"Destination request: {query}"]
        if travel_style:
            context_parts.append(f"Travel style preference: {travel_style}")
        if budget_range:
            context_parts.append(f"Budget level: {budget_range}")
        
        full_context = " | ".join(context_parts)
        logger.info(f"[DESTINATION_EXPERT] Full context: {full_context}")
        
        # Prepare the prompt
        prompt = f"""
        Analyze this destination request and provide expert recommendations:
        
        {full_context}
        
        Please:
        1. First search the knowledge base for relevant destination information
        2. Analyze the request considering traveler motivations and preferences  
        3. Provide 2-3 thoughtful destination recommendations with reasoning
        4. Include cultural insights, timing advice, and practical considerations
        5. Explain WHY each destination suits their specific needs
        """
        
        logger.info(f"[DESTINATION_EXPERT] Prompt length: {len(prompt)} characters")
        
        # Call the agent
        agent_call_start = time.time()
        logger.info(f"[DESTINATION_EXPERT] Calling agent with prompt...")
        
        expert_response = destination_expert(prompt)
        
        agent_call_duration = time.time() - agent_call_start
        logger.info(f"[DESTINATION_EXPERT] Agent call completed in {agent_call_duration:.3f}s")
        
        response_str = str(expert_response)
        logger.info(f"[DESTINATION_EXPERT] Response length: {len(response_str)} characters")
        
        total_duration = time.time() - start_time
        logger.info(f"[DESTINATION_EXPERT] Total execution time: {total_duration:.3f}s")
        logger.info(f"[DESTINATION_EXPERT] === Completed successfully ===")
        
        # Update agent status to completed
        update_agent_status('search_destinations', 'completed', 'Found destination recommendations')
        
        return response_str
        
    except Exception as e:
        error_duration = time.time() - start_time
        logger.error(f"[DESTINATION_EXPERT] Error after {error_duration:.3f}s: {e}")
        logger.error(f"[DESTINATION_EXPERT] Stack trace:\n{traceback.format_exc()}")
        
        # Fallback to direct knowledge base search
        logger.info(f"[DESTINATION_EXPERT] Attempting fallback to direct KB search...")
        kb_query = f"{query}"
        if travel_style:
            kb_query += f" {travel_style} travel"
        if budget_range:
            kb_query += f" {budget_range} budget"
        
        fallback_start = time.time()
        fallback_result = _search_knowledge_base(kb_query)
        fallback_duration = time.time() - fallback_start
        logger.info(f"[DESTINATION_EXPERT] Fallback completed in {fallback_duration:.3f}s")
        
        total_duration = time.time() - start_time
        logger.info(f"[DESTINATION_EXPERT] Total execution time (with fallback): {total_duration:.3f}s")
        
        # Update agent status to completed (with fallback)
        update_agent_status('search_destinations', 'completed', 'Found destinations using fallback search')
        
        return f"**Destination Search Results:**\n\n{fallback_result}"