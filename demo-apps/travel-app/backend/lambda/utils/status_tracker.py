"""
Simple status tracking for agents/tools
"""
import boto3
import os
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
PLANS_TABLE_NAME = os.environ.get('PLANS_TABLE_NAME', 'travel-planner-plans')

def update_agent_status(agent_name: str, status: str, message: Optional[str] = None) -> None:
    """Update agent status in DynamoDB if plan_id is available."""
    try:
        # Get plan_id from environment (set by orchestrator wrapper)
        plan_id = os.environ.get('CURRENT_PLAN_ID')
        if not plan_id:
            logger.debug(f"No plan_id available, skipping status update for {agent_name}")
            return
        
        table = dynamodb.Table(PLANS_TABLE_NAME)
        timestamp = datetime.utcnow().isoformat()
        
        agent_data = {
            'status': status,
            'timestamp': timestamp,
            'message': message or f"{agent_name} {status}"
        }
        
        # First ensure agent_status exists
        table.update_item(
            Key={'plan_id': plan_id},
            UpdateExpression='SET agent_status = if_not_exists(agent_status, :empty_map)',
            ExpressionAttributeValues={
                ':empty_map': {}
            }
        )
        
        # Then update the specific agent status
        table.update_item(
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
        
        logger.info(f"Updated {agent_name} status to {status} for plan {plan_id}")
        
    except Exception as e:
        logger.error(f"Failed to update agent status: {e}")
        # Don't fail the tool execution