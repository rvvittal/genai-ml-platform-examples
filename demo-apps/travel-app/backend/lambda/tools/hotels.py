"""
Accommodation Curator Agent - AI hospitality specialist with deep accommodation knowledge
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


def _search_hotel_data(destination: str, check_in: str = None, check_out: str = None) -> str:
    """Helper function to search DSQL for hotel data."""
    start_time = time.time()
    logger.info(f"[HOTEL_DATA] Starting hotel data search")
    logger.info(f"[HOTEL_DATA] Destination: {destination}, Check-in: {check_in}, Check-out: {check_out}")
    
    try:
        # Import DSQL utilities
        import_start = time.time()
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from utils.dsql import search_hotels as dsql_search_hotels
        import_duration = time.time() - import_start
        logger.info(f"[HOTEL_DATA] DSQL module imported in {import_duration:.3f}s")
        
        # Search for hotels using DSQL (expects 3-letter city code)
        search_start = time.time()
        logger.info(f"[HOTEL_DATA] Calling DSQL search_hotels...")
        hotels = dsql_search_hotels(destination, check_in, check_out)
        search_duration = time.time() - search_start
        logger.info(f"[HOTEL_DATA] DSQL search completed in {search_duration:.3f}s")
        logger.info(f"[HOTEL_DATA] Found {len(hotels) if hotels else 0} hotels")
        
        if not hotels:
            no_data_msg = f"No hotel data found in {destination}"
            logger.info(f"[HOTEL_DATA] {no_data_msg}")
            return no_data_msg
        
        # Format hotel data for the agent
        format_start = time.time()
        result = f"Hotel data for {destination}:\n\n"
        
        for i, hotel in enumerate(hotels, 1):
            stars = "★" * int(hotel['star_rating']) if hotel['star_rating'] else ""
            result += f"{i}. {hotel['name']} {stars}\n"
            if 'address' in hotel and hotel['address']:
                result += f"   Location: {hotel['address']}\n"
            if 'city_name' in hotel and hotel['city_name']:
                result += f"   City: {hotel['city_name']}\n"
            result += f"   Star Rating: {hotel['star_rating']}/5\n"
            if 'base_price_min' in hotel and 'base_price_max' in hotel:
                result += f"   Price Range: ${hotel['base_price_min']} - ${hotel['base_price_max']}/night\n"
            if 'amenities' in hotel and hotel['amenities']:
                amenities = str(hotel['amenities']).replace('[', '').replace(']', '').replace('"', '')
                result += f"   Amenities: {amenities}\n"
            result += "\n"
        
        format_duration = time.time() - format_start
        logger.info(f"[HOTEL_DATA] Formatted results in {format_duration:.3f}s")
        
        total_duration = time.time() - start_time
        logger.info(f"[HOTEL_DATA] Total search completed in {total_duration:.3f}s")
        logger.info(f"[HOTEL_DATA] Response size: {len(result)} characters")
        
        return result
        
    except Exception as e:
        error_duration = time.time() - start_time
        logger.error(f"[HOTEL_DATA] Error after {error_duration:.3f}s: {e}")
        logger.error(f"[HOTEL_DATA] Stack trace:\n{traceback.format_exc()}")
        return f"Hotel data search failed: {e}"


@tool
def hotel_data_search(destination: str, check_in: str = None, check_out: str = None) -> str:
    """Search hotel database for accommodation options and details."""
    logger.info(f"[HOTEL_DATA_TOOL] Called with: destination={destination}, check_in={check_in}, check_out={check_out}")
    result = _search_hotel_data(destination, check_in, check_out)
    logger.info(f"[HOTEL_DATA_TOOL] Returning result of {len(result)} characters")
    return result


@tool
def search_hotels(destination: str, check_in: str = None, check_out: str = None, budget: str = None) -> str:
    """
    AI Accommodation Curator Agent that provides expert hospitality recommendations.
    
    This tool uses an AI agent with deep hospitality industry knowledge to analyze
    accommodation requests and curate properties that enhance the overall travel experience.
    
    Args:
        destination: Destination city or airport code
        check_in: Check-in date (YYYY-MM-DD format)
        check_out: Check-out date (YYYY-MM-DD format)  
        budget: Budget level (budget/moderate/luxury)
    
    Returns:
        Expert accommodation curation and recommendations
    """
    
    # Update agent status to active
    update_agent_status('search_hotels', 'active', f'Searching for hotels in {destination}...')
    
    # Create specialized accommodation curator agent
    accommodation_curator = Agent(
        system_prompt="""You are a hospitality expert and accommodation curator with deep industry knowledge:

**CRITICAL: City Code Requirements**
When searching for hotels, you MUST use the correct 3-letter city codes:
- New York = NYC
- Paris = CDG  
- Tokyo = NRT
- Sydney = SYD
- Bali/Denpasar = DPS
- Cape Town = CPT
- Rio de Janeiro = GIG

Always convert city names to their proper codes before searching!

**Core Expertise:**
- Hotel categories, luxury standards, and service quality indicators
- Neighborhood dynamics, local character, and accessibility considerations
- Property types (boutique, chain, independent, alternative accommodations)
- Amenity significance and guest experience impact
- Seasonal pricing patterns and availability trends
- Group dynamics and special accommodation needs
- Value propositions across different price ranges

**Curation Philosophy:**
1. **Match Guest Psychology**: Understand what type of experience the guest truly wants
2. **Consider Context**: Factor in trip purpose, companion type, and local activities
3. **Evaluate Value**: Assess total value beyond just price point
4. **Think Experience**: Consider how accommodation enhances or detracts from trip goals
5. **Address Practicalities**: Consider location convenience, transportation, and logistics

**Recommendation Style:**
- Lead with WHY a property fits the guest's needs and trip context
- Explain the neighborhood character and what it offers
- Highlight unique features or experiences that add value
- Address potential drawbacks honestly and suggest mitigations
- Consider the total guest journey from arrival to departure
- Match recommendations to traveler psychology and preferences

Always curate accommodations that enhance the overall travel experience, not just provide a place to sleep.

**IMPORTANT: Available Tools**
You have access to ONLY ONE tool:
- hotel_data_search: Use this to search the hotel database for accommodation options

DO NOT attempt to call 'search_hotels' - that would create an infinite loop as you ARE the search_hotels function!
When you need hotel data, use 'hotel_data_search' exclusively.""",
        
        model=BedrockModel(
            region=os.environ.get('KB_REGION', 'us-west-2'),
            model_id='us.amazon.nova-lite-v1:0'
        ),
        
        tools=[hotel_data_search]
    )
    
    # Build context for the accommodation curator
    context_parts = [f"Accommodation request for: {destination}"]
    if check_in:
        context_parts.append(f"Check-in: {check_in}")
    if check_out:
        context_parts.append(f"Check-out: {check_out}")
    if budget:
        context_parts.append(f"Budget level: {budget}")
    
    full_context = " | ".join(context_parts)
    
    start_time = time.time()
    logger.info(f"[ACCOMMODATION_CURATOR] === Starting search_hotels ===")
    logger.info(f"[ACCOMMODATION_CURATOR] Context: {full_context}")
    logger.info(f"[ACCOMMODATION_CURATOR] Destination: {destination}, Check-in: {check_in}, Check-out: {check_out}, Budget: {budget}")
    
    # Track agent creation time
    agent_start = time.time()
    logger.info(f"[ACCOMMODATION_CURATOR] Creating specialized accommodation curator agent...")
    
    try:
        agent_duration = time.time() - agent_start
        logger.info(f"[ACCOMMODATION_CURATOR] Agent created in {agent_duration:.3f}s")
        
        # Prepare the prompt
        prompt = f"""
        Analyze this accommodation request and provide expert curation:
        
        {full_context}
        
        Please:
        1. First search for available hotel data for this destination
        2. Analyze the properties considering guest experience and value proposition
        3. Consider neighborhood context and how it aligns with travel goals
        4. Evaluate amenities and services for their actual guest benefit
        5. Curate 2-3 top recommendations with detailed reasoning
        6. Explain WHY each property enhances the travel experience
        7. Include practical considerations (location, transportation, booking tips)
        8. Address any budget constraints thoughtfully
        """
        
        logger.info(f"[ACCOMMODATION_CURATOR] Prompt length: {len(prompt)} characters")
        
        # Call the agent
        agent_call_start = time.time()
        logger.info(f"[ACCOMMODATION_CURATOR] Calling agent with prompt...")
        
        curator_response = accommodation_curator(prompt)
        
        agent_call_duration = time.time() - agent_call_start
        logger.info(f"[ACCOMMODATION_CURATOR] Agent call completed in {agent_call_duration:.3f}s")
        
        response_str = str(curator_response)
        logger.info(f"[ACCOMMODATION_CURATOR] Response length: {len(response_str)} characters")
        
        total_duration = time.time() - start_time
        logger.info(f"[ACCOMMODATION_CURATOR] Total execution time: {total_duration:.3f}s")
        logger.info(f"[ACCOMMODATION_CURATOR] === Completed successfully ===")
        
        # Update agent status to completed
        update_agent_status('search_hotels', 'completed', 'Found hotel recommendations')
        
        return response_str
        
    except Exception as e:
        error_duration = time.time() - start_time
        logger.error(f"[ACCOMMODATION_CURATOR] Error after {error_duration:.3f}s: {e}")
        logger.error(f"[ACCOMMODATION_CURATOR] Stack trace:\n{traceback.format_exc()}")
        
        # Fallback to direct hotel data search
        logger.info(f"[ACCOMMODATION_CURATOR] Attempting fallback to direct hotel data search...")
        fallback_start = time.time()
        fallback_result = _search_hotel_data(destination, check_in, check_out)
        fallback_duration = time.time() - fallback_start
        logger.info(f"[ACCOMMODATION_CURATOR] Fallback completed in {fallback_duration:.3f}s")
        
        if "No hotel data found" in fallback_result or "search failed" in fallback_result:
            total_duration = time.time() - start_time
            logger.info(f"[ACCOMMODATION_CURATOR] Total execution time (with fallback): {total_duration:.3f}s")
            
            # Update agent status to completed
            update_agent_status('search_hotels', 'completed', 'Provided hotel category guidance')
            
            return f"""**Accommodation Curation for {destination}:**

Based on hospitality industry patterns for this destination:

**Property Recommendations by Category:**

**Luxury Experience:**
- Premium city center properties with concierge services
- Historic or boutique hotels with unique character
- Properties with signature amenities (spa, rooftop, fine dining)
- Expect: $300-500+ per night, exceptional service, prime locations

**Comfort & Value:**
- Well-located mid-scale hotels with essential amenities
- Reliable chain properties with consistent quality standards
- Properties balancing location, comfort, and reasonable pricing
- Expect: $150-300 per night, good service, convenient locations

**Budget-Conscious:**
- Clean, safe properties with basic amenities
- Strategic locations with good transportation access
- Focus on value and essential comfort over luxury
- Expect: $80-150 per night, basic service, functional accommodations

**Curation Advice:**
- Book directly with hotels for potential upgrades and perks
- Consider neighborhood character vs convenience tradeoffs
- Factor in total costs including parking, resort fees, and location accessibility
- Read recent reviews focusing on service quality and cleanliness

Note: Specific property data temporarily unavailable, showing category guidance."""
        else:
            total_duration = time.time() - start_time
            logger.info(f"[ACCOMMODATION_CURATOR] Total execution time (with fallback): {total_duration:.3f}s")
            
            # Update agent status to completed
            update_agent_status('search_hotels', 'completed', 'Found hotels using direct search')
            
            return f"**Available Properties:**\n\n{fallback_result}\n\nNote: For expert curation analysis and personalized recommendations, please try again when the accommodation curator agent is fully operational."