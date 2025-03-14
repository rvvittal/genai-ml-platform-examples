
from langchain_aws import ChatBedrock
from langgraph.graph import END
from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.graph import START, StateGraph

from typing import Annotated
from typing_extensions import TypedDict
from dotenv import load_dotenv
import os

from botocore.client import Config
import boto3
import mlflow

from tools import get_stock_price_data

load_dotenv()
_MLFLOW_URI = os.getenv('MLFLOW_URI_SMAI')
mlflow.set_tracking_uri(_MLFLOW_URI)

MODELID_CLAUDE3_HAIKU = os.getenv('MODELID')
AWS_REGION = os.getenv('AWS_REGION') 
bedrock_config = Config(
    connect_timeout=120, 
    read_timeout=120, 
    retries={
        "max_attempts": 200,
        "mode": "standard",
    })

kwargs: dict = {'temperature': 0.0,
                'top_k': 0,
                'max_tokens': 4096}

bedrock_runtime_client = boto3.client('bedrock-runtime', 
                                      config=bedrock_config, 
                                      region_name = AWS_REGION
                                      )

LLM = ChatBedrock(model_id=MODELID_CLAUDE3_HAIKU,
                  #model_kwargs=kwargs,
                  client=bedrock_runtime_client,
                  beta_use_converse_api=True,
                  region_name = AWS_REGION
                  )

TOOLS =  [get_stock_price_data]
llm_with_tools = LLM.bind_tools(TOOLS)

# Define langgraph state
class GraphState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

# Define the function that determines whether to continue or not
# Instrument the mlflow trace to export metrics from the langgraph node
@mlflow.trace(name="should_continue", attributes={"workflow": "agent_should_continue"}, span_type="graph.py")
def should_continue(state: GraphState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END

# LangGraph Node 
# Instrument the mlflow trace to export metrics from the langgraph node
@mlflow.trace(name="assistant", attributes={"workflow": "agent_assistant"}, span_type="graph.py")
def assistant(state: GraphState):
    system_prompt = """You are an AI assistant specialized in finance and stock market topics. 
    Your primary focus is to provide accurate and helpful information related to financial markets, 
    stocks, investments, and economic trends. Please limit your responses to these areas of expertise. 
    If asked about topics outside of finance and the stock market, politely redirect the conversation 
    to your area of specialization."""
    
    messages = [HumanMessage(content=system_prompt)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# Node
tool_node = ToolNode(TOOLS)

@mlflow.trace(name="build_workflow", attributes={"workflow": "agent_build_workflow"}, span_type="graph.py")
def build_workflow() -> StateGraph:
    # Define a new graph for the agent
    builder = StateGraph(GraphState)
    builder.add_node("assistant", assistant)
    builder.add_node("tools", tool_node)
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges("assistant", should_continue, ["tools", END])
    builder.add_edge("tools", "assistant")
    return builder

@mlflow.trace(name="build_app", attributes={"workflow": "agent_build_app"}, span_type="graph.py")
def build_app():
    """Build and compile the workflow."""
    workflow = build_workflow()
    return workflow.compile()

# Set are model to be leveraged via model from code
mlflow.models.set_model(build_app())