"""
Quick Lambda Proxy Solution
Adapts REST API calls to the existing orchestrator Lambda format
"""

import json
import boto3
import uuid
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
lambda_client = boto3.client('lambda')
dynamodb = boto3.resource('dynamodb')

# Environment variables
ORCHESTRATOR_FUNCTION_NAME = os.environ.get('ORCHESTRATOR_FUNCTION_NAME', 'travel-planner-orchestrator')
PLANS_TABLE_NAME = os.environ.get('PLANS_TABLE_NAME', 'travel-planner-plans')
REGION = os.environ.get('AWS_REGION', 'us-west-2')

# Initialize DynamoDB table
plans_table = dynamodb.Table(PLANS_TABLE_NAME)


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for DynamoDB Decimal types."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def create_cors_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create a response with CORS headers."""
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }


def handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Main proxy handler for API Gateway requests."""
    
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Handle OPTIONS requests for CORS
    if event.get('httpMethod') == 'OPTIONS':
        return create_cors_response(200, {'message': 'OK'})
    
    # Extract path and method
    path = event.get('path', '')
    method = event.get('httpMethod', '')
    
    try:
        # Route to appropriate handler
        if path == '/api/planning/start' and method == 'POST':
            return handle_start_planning(event)
        elif path == '/api/planning/continue' and method == 'POST':
            return handle_continue_planning(event)
        elif path.startswith('/api/planning/') and path.endswith('/status') and method == 'GET':
            plan_id = path.split('/')[-2]
            return handle_get_status(plan_id)
        elif path.startswith('/api/planning/') and path.endswith('/finalize') and method == 'POST':
            plan_id = path.split('/')[-2]
            return handle_finalize_plan(plan_id)
        else:
            return create_cors_response(404, {'error': 'Not found'})
            
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return create_cors_response(500, {'error': 'Internal server error', 'message': str(e)})


def handle_start_planning(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle POST /api/planning/start"""
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        user_goal = body.get('user_goal', '')
        user_preferences = body.get('user_preferences', {})
        user_id = body.get('user_id', 'default')
        
        if not user_goal:
            return create_cors_response(400, {'error': 'user_goal is required'})
        
        # Generate plan ID
        plan_id = f"plan-{str(uuid.uuid4())}"
        
        logger.info(f"Starting new plan: {plan_id} for goal: {user_goal}")
        
        # Store initial plan state in DynamoDB
        timestamp = datetime.utcnow().isoformat()
        plan_item = {
            'plan_id': plan_id,
            'user_id': user_id,
            'status': 'planning',
            'user_goal': user_goal,
            'user_preferences': user_preferences,
            'created_at': timestamp,
            'updated_at': timestamp,
            'conversation_history': [],
            'travel_plan': {}
        }
        
        try:
            plans_table.put_item(Item=plan_item)
        except ClientError as e:
            logger.error(f"Failed to create plan in DynamoDB: {e}")
            # Continue even if DynamoDB fails
        
        # Prepare Lambda event for orchestrator
        orchestrator_event = {
            'prompt': user_goal,
            'plan_id': plan_id,  # Pass plan_id for context
            'user_preferences': user_preferences
        }
        
        logger.info(f"Invoking orchestrator with event: {json.dumps(orchestrator_event)}")
        
        # Invoke the orchestrator Lambda asynchronously
        try:
            response = lambda_client.invoke(
                FunctionName=ORCHESTRATOR_FUNCTION_NAME,
                InvocationType='Event',  # Async invocation
                Payload=json.dumps(orchestrator_event)
            )
            
            logger.info(f"Orchestrator invoked asynchronously. Status code: {response['StatusCode']}")
            
            # Return success response immediately
            return create_cors_response(200, {
                'success': True,
                'plan_id': plan_id,
                'status': 'planning',
                'initial_response': "I'll help you plan your trip to Paris. Let me analyze the best options for flights, hotels, and activities. This may take a moment as I research the best recommendations for you.",
                'message': 'Planning in progress. Poll the status endpoint or connect via WebSocket for updates.'
            })
            
        except ClientError as e:
            logger.error(f"Failed to invoke orchestrator: {e}")
            return create_cors_response(500, {
                'success': False,
                'error': 'Failed to start planning',
                'message': str(e)
            })
            
    except json.JSONDecodeError:
        return create_cors_response(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        logger.error(f"Error in start_planning: {str(e)}", exc_info=True)
        return create_cors_response(500, {'error': 'Internal server error', 'message': str(e)})


def handle_continue_planning(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle POST /api/planning/continue"""
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        plan_id = body.get('plan_id', '')
        user_input = body.get('user_input', '')
        
        if not plan_id or not user_input:
            return create_cors_response(400, {'error': 'plan_id and user_input are required'})
        
        logger.info(f"Continuing plan: {plan_id} with input: {user_input}")
        
        # Get existing plan from DynamoDB
        try:
            response = plans_table.get_item(Key={'plan_id': plan_id})
            plan = response.get('Item')
            
            if not plan:
                return create_cors_response(404, {'error': 'Plan not found'})
                
        except ClientError as e:
            logger.error(f"Failed to get plan from DynamoDB: {e}")
            # Create minimal plan object if DynamoDB fails
            plan = {
                'plan_id': plan_id,
                'conversation_history': [],
                'user_goal': user_input
            }
        
        # Build context from conversation history
        context = f"Original goal: {plan.get('user_goal', '')}\n"
        if plan.get('conversation_history'):
            context += "Previous conversation:\n"
            for msg in plan['conversation_history'][-4:]:  # Last 4 messages for context
                context += f"{msg['role']}: {msg['content']}\n"
        
        # Prepare Lambda event
        orchestrator_event = {
            'prompt': f"{context}\n\nUser: {user_input}",
            'plan_id': plan_id,
            'continuation': True
        }
        
        # Invoke orchestrator
        try:
            response = lambda_client.invoke(
                FunctionName=ORCHESTRATOR_FUNCTION_NAME,
                InvocationType='RequestResponse',
                Payload=json.dumps(orchestrator_event)
            )
            
            # Parse response
            response_payload = json.loads(response['Payload'].read())
            assistant_response = response_payload if isinstance(response_payload, str) else str(response_payload)
            
            # Update conversation history
            timestamp = datetime.utcnow().isoformat()
            new_history = plan.get('conversation_history', []) + [
                {'role': 'user', 'content': user_input, 'timestamp': timestamp},
                {'role': 'assistant', 'content': assistant_response, 'timestamp': timestamp}
            ]
            
            # Update DynamoDB
            try:
                plans_table.update_item(
                    Key={'plan_id': plan_id},
                    UpdateExpression='SET conversation_history = :history, updated_at = :updated',
                    ExpressionAttributeValues={
                        ':history': new_history,
                        ':updated': timestamp
                    }
                )
            except ClientError as e:
                logger.error(f"Failed to update plan: {e}")
            
            return create_cors_response(200, {
                'success': True,
                'status': 'in_progress',
                'response': assistant_response
            })
            
        except ClientError as e:
            logger.error(f"Failed to invoke orchestrator: {e}")
            return create_cors_response(500, {
                'success': False,
                'error': 'Failed to continue planning',
                'message': str(e)
            })
            
    except json.JSONDecodeError:
        return create_cors_response(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        logger.error(f"Error in continue_planning: {str(e)}", exc_info=True)
        return create_cors_response(500, {'error': 'Internal server error', 'message': str(e)})


def handle_get_status(plan_id: str) -> Dict[str, Any]:
    """Handle GET /api/planning/{plan_id}/status"""
    
    try:
        logger.info(f"Getting status for plan: {plan_id}")
        
        # Get plan from DynamoDB
        try:
            response = plans_table.get_item(Key={'plan_id': plan_id})
            plan = response.get('Item')
            
            if not plan:
                return create_cors_response(404, {'error': 'Plan not found'})
                
        except ClientError as e:
            logger.error(f"Failed to get plan from DynamoDB: {e}")
            # Return mock data if DynamoDB fails
            return create_cors_response(200, {
                'plan_id': plan_id,
                'status': 'unknown',
                'error': 'Unable to retrieve plan status'
            })
        
        # Check if we have the orchestrator response
        orchestrator_response = plan.get('orchestrator_response')
        processing_duration = plan.get('processing_duration')
        
        # Extract travel plan details from conversation history or orchestrator response
        travel_plan = plan.get('travel_plan', {})
        
        # Try to parse structured data from the orchestrator response or last assistant message
        content_to_analyze = orchestrator_response
        if not content_to_analyze and plan.get('conversation_history'):
            for msg in reversed(plan['conversation_history']):
                if msg['role'] == 'assistant':
                    content_to_analyze = msg['content']
                    break
        
        if content_to_analyze:
            content_lower = content_to_analyze.lower()
            # Simple parsing to extract flight/hotel/activity mentions
            travel_plan['has_flights'] = 'flight' in content_lower
            travel_plan['has_hotels'] = 'hotel' in content_lower or 'accommodation' in content_lower
            travel_plan['has_activities'] = 'activity' in content_lower or 'activities' in content_lower
            travel_plan['has_itinerary'] = 'itinerary' in content_lower or 'day-by-day' in content_lower
        
        response_data = {
            'plan_id': plan_id,
            'status': plan.get('status', 'unknown'),
            'timestamp': datetime.utcnow().isoformat(),
            'agents': plan.get('agent_status', {}),  # Include agent status
            'current_stage': 'complete' if plan.get('status') == 'completed' else 'planning',
            'created_at': plan.get('created_at'),
            'updated_at': plan.get('updated_at'),
            'travel_plan': travel_plan
        }
        
        # Include the full response if completed
        if plan.get('status') == 'completed' and orchestrator_response:
            response_data['final_response'] = orchestrator_response
            response_data['processing_duration'] = processing_duration
        
        # Include error if failed
        if plan.get('status') == 'failed':
            response_data['error'] = plan.get('error_message', 'Planning failed')
        
        return create_cors_response(200, response_data)
        
    except Exception as e:
        logger.error(f"Error in get_status: {str(e)}", exc_info=True)
        return create_cors_response(500, {'error': 'Internal server error', 'message': str(e)})


def handle_finalize_plan(plan_id: str) -> Dict[str, Any]:
    """Handle POST /api/planning/{plan_id}/finalize"""
    
    try:
        logger.info(f"Finalizing plan: {plan_id}")
        
        # Update plan status in DynamoDB
        try:
            plans_table.update_item(
                Key={'plan_id': plan_id},
                UpdateExpression='SET #status = :status, updated_at = :updated',
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':status': 'completed',
                    ':updated': datetime.utcnow().isoformat()
                }
            )
            
            return create_cors_response(200, {
                'success': True,
                'plan_id': plan_id,
                'status': 'completed',
                'message': 'Plan finalized successfully'
            })
            
        except ClientError as e:
            logger.error(f"Failed to finalize plan: {e}")
            # Return success even if DynamoDB fails
            return create_cors_response(200, {
                'success': True,
                'plan_id': plan_id,
                'status': 'completed',
                'message': 'Plan finalized (warning: state not persisted)'
            })
            
    except Exception as e:
        logger.error(f"Error in finalize_plan: {str(e)}", exc_info=True)
        return create_cors_response(500, {'error': 'Internal server error', 'message': str(e)})