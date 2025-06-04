"""
Financial Planning Agent - AI budget strategist for travel cost optimization
"""

import logging
import time
import traceback
from strands import tool, Agent
from strands.models.bedrock import BedrockModel
import os
from utils.status_tracker import update_agent_status

logger = logging.getLogger(__name__)


@tool
def analyze_budget(trip_details: str, budget_amount: float) -> str:
    """
    AI Financial Planning Agent that provides strategic budget analysis and optimization.
    
    This tool uses an AI agent with financial planning expertise to analyze travel budgets
    and provide strategic recommendations for cost optimization and value maximization.
    
    Args:
        trip_details: Description of the trip (destination, duration, travelers, preferences)
        budget_amount: Total budget in USD
    
    Returns:
        Expert financial analysis and strategic budget recommendations
    """
    
    # Update agent status to active
    update_agent_status('analyze_budget', 'active', f'Analyzing budget of ${budget_amount:,.2f}...')
    
    # Create specialized financial planning agent
    financial_planner = Agent(
        system_prompt="""You are a financial planning expert specializing in travel budget optimization:

**Core Expertise:**
- Travel cost patterns across different destinations and seasons
- Strategic budget allocation for maximum value and experience quality
- Cost-saving techniques that don't compromise travel goals
- Financial risk management and contingency planning
- Currency considerations and international spending strategies
- Value assessment beyond just lowest price options
- Seasonal pricing patterns and booking optimization

**Financial Strategy Approach:**
1. **Value-First Thinking**: Prioritize spending that maximizes experience value
2. **Strategic Allocation**: Balance must-have vs nice-to-have expenditures
3. **Risk Management**: Plan for unexpected costs and contingencies
4. **Opportunity Cost**: Consider tradeoffs between different spending choices
5. **Long-term Perspective**: Factor in lasting value vs temporary savings

**Budget Optimization Principles:**
- Lead with traveler priorities and goals, then optimize around them
- Identify where premium spending delivers disproportionate value
- Find cost savings that don't impact core travel experiences
- Build in flexibility for spontaneous opportunities
- Consider total cost of ownership (hidden fees, exchange rates, etc.)
- Provide actionable, specific money-saving strategies

Always focus on maximizing travel value and experience within budget constraints.

**IMPORTANT: Tool Availability**
You have NO external tools available - you are a pure analytical agent.
DO NOT attempt to call 'analyze_budget' - that would create an infinite loop as you ARE the analyze_budget function!
Provide your financial analysis based on your expertise alone.""",
        
        model=BedrockModel(
            region=os.environ.get('KB_REGION', 'us-west-2'),
            model_id='us.amazon.nova-lite-v1:0'
        ),
        
        tools=[]  # Budget planning is primarily analytical, uses no external data tools
    )
    
    start_time = time.time()
    logger.info(f"[FINANCIAL_PLANNER] === Starting analyze_budget ===")
    logger.info(f"[FINANCIAL_PLANNER] Budget: ${budget_amount:,.2f}")
    logger.info(f"[FINANCIAL_PLANNER] Trip details: {trip_details[:200] if trip_details else 'None'}...")
    logger.info(f"[FINANCIAL_PLANNER] Trip details length: {len(trip_details) if trip_details else 0} characters")
    
    # Track agent creation time
    agent_start = time.time()
    logger.info(f"[FINANCIAL_PLANNER] Creating specialized financial planning agent...")
    
    try:
        agent_duration = time.time() - agent_start
        logger.info(f"[FINANCIAL_PLANNER] Agent created in {agent_duration:.3f}s")
        
        # Prepare the prompt
        prompt = f"""
        Analyze this travel budget and provide strategic financial planning:
        
        Trip Details: {trip_details}
        Total Budget: ${budget_amount:,.2f}
        
        Please provide:
        1. Strategic budget allocation tailored to this specific trip
        2. Analysis of where premium spending delivers the most value
        3. Specific cost-saving opportunities that don't compromise experience
        4. Risk management and contingency planning recommendations
        5. Booking timing strategies for different expense categories
        6. Hidden costs to watch out for and budget for
        7. Currency and payment strategy considerations if international
        8. Value optimization recommendations based on trip priorities
        
        Focus on actionable, specific advice that maximizes travel value within this budget.
        """
        
        logger.info(f"[FINANCIAL_PLANNER] Prompt length: {len(prompt)} characters")
        
        # Call the agent
        agent_call_start = time.time()
        logger.info(f"[FINANCIAL_PLANNER] Calling agent with prompt...")
        
        financial_response = financial_planner(prompt)
        
        agent_call_duration = time.time() - agent_call_start
        logger.info(f"[FINANCIAL_PLANNER] Agent call completed in {agent_call_duration:.3f}s")
        
        response_str = str(financial_response)
        logger.info(f"[FINANCIAL_PLANNER] Response length: {len(response_str)} characters")
        
        total_duration = time.time() - start_time
        logger.info(f"[FINANCIAL_PLANNER] Total execution time: {total_duration:.3f}s")
        logger.info(f"[FINANCIAL_PLANNER] === Completed successfully ===")
        
        # Update agent status to completed
        update_agent_status('analyze_budget', 'completed', 'Budget analysis complete')
        
        return response_str
        
    except Exception as e:
        error_duration = time.time() - start_time
        logger.error(f"[FINANCIAL_PLANNER] Error after {error_duration:.3f}s: {e}")
        logger.error(f"[FINANCIAL_PLANNER] Stack trace:\n{traceback.format_exc()}")
        
        # Fallback to basic budget analysis
        logger.info(f"[FINANCIAL_PLANNER] Using fallback budget analysis...")
        
        total_duration = time.time() - start_time
        logger.info(f"[FINANCIAL_PLANNER] Total execution time (with fallback): {total_duration:.3f}s")
        
        # Update agent status to completed (with fallback)
        update_agent_status('analyze_budget', 'completed', 'Provided budget framework')
        
        return f"""**Financial Planning Analysis for ${budget_amount:,.2f}:**

**Strategic Budget Allocation:**
Based on typical travel patterns and value optimization:

- **Transportation: 35-45%** (${budget_amount * 0.4:,.2f})
  - Domestic: 30-35%, International: 40-50%
  - Premium spending here saves time and reduces trip stress

- **Accommodation: 25-35%** (${budget_amount * 0.3:,.2f})
  - Location often more valuable than luxury amenities
  - Consider mid-range properties in prime locations

- **Experiences & Activities: 15-25%** (${budget_amount * 0.2:,.2f})
  - High-value spending category for memorable experiences
  - Mix of must-do highlights and spontaneous discoveries

- **Food & Daily Expenses: 15-20%** (${budget_amount * 0.15:,.2f})
  - Balance special dining with local, affordable options
  - Include contingency for unexpected opportunities

**Value Optimization Strategies:**
- Book transportation 6-8 weeks in advance for best prices
- Consider shoulder seasons for 20-40% savings across categories
- Mix of splurge and save decisions based on personal priorities
- Build 10-15% contingency buffer for flexibility and unexpected costs

**Cost-Saving Opportunities:**
- Mid-week travel typically 15-30% cheaper than weekends
- Direct booking with hotels often includes perks worth 10-15% extra
- Local transportation passes vs individual tickets
- Market meals and local favorites vs tourist restaurant pricing

Note: For personalized financial strategy analysis, please try again when the financial planning agent is fully operational."""