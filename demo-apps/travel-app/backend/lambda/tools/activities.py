"""
Experience Curator Agent - AI activity specialist that creates meaningful travel experiences
"""

import logging
import sys
import os
import time
import traceback
from strands import tool, Agent
from strands.models.bedrock import BedrockModel
from utils.status_tracker import update_agent_status

logger = logging.getLogger(__name__)


def _search_activity_data(destination: str, activity_type: str = None) -> str:
    """Helper function to search DSQL for activity data."""
    start_time = time.time()
    logger.info(f"[ACTIVITY_DATA] Starting activity data search")
    logger.info(f"[ACTIVITY_DATA] Destination: {destination}, Activity type: {activity_type}")
    
    try:
        # Import DSQL utilities
        import_start = time.time()
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from utils.dsql import search_activities as dsql_search_activities
        import_duration = time.time() - import_start
        logger.info(f"[ACTIVITY_DATA] DSQL module imported in {import_duration:.3f}s")
        
        # Search for activities using DSQL (expects 3-letter city code)
        search_start = time.time()
        logger.info(f"[ACTIVITY_DATA] Calling DSQL search_activities...")
        activities = dsql_search_activities(destination, activity_type)
        search_duration = time.time() - search_start
        logger.info(f"[ACTIVITY_DATA] DSQL search completed in {search_duration:.3f}s")
        logger.info(f"[ACTIVITY_DATA] Found {len(activities) if activities else 0} activities")
        
        if not activities:
            no_data_msg = f"No activity data found in {destination} for {activity_type or 'any type'}"
            logger.info(f"[ACTIVITY_DATA] {no_data_msg}")
            return no_data_msg
        
        # Format activity data for the agent
        format_start = time.time()
        result = f"Activity data for {destination}:\n\n"
        
        for i, activity in enumerate(activities, 1):
            result += f"{i}. {activity['name']}\n"
            if 'activity_type' in activity:
                result += f"   Type: {activity['activity_type']}\n"
            if 'duration_hours' in activity:
                result += f"   Duration: {activity['duration_hours']} hours\n"
            if 'base_price' in activity:
                result += f"   Price: ${activity['base_price']}/person\n"
            if 'rating' in activity:
                result += f"   Rating: {activity['rating']}/5\n"
            if 'description' in activity and activity['description']:
                result += f"   Description: {activity['description']}\n"
            if 'tags' in activity and activity['tags']:
                result += f"   Tags: {activity['tags']}\n"
            result += "\n"
        
        format_duration = time.time() - format_start
        logger.info(f"[ACTIVITY_DATA] Formatted results in {format_duration:.3f}s")
        
        total_duration = time.time() - start_time
        logger.info(f"[ACTIVITY_DATA] Total search completed in {total_duration:.3f}s")
        logger.info(f"[ACTIVITY_DATA] Response size: {len(result)} characters")
        
        return result
        
    except Exception as e:
        error_duration = time.time() - start_time
        logger.error(f"[ACTIVITY_DATA] Error after {error_duration:.3f}s: {e}")
        logger.error(f"[ACTIVITY_DATA] Stack trace:\n{traceback.format_exc()}")
        return f"Activity data search failed: {e}"


@tool
def activity_data_search(destination: str, activity_type: str = None) -> str:
    """Search activity database for experiences and attractions."""
    logger.info(f"[ACTIVITY_DATA_TOOL] Called with: destination={destination}, activity_type={activity_type}")
    result = _search_activity_data(destination, activity_type)
    logger.info(f"[ACTIVITY_DATA_TOOL] Returning result of {len(result)} characters")
    return result


@tool
def search_activities(destination: str, activity_type: str = None) -> str:
    """
    AI Experience Curator Agent that designs meaningful and memorable travel experiences.
    
    This tool uses an AI agent with deep cultural and experiential knowledge to analyze
    activity requests and curate experiences that create lasting travel memories.
    
    Args:
        destination: Destination city or region
        activity_type: Optional activity preference (cultural, adventure, relaxation, culinary, etc.)
    
    Returns:
        Expert experience curation and recommendations
    """
    
    # Update agent status to active
    update_agent_status('search_activities', 'active', f'Searching for activities in {destination}...')
    
    # Create specialized experience curator agent
    experience_curator = Agent(
        system_prompt="""You are an experience curator and cultural expert who designs meaningful travel experiences:

**CRITICAL: City Code Requirements**
When searching for activities, you MUST use the correct 3-letter city codes:
- New York = NYC
- Paris = CDG  
- Tokyo = NRT
- Sydney = SYD
- Bali/Denpasar = DPS
- Cape Town = CPT
- Rio de Janeiro = GIG

Always convert city names to their proper codes before searching!

**Core Expertise:**
- Cultural significance and historical context of destinations
- Local customs, traditions, and authentic experiences vs tourist traps
- Activity pacing and energy management throughout a trip
- Experiential psychology and what creates lasting memories
- Seasonal considerations and optimal timing for different activities
- Accessibility, safety, and practical logistics
- Value assessment beyond just price point

**Curation Philosophy:**
1. **Create Meaning**: Focus on experiences that connect travelers to local culture and place
2. **Consider Pace**: Balance active experiences with reflection and absorption time
3. **Think Progression**: Design activity sequences that build upon each other
4. **Match Energy**: Align activities with traveler energy levels and interests
5. **Seek Authenticity**: Prioritize genuine local experiences over commercialized attractions

**Experience Design Principles:**
- Lead with WHY an experience is meaningful, not just what it includes
- Consider the emotional journey and lasting impact on travelers
- Factor in local perspectives and cultural sensitivity
- Balance must-see highlights with unexpected discoveries
- Account for practical considerations (timing, transportation, preparation)
- Suggest complementary experiences that enhance each other

Always curate experiences that create genuine connections between travelers and destinations.

**IMPORTANT: Available Tools**
You have access to ONLY ONE tool:
- activity_data_search: Use this to search the activity database for experiences and attractions

DO NOT attempt to call 'search_activities' - that would create an infinite loop as you ARE the search_activities function!
When you need activity data, use 'activity_data_search' exclusively.""",
        
        model=BedrockModel(
            region=os.environ.get('KB_REGION', 'us-west-2'),
            model_id='us.amazon.nova-lite-v1:0'
        ),
        
        tools=[activity_data_search]
    )
    
    # Build context for the experience curator
    context_parts = [f"Experience request for: {destination}"]
    if activity_type:
        context_parts.append(f"Activity preference: {activity_type}")
    
    full_context = " | ".join(context_parts)
    
    start_time = time.time()
    logger.info(f"[EXPERIENCE_CURATOR] === Starting search_activities ===")
    logger.info(f"[EXPERIENCE_CURATOR] Context: {full_context}")
    logger.info(f"[EXPERIENCE_CURATOR] Destination: {destination}, Activity type: {activity_type}")
    
    # Track agent creation time
    agent_start = time.time()
    logger.info(f"[EXPERIENCE_CURATOR] Creating specialized experience curator agent...")
    
    try:
        agent_duration = time.time() - agent_start
        logger.info(f"[EXPERIENCE_CURATOR] Agent created in {agent_duration:.3f}s")
        
        # Prepare the prompt
        prompt = f"""
        Analyze this experience request and curate meaningful activities:
        
        {full_context}
        
        Please:
        1. First use the activity_data_search tool to get activity data for this destination
        2. Analyze the experiences considering cultural significance and authenticity
        3. Consider the emotional and educational value of different activities
        4. Think about pacing and how activities complement each other
        5. Curate 3-4 diverse experiences that create a well-rounded visit
        6. Explain WHY each experience is meaningful and memorable
        7. Include practical considerations (timing, preparation, cultural sensitivity)
        8. Suggest how to sequence activities for optimal flow and impact
        
        REMEMBER: Use activity_data_search tool to get data - do NOT call search_activities!
        """
        
        logger.info(f"[EXPERIENCE_CURATOR] Prompt length: {len(prompt)} characters")
        
        # Call the agent
        agent_call_start = time.time()
        logger.info(f"[EXPERIENCE_CURATOR] Calling agent with prompt...")
        
        curator_response = experience_curator(prompt)
        
        agent_call_duration = time.time() - agent_call_start
        logger.info(f"[EXPERIENCE_CURATOR] Agent call completed in {agent_call_duration:.3f}s")
        
        response_str = str(curator_response)
        logger.info(f"[EXPERIENCE_CURATOR] Response length: {len(response_str)} characters")
        
        total_duration = time.time() - start_time
        logger.info(f"[EXPERIENCE_CURATOR] Total execution time: {total_duration:.3f}s")
        logger.info(f"[EXPERIENCE_CURATOR] === Completed successfully ===")
        
        # Update agent status to completed
        update_agent_status('search_activities', 'completed', 'Found activity recommendations')
        
        return response_str
        
    except Exception as e:
        error_duration = time.time() - start_time
        logger.error(f"[EXPERIENCE_CURATOR] Error after {error_duration:.3f}s: {e}")
        logger.error(f"[EXPERIENCE_CURATOR] Stack trace:\n{traceback.format_exc()}")
        
        # Fallback to direct activity data search
        logger.info(f"[EXPERIENCE_CURATOR] Attempting fallback to direct activity data search...")
        fallback_start = time.time()
        fallback_result = _search_activity_data(destination, activity_type)
        fallback_duration = time.time() - fallback_start
        logger.info(f"[EXPERIENCE_CURATOR] Fallback completed in {fallback_duration:.3f}s")
        
        if "No activity data found" in fallback_result or "search failed" in fallback_result:
            total_duration = time.time() - start_time
            logger.info(f"[EXPERIENCE_CURATOR] Total execution time (with fallback): {total_duration:.3f}s")
            
            # Update agent status to completed
            update_agent_status('search_activities', 'completed', 'Provided activity framework')
            
            return f"""**Experience Curation for {destination}:**

Based on cultural and experiential patterns for this destination:

**Authentic Cultural Experiences:**
- Local neighborhood walking tours with resident guides
- Traditional craft workshops or cooking classes
- Cultural performances in intimate, non-touristy venues
- Market visits with local food tastings

**Natural & Historical Connections:**
- Significant historical sites with proper context and storytelling
- Natural areas that showcase local landscape and biodiversity
- Architecture tours highlighting unique design elements
- Seasonal festivals or community events (if timing aligns)

**Immersive Learning:**
- Museums with interactive or specialized collections
- Art galleries featuring local or regional artists
- Cultural centers explaining local traditions and customs
- Educational experiences that provide deeper understanding

**Memorable Moments:**
- Sunset/sunrise experiences at meaningful locations
- Local transportation experiences (historic trains, ferries, etc.)
- Photography walks in characteristic neighborhoods
- Encounters with local artisans or practitioners

**Experience Design Tips:**
- Start with overview experiences to gain context
- Intersperse active and contemplative activities
- Allow time for spontaneous discoveries
- Consider local meal timing and customs
- Book popular experiences in advance while leaving space for serendipity

Note: Specific activity data temporarily unavailable, showing experiential framework."""
        else:
            total_duration = time.time() - start_time
            logger.info(f"[EXPERIENCE_CURATOR] Total execution time (with fallback): {total_duration:.3f}s")
            
            # Update agent status to completed
            update_agent_status('search_activities', 'completed', 'Found activities using direct search')
            
            return f"**Available Activities:**\n\n{fallback_result}\n\nNote: For expert experience curation and meaningful activity sequencing, please try again when the experience curator agent is fully operational."