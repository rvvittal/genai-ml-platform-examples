"""
Itinerary Compiler Agent - AI travel document specialist that creates comprehensive trip itineraries
"""

import logging
import time
import traceback
from strands import tool, Agent
from strands.models.bedrock import BedrockModel
import os
from datetime import datetime
from utils.status_tracker import update_agent_status

logger = logging.getLogger(__name__)


@tool
def compile_itinerary(
    destination: str,
    trip_details: str,
    flights: str = None,
    hotels: str = None,
    activities: str = None,
    budget_analysis: str = None
) -> str:
    """
    AI Itinerary Compiler Agent that creates comprehensive, well-formatted travel itineraries.
    
    This tool uses an AI agent with travel documentation expertise to compile all trip
    information into a beautiful, detailed markdown itinerary document.
    
    Args:
        destination: Primary destination for the trip
        trip_details: Overview of the trip (dates, travelers, purpose, etc.)
        flights: Flight information and recommendations
        hotels: Accommodation details and recommendations
        activities: Activity and experience recommendations
        budget_analysis: Budget breakdown and financial planning
    
    Returns:
        Comprehensive markdown-formatted travel itinerary
    """
    
    # Update agent status to active
    update_agent_status('compile_itinerary', 'active', f'Compiling itinerary for {destination}...')
    
    # Create specialized itinerary compiler agent
    itinerary_compiler = Agent(
        system_prompt="""You are a travel documentation expert who creates comprehensive, beautifully formatted travel itineraries:

**Core Expertise:**
- Travel document design and information architecture
- Chronological trip organization and daily scheduling
- Clear, scannable formatting for easy reference while traveling
- Inclusion of practical details (confirmation numbers, addresses, contact info)
- Budget tracking and expense organization
- Cultural context and travel tips integration
- Emergency information and contingency planning

**Document Creation Philosophy:**
1. **Clarity First**: Information should be instantly findable and understandable
2. **Practical Focus**: Include all details a traveler needs in the moment
3. **Visual Hierarchy**: Use formatting to guide the eye to important information
4. **Comprehensive Coverage**: Address all aspects of the trip in one document
5. **Mobile-Friendly**: Format for easy reading on phones while traveling

**Itinerary Structure:**
- **Header**: Trip title, dates, destination overview
- **Quick Reference**: Key information at a glance
- **Day-by-Day**: Detailed daily schedules with times and locations
- **Bookings**: All reservation details organized by category
- **Budget**: Clear breakdown of costs and payment methods
- **Tips & Notes**: Practical advice and cultural insights
- **Emergency Info**: Important contacts and contingency plans

**Formatting Guidelines:**
- Use clear markdown headers (##, ###) for sections
- Bold important details like times, prices, confirmation numbers
- Use bullet points for easy scanning
- Include emoji for visual interest and quick category identification
- Add horizontal rules (---) between major sections
- Use tables for structured data when appropriate

Always create itineraries that are both comprehensive and easy to use while traveling.

**IMPORTANT: Tool Availability**
You have NO external tools available - you are a pure document generation agent.
DO NOT attempt to call 'compile_itinerary' - that would create an infinite loop as you ARE the compile_itinerary function!
Generate the itinerary document based on the provided information alone.""",
        
        model=BedrockModel(
            region=os.environ.get('KB_REGION', 'us-west-2'),
            model_id='us.amazon.nova-pro-v1:0'
        ),
        
        tools=[]  # Itinerary compilation is purely document generation
    )
    
    # Build context for the itinerary compiler
    context_parts = []
    context_parts.append(f"Destination: {destination}")
    context_parts.append(f"Trip Overview: {trip_details}")
    
    if flights:
        context_parts.append(f"Flight Information: {flights}")
    if hotels:
        context_parts.append(f"Accommodation Details: {hotels}")
    if activities:
        context_parts.append(f"Activities & Experiences: {activities}")
    if budget_analysis:
        context_parts.append(f"Budget Analysis: {budget_analysis}")
    
    full_context = "\n\n---\n\n".join(context_parts)
    
    start_time = time.time()
    logger.info(f"[ITINERARY_COMPILER] === Starting compile_itinerary ===")
    logger.info(f"[ITINERARY_COMPILER] Destination: {destination}")
    logger.info(f"[ITINERARY_COMPILER] Trip details: {trip_details[:200] if trip_details else 'None'}...")
    logger.info(f"[ITINERARY_COMPILER] Has flights: {'Yes' if flights else 'No'} ({len(flights) if flights else 0} chars)")
    logger.info(f"[ITINERARY_COMPILER] Has hotels: {'Yes' if hotels else 'No'} ({len(hotels) if hotels else 0} chars)")
    logger.info(f"[ITINERARY_COMPILER] Has activities: {'Yes' if activities else 'No'} ({len(activities) if activities else 0} chars)")
    logger.info(f"[ITINERARY_COMPILER] Has budget: {'Yes' if budget_analysis else 'No'} ({len(budget_analysis) if budget_analysis else 0} chars)")
    logger.info(f"[ITINERARY_COMPILER] Full context length: {len(full_context)} characters")
    
    # Track agent creation time
    agent_start = time.time()
    logger.info(f"[ITINERARY_COMPILER] Creating specialized itinerary compiler agent...")
    
    try:
        agent_duration = time.time() - agent_start
        logger.info(f"[ITINERARY_COMPILER] Agent created in {agent_duration:.3f}s")
        
        # Prepare the prompt
        prompt = f"""
        Create a comprehensive travel itinerary document based on this information:
        
        {full_context}
        
        Please create a well-formatted markdown document that includes:
        
        1. **Trip Header** with title, dates, and destination overview
        2. **Quick Reference Card** with essential information
        3. **Flight Details** formatted clearly with all relevant times and confirmation info
        4. **Accommodation Information** with addresses, check-in/out times, and amenities
        5. **Day-by-Day Itinerary** organizing activities chronologically
        6. **Budget Breakdown** showing all costs clearly
        7. **Practical Tips** for the destination
        8. **Emergency Contacts** and important information
        
        Format the document to be:
        - Easy to read on mobile devices
        - Comprehensive yet scannable
        - Practical for use while traveling
        - Visually organized with clear sections
        
        Use markdown formatting, emojis, and clear visual hierarchy to make the itinerary both beautiful and functional.
        """
        
        logger.info(f"[ITINERARY_COMPILER] Prompt length: {len(prompt)} characters")
        
        # Call the agent
        agent_call_start = time.time()
        logger.info(f"[ITINERARY_COMPILER] Calling agent with prompt...")
        
        itinerary_response = itinerary_compiler(prompt)
        
        agent_call_duration = time.time() - agent_call_start
        logger.info(f"[ITINERARY_COMPILER] Agent call completed in {agent_call_duration:.3f}s")
        
        response_str = str(itinerary_response)
        logger.info(f"[ITINERARY_COMPILER] Response length: {len(response_str)} characters")
        
        total_duration = time.time() - start_time
        logger.info(f"[ITINERARY_COMPILER] Total execution time: {total_duration:.3f}s")
        logger.info(f"[ITINERARY_COMPILER] === Completed successfully ===")
        
        # Update agent status to completed
        update_agent_status('compile_itinerary', 'completed', 'Itinerary compiled successfully')
        
        return response_str
        
    except Exception as e:
        error_duration = time.time() - start_time
        logger.error(f"[ITINERARY_COMPILER] Error after {error_duration:.3f}s: {e}")
        logger.error(f"[ITINERARY_COMPILER] Stack trace:\n{traceback.format_exc()}")
        
        # Fallback to basic template
        logger.info(f"[ITINERARY_COMPILER] Using fallback template...")
        
        total_duration = time.time() - start_time
        logger.info(f"[ITINERARY_COMPILER] Total execution time (with fallback): {total_duration:.3f}s")
        
        # Update agent status to completed (with fallback)
        update_agent_status('compile_itinerary', 'completed', 'Provided itinerary template')
        
        return f"""# 📍 {destination} Travel Itinerary

## 🗓️ Trip Overview
**Destination:** {destination}  
**Details:** {trip_details}

---

## ✈️ Flight Information
{flights if flights else "No flight information provided"}

---

## 🏨 Accommodation
{hotels if hotels else "No hotel information provided"}

---

## 🎭 Activities & Experiences
{activities if activities else "No activity information provided"}

---

## 💰 Budget Analysis
{budget_analysis if budget_analysis else "No budget analysis provided"}

---

## 📝 Travel Tips
- Always keep copies of important documents
- Check visa requirements before travel
- Register with your embassy if traveling internationally
- Keep emergency contacts readily available

---

## 🆘 Emergency Information
- Local Emergency Number: Research before travel
- Embassy Contact: Check your country's embassy website
- Travel Insurance: Keep policy number handy

---

*Itinerary generated on {datetime.now().strftime('%Y-%m-%d')}*

Note: For a more detailed itinerary, please try again when the Itinerary Compiler agent is fully operational."""