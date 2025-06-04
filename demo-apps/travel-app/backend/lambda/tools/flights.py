"""
Flight Strategy Agent - AI flight specialist that optimizes routing, timing, and costs
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


def _search_flight_data(origin: str, destination: str, travel_date: str = None) -> str:
    """Helper function to search DSQL for flight data."""
    start_time = time.time()
    logger.info(f"[FLIGHT_DATA] Starting flight data search")
    logger.info(f"[FLIGHT_DATA] Origin: {origin}, Destination: {destination}, Date: {travel_date}")
    
    try:
        # Import DSQL utilities
        import_start = time.time()
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from utils.dsql import search_flights as dsql_search_flights
        import_duration = time.time() - import_start
        logger.info(f"[FLIGHT_DATA] DSQL module imported in {import_duration:.3f}s")
        
        # Search for flights using DSQL
        search_start = time.time()
        logger.info(f"[FLIGHT_DATA] Calling DSQL search_flights...")
        flights = dsql_search_flights(origin, destination, travel_date)
        search_duration = time.time() - search_start
        logger.info(f"[FLIGHT_DATA] DSQL search completed in {search_duration:.3f}s")
        logger.info(f"[FLIGHT_DATA] Found {len(flights) if flights else 0} flights")
        
        if not flights:
            no_data_msg = f"No flight data found from {origin} to {destination} for {travel_date or 'any date'}"
            logger.info(f"[FLIGHT_DATA] {no_data_msg}")
            return no_data_msg
        
        # Format flight data for the agent
        format_start = time.time()
        result = f"Flight data from {origin} to {destination}:\n\n"
        
        for i, flight in enumerate(flights, 1):
            airlines = flight.get('airlines', 'Multiple Airlines')
            result += f"{i}. {airlines} Routes\n"
            result += f"   Route: {flight['origin_city']} → {flight['destination_city']}\n"
            if 'flight_duration_minutes' in flight:
                result += f"   Duration: {flight['flight_duration_minutes']} minutes\n"
            if 'distance_km' in flight:
                result += f"   Distance: {flight['distance_km']} km\n"
            result += "\n"
        
        format_duration = time.time() - format_start
        logger.info(f"[FLIGHT_DATA] Formatted results in {format_duration:.3f}s")
        
        total_duration = time.time() - start_time
        logger.info(f"[FLIGHT_DATA] Total search completed in {total_duration:.3f}s")
        logger.info(f"[FLIGHT_DATA] Response size: {len(result)} characters")
        
        return result
        
    except Exception as e:
        error_duration = time.time() - start_time
        logger.error(f"[FLIGHT_DATA] Error after {error_duration:.3f}s: {e}")
        logger.error(f"[FLIGHT_DATA] Stack trace:\n{traceback.format_exc()}")
        return f"Flight data search failed: {e}"


@tool
def flight_data_search(origin: str, destination: str, travel_date: str = None) -> str:
    """Search flight database for route and schedule information."""
    logger.info(f"[FLIGHT_DATA_TOOL] Called with: origin={origin}, destination={destination}, date={travel_date}")
    result = _search_flight_data(origin, destination, travel_date)
    logger.info(f"[FLIGHT_DATA_TOOL] Returning result of {len(result)} characters")
    return result


@tool
def search_flights(origin: str, destination: str, travel_date: str = None) -> str:
    """
    AI Flight Strategy Agent that optimizes flight search with expert routing knowledge.
    
    This tool uses an AI agent with deep aviation industry knowledge to analyze
    flight requests and provide strategic recommendations on routing, timing, and costs.
    
    Args:
        origin: Origin airport code (e.g., JFK, LAX) or city name
        destination: Destination airport code or city name  
        travel_date: Optional travel date (YYYY-MM-DD format)
    
    Returns:
        Expert flight strategy analysis and recommendations
    """
    
    # Update agent status to active
    update_agent_status('search_flights', 'active', f'Searching flights from {origin} to {destination}...')
    
    # Create specialized flight strategy agent
    flight_strategist = Agent(
        system_prompt="""You are an expert flight strategist with deep aviation industry knowledge:

**CRITICAL: Airport Code Requirements**
When searching for flights, you MUST use the correct 3-letter airport codes:
- New York airports: JFK, LGA, EWR (use JFK as default)
- Paris airports: CDG, ORY (use CDG as default)
- Tokyo airports: NRT (Narita), HND (use NRT as default)
- Sydney: SYD
- Bali/Denpasar: DPS
- Cape Town: CPT
- Rio de Janeiro: GIG

Always convert city names to their proper airport codes before searching!

**Core Expertise:**
- Global airport hubs, connections, and routing optimization
- Airline alliances, partnerships, and code-sharing agreements
- Seasonal demand patterns and pricing dynamics
- Aircraft types, capacity, and route efficiency
- Time zone considerations and jet lag minimization
- Alternative airports and routing strategies
- Booking timing and fare class optimization

**Strategic Analysis:**
1. **Route Optimization**: Identify the most efficient routing options
2. **Timing Strategy**: Consider seasonal patterns, day-of-week effects, and demand cycles
3. **Cost vs Convenience**: Analyze tradeoffs between price, duration, and convenience
4. **Alternative Options**: Suggest nearby airports or indirect routings when beneficial
5. **Booking Recommendations**: Advise on optimal booking timing and strategies

**Recommendation Style:**
- Explain the reasoning behind route suggestions
- Consider both direct and connecting flight options
- Factor in traveler preferences (time vs cost vs convenience)
- Provide strategic timing advice for booking and travel
- Address potential issues like long layovers or tight connections
- Include insights about airline service quality and reliability

Always think strategically about the entire journey, not just individual flights.

**IMPORTANT: Available Tools**
You have access to ONLY ONE tool:
- flight_data_search: Use this to search the flight database for route and schedule information

DO NOT attempt to call 'search_flights' - that would create an infinite loop as you ARE the search_flights function!
When you need flight data, use 'flight_data_search' exclusively.""",
        
        model=BedrockModel(
            region=os.environ.get('KB_REGION', 'us-west-2'),
            model_id='us.anthropic.claude-3-5-sonnet-20241022-v2:0'
        ),
        
        tools=[flight_data_search]
    )
    
    # Build context for the flight strategist
    context_parts = [f"Flight request: {origin} to {destination}"]
    if travel_date:
        context_parts.append(f"Travel date: {travel_date}")
    
    full_context = " | ".join(context_parts)
    
    start_time = time.time()
    logger.info(f"[FLIGHT_STRATEGIST] === Starting search_flights ===")
    logger.info(f"[FLIGHT_STRATEGIST] Origin: {origin}, Destination: {destination}, Date: {travel_date}")
    logger.info(f"[FLIGHT_STRATEGIST] Context: {full_context}")
    
    # Track agent creation time
    agent_start = time.time()
    logger.info(f"[FLIGHT_STRATEGIST] Creating specialized flight strategy agent...")
    
    try:
        agent_duration = time.time() - agent_start
        logger.info(f"[FLIGHT_STRATEGIST] Agent created in {agent_duration:.3f}s")
        
        # Prepare the prompt
        prompt = f"""
        Analyze this flight request and provide strategic recommendations:
        
        {full_context}
        
        Please:
        1. First use the flight_data_search tool to get flight data for this route
        2. Analyze the routing options and efficiency considerations
        3. Evaluate timing factors (seasonal demand, day-of-week patterns)
        4. Consider alternative airports or routing strategies if beneficial
        5. Provide strategic recommendations with clear reasoning
        6. Include booking timing advice and cost optimization tips
        7. Address any potential challenges or considerations for this route
        
        REMEMBER: Use flight_data_search tool to get data - do NOT call search_flights!
        """
        
        logger.info(f"[FLIGHT_STRATEGIST] Prompt length: {len(prompt)} characters")
        
        # Call the agent
        agent_call_start = time.time()
        logger.info(f"[FLIGHT_STRATEGIST] Calling agent with prompt...")
        
        strategy_response = flight_strategist(prompt)
        
        agent_call_duration = time.time() - agent_call_start
        logger.info(f"[FLIGHT_STRATEGIST] Agent call completed in {agent_call_duration:.3f}s")
        
        response_str = str(strategy_response)
        logger.info(f"[FLIGHT_STRATEGIST] Response length: {len(response_str)} characters")
        
        total_duration = time.time() - start_time
        logger.info(f"[FLIGHT_STRATEGIST] Total execution time: {total_duration:.3f}s")
        logger.info(f"[FLIGHT_STRATEGIST] === Completed successfully ===")
        
        return response_str
        
    except Exception as e:
        error_duration = time.time() - start_time
        logger.error(f"[FLIGHT_STRATEGIST] Error after {error_duration:.3f}s: {e}")
        logger.error(f"[FLIGHT_STRATEGIST] Stack trace:\n{traceback.format_exc()}")
        
        # Fallback to direct flight data search
        logger.info(f"[FLIGHT_STRATEGIST] Attempting fallback to direct flight data search...")
        fallback_start = time.time()
        fallback_result = _search_flight_data(origin, destination, travel_date)
        fallback_duration = time.time() - fallback_start
        logger.info(f"[FLIGHT_STRATEGIST] Fallback completed in {fallback_duration:.3f}s")
        
        if "No flight data found" in fallback_result or "search failed" in fallback_result:
            total_duration = time.time() - start_time
            logger.info(f"[FLIGHT_STRATEGIST] Total execution time (with fallback): {total_duration:.3f}s")
            
            # Update agent status to completed
            update_agent_status('search_flights', 'completed', 'Provided strategic flight guidance')
            
            return f"""**Flight Strategy Analysis for {origin} to {destination}:**

Based on aviation industry patterns for this route:

**Routing Recommendations:**
- Direct flights typically available with major carriers
- Consider hub connections through major airports if direct options limited
- Alternative nearby airports may offer competitive pricing

**Timing Strategy:**
- Book domestic flights 1-3 months in advance for best pricing
- Book international flights 2-8 weeks in advance
- Tuesday/Wednesday departures often have lower demand and pricing
- Avoid peak travel periods (holidays, summer) when possible

**Cost Optimization:**
- Compare prices across multiple booking platforms
- Consider nearby airports within reasonable driving distance
- Flexible date searches can reveal significant savings
- Morning flights often priced lower than evening departures

**Booking Recommendations:**
- Monitor prices for 1-2 weeks before booking if not urgent
- Clear browser cookies between searches to avoid price tracking
- Consider basic economy vs standard economy value proposition

Note: Specific flight data temporarily unavailable, showing strategic guidance."""
        else:
            total_duration = time.time() - start_time
            logger.info(f"[FLIGHT_STRATEGIST] Total execution time (with fallback): {total_duration:.3f}s")
            
            # Update agent status to completed
            update_agent_status('search_flights', 'completed', 'Found flights using direct search')
            
            return f"**Flight Data Available:**\n\n{fallback_result}\n\nNote: For strategic analysis and optimization recommendations, please try again when the flight strategy agent is fully operational."