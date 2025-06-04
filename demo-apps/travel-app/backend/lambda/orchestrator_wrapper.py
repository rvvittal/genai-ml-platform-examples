"""
Orchestrator wrapper that handles async invocation and saves results to DynamoDB
"""

import json
import boto3
import logging
from datetime import datetime
from typing import Dict, Any
import os
from decimal import Decimal

# Import the original handler
from handler import handler as original_handler

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
PLANS_TABLE_NAME = os.environ.get('PLANS_TABLE_NAME', 'travel-planner-plans')
plans_table = dynamodb.Table(PLANS_TABLE_NAME)

# Initialize API Gateway Management API for WebSocket
WEBSOCKET_API_ID = os.environ.get('WEBSOCKET_API_ID')
WEBSOCKET_STAGE = os.environ.get('WEBSOCKET_STAGE', 'prod')
CONNECTIONS_TABLE_NAME = os.environ.get('CONNECTIONS_TABLE_NAME', 'travel-planner-websocket-connections')

if WEBSOCKET_API_ID:
    # Get the WebSocket endpoint from environment or construct it
    WEBSOCKET_ENDPOINT = os.environ.get('WEBSOCKET_ENDPOINT')
    if not WEBSOCKET_ENDPOINT and WEBSOCKET_API_ID:
        region = os.environ.get('AWS_REGION', 'us-west-2')
        WEBSOCKET_ENDPOINT = f"https://{WEBSOCKET_API_ID}.execute-api.{region}.amazonaws.com/{WEBSOCKET_STAGE}"
    
    if WEBSOCKET_ENDPOINT:
        # Remove the protocol and stage from the endpoint for the API Gateway Management API
        endpoint_url = WEBSOCKET_ENDPOINT.replace('wss://', 'https://').replace('ws://', 'http://')
        apigw_management = boto3.client('apigatewaymanagementapi', endpoint_url=endpoint_url)
        connections_table = dynamodb.Table(CONNECTIONS_TABLE_NAME)
    else:
        apigw_management = None
        connections_table = None
else:
    apigw_management = None
    connections_table = None


def emit_websocket_message(plan_id: str, message_type: str, payload: Dict[str, Any]) -> None:
    """
    Emit a WebSocket message to all connected clients for a specific plan.
    """
    if not apigw_management or not connections_table:
        logger.warning("WebSocket not configured, skipping message emission")
        return
    
    try:
        # Query connections for this plan_id
        response = connections_table.query(
            IndexName='plan-index',  # Assuming there's a GSI on plan_id
            KeyConditionExpression='plan_id = :plan_id',
            ExpressionAttributeValues={
                ':plan_id': plan_id
            }
        )
        
        connections = response.get('Items', [])
        logger.info(f"Found {len(connections)} connections for plan_id: {plan_id}")
        
        # Prepare the message
        message = json.dumps({
            'type': message_type,
            'payload': payload
        })
        
        # Send to each connection
        for connection in connections:
            connection_id = connection.get('connection_id')
            if not connection_id:
                continue
            
            try:
                apigw_management.post_to_connection(
                    ConnectionId=connection_id,
                    Data=message
                )
                logger.info(f"Sent {message_type} to connection: {connection_id}")
            except Exception as e:
                logger.error(f"Failed to send to connection {connection_id}: {e}")
                # Clean up stale connection
                try:
                    connections_table.delete_item(
                        Key={'connection_id': connection_id}
                    )
                except:
                    pass
    
    except Exception as e:
        logger.error(f"Error emitting WebSocket message: {e}")


def handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Wrapper handler that processes the request and saves results to DynamoDB.
    """
    
    # Extract plan_id if provided
    plan_id = event.get('plan_id')
    
    logger.info(f"Orchestrator wrapper invoked with plan_id: {plan_id}")
    logger.info(f"Event: {json.dumps(event)}")
    
    try:
        # Set plan_id in environment for tools to access
        if plan_id:
            os.environ['CURRENT_PLAN_ID'] = plan_id
        
        # Call the original handler
        start_time = datetime.utcnow()
        result = original_handler(event, context)
        end_time = datetime.utcnow()
        
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Original handler completed in {duration:.2f} seconds")
        logger.info(f"Result type: {type(result)}, length: {len(str(result))}")
        
        # If we have a plan_id, save the result to DynamoDB
        if plan_id:
            try:
                # Prepare the response content
                response_content = result if isinstance(result, str) else str(result)
                
                # Update the plan with the result
                plans_table.update_item(
                    Key={'plan_id': plan_id},
                    UpdateExpression="""
                        SET #status = :status, 
                            updated_at = :updated,
                            orchestrator_response = :response,
                            processing_duration = :duration,
                            conversation_history = list_append(
                                if_not_exists(conversation_history, :empty_list),
                                :new_message
                            )
                    """,
                    ExpressionAttributeNames={
                        '#status': 'status'
                    },
                    ExpressionAttributeValues={
                        ':status': 'completed',
                        ':updated': datetime.utcnow().isoformat(),
                        ':response': response_content,
                        ':duration': Decimal(str(round(duration, 3))),
                        ':empty_list': [],
                        ':new_message': [{
                            'role': 'assistant',
                            'content': response_content,
                            'timestamp': datetime.utcnow().isoformat()
                        }]
                    }
                )
                
                logger.info(f"Successfully saved result to DynamoDB for plan_id: {plan_id}")
                
                # Emit WebSocket message with the results
                emit_websocket_message(plan_id, 'results_updated', {
                    'results': response_content,
                    'status': 'completed',
                    'timestamp': datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Failed to save result to DynamoDB: {e}")
                # Don't fail the whole request if DynamoDB update fails
        
        return result
        
    except Exception as e:
        logger.error(f"Error in orchestrator wrapper: {e}", exc_info=True)
        
        # Try to update the plan status to failed
        if plan_id:
            try:
                plans_table.update_item(
                    Key={'plan_id': plan_id},
                    UpdateExpression='SET #status = :status, updated_at = :updated, error_message = :error',
                    ExpressionAttributeNames={
                        '#status': 'status'
                    },
                    ExpressionAttributeValues={
                        ':status': 'failed',
                        ':updated': datetime.utcnow().isoformat(),
                        ':error': str(e)
                    }
                )
            except:
                pass
        
        raise