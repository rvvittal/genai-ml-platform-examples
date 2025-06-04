"""
Agent Status Tracking Utility
Tracks when each agent/tool is activated and completed
"""

import boto3
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable
import functools
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
PLANS_TABLE_NAME = os.environ.get('PLANS_TABLE_NAME', 'travel-planner-plans')
plans_table = dynamodb.Table(PLANS_TABLE_NAME)

# Agent status types
AGENT_STATUS_PENDING = 'pending'
AGENT_STATUS_ACTIVE = 'active'
AGENT_STATUS_COMPLETED = 'completed'
AGENT_STATUS_FAILED = 'failed'

# Map tool names to agent display names
AGENT_DISPLAY_NAMES = {
    'search_destinations': 'Destination Expert',
    'search_flights': 'Flight Specialist',
    'search_hotels': 'Hotel Expert',
    'search_activities': 'Activity Curator',
    'analyze_budget': 'Budget Analyst',
    'compile_itinerary': 'Itinerary Compiler'
}


def update_agent_status(plan_id: str, agent_name: str, status: str, 
                       message: Optional[str] = None, result: Optional[Any] = None) -> None:
    """Update the status of an agent in DynamoDB."""
    if not plan_id:
        logger.warning(f"No plan_id provided for agent status update: {agent_name}")
        return
    
    try:
        timestamp = datetime.utcnow().isoformat()
        agent_data = {
            'status': status,
            'timestamp': timestamp,
            'display_name': AGENT_DISPLAY_NAMES.get(agent_name, agent_name)
        }
        
        if message:
            agent_data['message'] = message
        
        if status == AGENT_STATUS_ACTIVE:
            agent_data['started_at'] = timestamp
        elif status in [AGENT_STATUS_COMPLETED, AGENT_STATUS_FAILED]:
            agent_data['completed_at'] = timestamp
            
        if result and status == AGENT_STATUS_COMPLETED:
            # Add a summary of the result
            if hasattr(result, '__dict__'):
                result_summary = str(result)[:200]  # First 200 chars
            else:
                result_summary = str(result)[:200]
            agent_data['result_summary'] = result_summary
        
        # Update DynamoDB
        plans_table.update_item(
            Key={'plan_id': plan_id},
            UpdateExpression='SET agent_status.#agent = :status, updated_at = :updated',
            ExpressionAttributeNames={
                '#agent': agent_name
            },
            ExpressionAttributeValues={
                ':status': agent_data,
                ':updated': timestamp
            }
        )
        
        logger.info(f"Updated agent status - Plan: {plan_id}, Agent: {agent_name}, Status: {status}")
        
    except Exception as e:
        logger.error(f"Failed to update agent status: {e}")
        # Don't fail the main operation


def track_agent(agent_name: str):
    """Decorator to track agent/tool execution status."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract plan_id from context if available
            plan_id = None
            
            # Try to get plan_id from kwargs
            if 'plan_id' in kwargs:
                plan_id = kwargs['plan_id']
            
            # Try to get from args if it's a dict with plan_id
            elif args and isinstance(args[0], dict) and 'plan_id' in args[0]:
                plan_id = args[0]['plan_id']
            
            # Look for context in various places
            for arg in args:
                if isinstance(arg, dict):
                    if 'plan_id' in arg:
                        plan_id = arg['plan_id']
                        break
                    elif 'context' in arg and isinstance(arg['context'], dict):
                        plan_id = arg['context'].get('plan_id')
                        if plan_id:
                            break
            
            # Mark agent as active
            if plan_id:
                update_agent_status(plan_id, agent_name, AGENT_STATUS_ACTIVE, 
                                  f"Processing {agent_name} request...")
            
            try:
                # Execute the actual function
                result = func(*args, **kwargs)
                
                # Mark agent as completed
                if plan_id:
                    update_agent_status(plan_id, agent_name, AGENT_STATUS_COMPLETED,
                                      f"Successfully completed {agent_name}", result)
                
                return result
                
            except Exception as e:
                # Mark agent as failed
                if plan_id:
                    update_agent_status(plan_id, agent_name, AGENT_STATUS_FAILED,
                                      f"Error in {agent_name}: {str(e)}")
                raise
        
        return wrapper
    return decorator


def get_agent_statuses(plan_id: str) -> Dict[str, Any]:
    """Get all agent statuses for a plan."""
    try:
        response = plans_table.get_item(Key={'plan_id': plan_id})
        plan = response.get('Item', {})
        return plan.get('agent_status', {})
    except Exception as e:
        logger.error(f"Failed to get agent statuses: {e}")
        return {}


def initialize_agent_statuses(plan_id: str) -> None:
    """Initialize all agents with pending status."""
    if not plan_id:
        return
    
    try:
        timestamp = datetime.utcnow().isoformat()
        agent_status = {}
        
        for tool_name, display_name in AGENT_DISPLAY_NAMES.items():
            agent_status[tool_name] = {
                'status': AGENT_STATUS_PENDING,
                'timestamp': timestamp,
                'display_name': display_name
            }
        
        plans_table.update_item(
            Key={'plan_id': plan_id},
            UpdateExpression='SET agent_status = :status, updated_at = :updated',
            ExpressionAttributeValues={
                ':status': agent_status,
                ':updated': timestamp
            }
        )
        
        logger.info(f"Initialized agent statuses for plan: {plan_id}")
        
    except Exception as e:
        logger.error(f"Failed to initialize agent statuses: {e}")