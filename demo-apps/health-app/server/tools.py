"""
AI Health Assistant Tools

This module contains all the function tools that the AI Health Assistant can use
to interact with external systems and provide functionality beyond conversation.

The tools include:
- Database operations for appointments and calendar management
- Health knowledge base querying via AWS Bedrock
- Appointment booking and scheduling
- Calendar conflict detection

Note: The calendar and appointment system uses a SQLite database as a mock-up
for demonstration purposes. In a production environment, this would integrate
with real calendar APIs (Google Calendar, Outlook, Apple Calendar, etc.) and
medical appointment systems. The current implementation demonstrates the conflict
detection logic and scheduling workflow using local database storage.
"""

import json
import sqlite3
import os
from datetime import datetime
from loguru import logger
import boto3  # AWS SDK for Bedrock integration

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.services.llm_service import FunctionCallParams

# Configuration constants
DB_PATH = "data/store.db"  # SQLite database path for appointments and calendar

# Date configuration for demo purposes
# In production, use: TODAY_DATE = datetime.now()
TODAY_DATE = datetime.strptime("2025-06-05", "%Y-%m-%d")  # Demo date override

# AWS Bedrock client for health knowledge base queries
BEDROCK_AGENT_RUNTIME_CLIENT = None
try:
    BEDROCK_AGENT_RUNTIME_CLIENT = boto3.client(
        service_name='bedrock-agent-runtime',
        region_name=os.getenv("AWS_REGION", "us-east-1")
    )
    logger.info("AWS Bedrock client initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Bedrock client: {e}")
    logger.warning("Health knowledge base queries will not be available")


def initialize_database():
    """
    Initialize the SQLite database with required tables.
    
    Creates two main tables:
    1. appointments: Stores available appointment slots and bookings
    2. personal_calendar: Stores user's personal calendar events for conflict detection
    
    This function is safe to call multiple times as it uses CREATE TABLE IF NOT EXISTS.
    """
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create appointments table for medical appointment slots
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id TEXT PRIMARY KEY,           -- Unique appointment slot identifier
        date TEXT NOT NULL,            -- Appointment date (YYYY-MM-DD format)
        time TEXT NOT NULL,            -- Appointment time (HH:MM AM/PM format)
        doctor TEXT NOT NULL,          -- Doctor name and specialty
        available BOOLEAN NOT NULL DEFAULT 1,  -- Availability status
        user_id TEXT DEFAULT NULL      -- User who booked the appointment (if any)
    )
    ''')
    
    # Create personal calendar table for user's existing events
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS personal_calendar (
        id TEXT PRIMARY KEY,           -- Unique event identifier
        title TEXT NOT NULL,           -- Event title/description
        start_date TEXT NOT NULL,      -- Event start date (YYYY-MM-DD)
        end_date TEXT NOT NULL,        -- Event end date (YYYY-MM-DD)
        all_day BOOLEAN DEFAULT 0,     -- Whether event is all-day
        start_time TEXT,               -- Event start time (HH:MM AM/PM)
        end_time TEXT,                 -- Event end time (HH:MM AM/PM)
        location TEXT,                 -- Event location
        details TEXT,                  -- Additional event details
        event_type TEXT NOT NULL       -- Event type: 'medical', 'personal', 'vacation'
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")


def _check_calendar_conflict(slot, calendar_events):
    """
    Check if an appointment slot conflicts with existing calendar events.
    
    Args:
        slot: Appointment slot dictionary
        calendar_events: List of calendar events
        
    Returns:
        Tuple of (has_conflict: bool, conflict_details: str or None)
    """
    slot_date = datetime.strptime(slot["date"], "%Y-%m-%d").date()
    
    for event in calendar_events:
        event_start = datetime.strptime(event["start_date"], "%Y-%m-%d").date()
        event_end = datetime.strptime(event["end_date"], "%Y-%m-%d").date()
        
        # Check if slot date falls within event date range
        if event_start <= slot_date <= event_end:
            # All-day events automatically conflict
            if event["all_day"]:
                return True, event["title"]
            
            # Check time-specific conflicts
            if event["start_time"] and event["end_time"]:
                try:
                    slot_time = datetime.strptime(slot["time"], "%I:%M %p").time()
                    event_start_time = datetime.strptime(event["start_time"], "%I:%M %p").time()
                    event_end_time = datetime.strptime(event["end_time"], "%I:%M %p").time()
                    
                    # Check for time overlap
                    if event_start_time <= slot_time <= event_end_time:
                        return True, event["title"]
                except ValueError as e:
                    logger.warning(f"Error parsing time for conflict check: {e}")
                    continue
    
    return False, None


def _get_recommended_slots(cursor, available_slots):
    """
    Generate appointment recommendations based on past medical appointments.
    
    Args:
        cursor: Database cursor
        available_slots: List of available appointment slots
        
    Returns:
        List of recommended slots with reasoning
    """
    # Get past medical appointments for recommendations
    cursor.execute("""
        SELECT * FROM personal_calendar 
        WHERE event_type = 'medical' 
        ORDER BY start_date DESC
    """)
    past_appointments = [dict(row) for row in cursor.fetchall()]
    
    recommended_slots = []
    
    for past_appt in past_appointments:
        # Extract doctor information from past appointments
        doctor_name = None
        if "Dr." in past_appt["title"] and "with " in past_appt["title"]:
            doctor_name = past_appt["title"].split("with ")[1]
        
        # Find matching available slots with the same doctor
        if doctor_name:
            for slot in available_slots:
                if doctor_name in slot["doctor"] and slot not in recommended_slots:
                    recommended_slots.append({
                        **slot,
                        "recommended": True,
                        "reason": f"Previous appointment with {doctor_name}"
                    })
                    break  # Only recommend one slot per doctor
    
    return recommended_slots

async def book_appointment(params: FunctionCallParams):
    """
    Book an appointment in the selected slot.
    
    This function:
    1. Validates that the requested slot exists and is available
    2. Updates the database to mark the slot as booked
    3. Returns confirmation details of the booked appointment
    
    Args:
        params: Function call parameters containing:
            - slot_id: The ID of the appointment slot to book
            - symptoms_summary: Optional summary of symptoms (for context)
            - user_id: Optional user identifier (defaults to "demo_user")
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating if booking was successful
        - appointment: Details of the booked appointment (if successful)
        - error: Error message (if unsuccessful)
    """
    try:
        slot_id = params.arguments["slot_id"]
        # In a production system, this would come from user authentication
        user_id = params.arguments.get("user_id", "demo_user")
        symptoms_summary = params.arguments.get("symptoms_summary", {})
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verify slot exists and is available
        cursor.execute("SELECT * FROM appointments WHERE id = ? AND available = 1", (slot_id,))
        slot = cursor.fetchone()
        
        if not slot:
            conn.close()
            logger.warning(f"Booking attempt failed: Slot {slot_id} not found or unavailable")
            await params.result_callback({
                "success": False, 
                "error": "This appointment slot is not available or doesn't exist."
            })
            return
        
        # Book the appointment by updating availability and assigning user
        cursor.execute(
            "UPDATE appointments SET available = 0, user_id = ? WHERE id = ?", 
            (user_id, slot_id)
        )
        conn.commit()
        
        # Prepare booking confirmation details
        booked_appointment = {
            "slot_id": slot[0],      # Appointment ID
            "date": slot[1],         # Appointment date
            "time": slot[2],         # Appointment time
            "doctor": slot[3],       # Doctor name and specialty
            "user_id": user_id,
            "symptoms_summary": symptoms_summary,
            "booking_timestamp": TODAY_DATE.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "confirmed"
        }
        
        conn.close()
        
        logger.info(f"Appointment booked successfully: {slot_id} for user {user_id}")
        await params.result_callback({
            "success": True,
            "message": "Appointment booked successfully!",
            "appointment": booked_appointment
        })
        
    except KeyError as e:
        logger.error(f"Missing required parameter for booking: {e}")
        await params.result_callback({
            "success": False, 
            "error": f"Missing required parameter: {e}"
        })
    except Exception as e:
        logger.error(f"Error booking appointment: {str(e)}")
        await params.result_callback({
            "success": False, 
            "error": "An error occurred while booking the appointment. Please try again."
        })


async def get_non_clashing_slots(params: FunctionCallParams):
    """
    Get available appointment slots that don't conflict with personal calendar events.
    
    This function queries the database for available appointment slots and filters out
    any that would clash with existing personal calendar events. It handles both
    all-day events and timed events, ensuring no scheduling conflicts.
    
    Note: This implementation uses a local SQLite database to mock calendar events.
    In production, this would integrate with real calendar APIs (Google Calendar,
    Outlook, etc.) to fetch actual user calendar data.
    
    Args:
        params: Function call parameters containing:
            - doctor_name: Name or partial name of the doctor (required)
            - unavailable_date: Optional date in YYYY-MM-DD format to exclude
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating if the query was successful
        - non_clashing_slots: List of available appointment slots
        - error: Error message (if unsuccessful)
    
    Note:
        Uses complex SQL logic to handle time format conversion and overlap detection
        between appointment slots and personal calendar events.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get doctor name from params if provided
        doctor_name = params.arguments.get("doctor_name", None)
        # Get unavailable date if customer mentioned it
        unavailable_date = params.arguments.get("unavailable_date", None)

        if not doctor_name:
            logger.warning("get_non_clashing_slots called without doctor_name")
            await params.result_callback({
                "success": False,
                "error": "Doctor name is required to find available slots"
            })
            return
        
        logger.info(f"Finding non-clashing slots for doctor: {doctor_name}")
        
        # Base query to find available appointments
        query = """
        SELECT a.id, a.date, a.time, a.doctor, a.available
        FROM appointments a
        WHERE a.available = 1
        """
        
        # Add doctor filter
        query += f" AND a.doctor LIKE ?"
        query_params = [f"%{doctor_name}%"]
        
        # Add unavailable date filter if provided
        if unavailable_date:
            query += " AND a.date != ?"
            query_params.append(unavailable_date)
            logger.info(f"Excluding unavailable date: {unavailable_date}")
            
        # Add calendar clash filter - complex SQL to handle time overlaps
        query += """
        AND NOT EXISTS (
            SELECT 1 FROM personal_calendar pc
            WHERE 
                -- Check date overlap for all events
                (pc.start_date <= a.date AND pc.end_date >= a.date)
                AND (
                    -- For all-day events, any time on that date clashes
                    pc.all_day = 1
                    OR 
                    -- For timed events, check time overlap
                    (
                        pc.all_day = 0 
                        AND pc.start_time IS NOT NULL 
                        AND pc.end_time IS NOT NULL
                        AND time(substr(a.time, 1, instr(a.time, ' ')-1) || ':00' || 
                            CASE WHEN substr(a.time, instr(a.time, ' ')+1) = 'PM' AND substr(a.time, 1, 2) != '12' 
                                THEN '+12 hours' 
                                WHEN substr(a.time, instr(a.time, ' ')+1) = 'AM' AND substr(a.time, 1, 2) = '12' 
                                THEN '-12 hours' 
                                ELSE '' 
                            END) 
                        BETWEEN 
                            time(substr(pc.start_time, 1, instr(pc.start_time, ' ')-1) || ':00' || 
                                CASE WHEN substr(pc.start_time, instr(pc.start_time, ' ')+1) = 'PM' AND substr(pc.start_time, 1, 2) != '12' 
                                    THEN '+12 hours' 
                                    WHEN substr(pc.start_time, instr(pc.start_time, ' ')+1) = 'AM' AND substr(pc.start_time, 1, 2) = '12' 
                                    THEN '-12 hours' 
                                    ELSE '' 
                                END)
                        AND 
                            time(substr(pc.end_time, 1, instr(pc.end_time, ' ')-1) || ':00' || 
                                CASE WHEN substr(pc.end_time, instr(pc.end_time, ' ')+1) = 'PM' AND substr(pc.end_time, 1, 2) != '12' 
                                    THEN '+12 hours' 
                                    WHEN substr(pc.end_time, instr(pc.end_time, ' ')+1) = 'AM' AND substr(pc.end_time, 1, 2) = '12' 
                                    THEN '-12 hours' 
                                    ELSE '' 
                                END)
                    )
                )
        )
        ORDER BY a.date, a.time
        """
        
        cursor.execute(query, tuple(query_params))
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        non_clashing_slots = []
        for row in rows:
            non_clashing_slots.append({
                "id": row["id"],
                "date": row["date"],
                "time": row["time"],
                "doctor": row["doctor"],
                "available": bool(row["available"])
            })
        
        conn.close()
        
        logger.info(f"Found {len(non_clashing_slots)} non-clashing slots for {doctor_name}")
        await params.result_callback({
            "success": True,
            "non_clashing_slots": non_clashing_slots,
            "doctor_searched": doctor_name
        })
        
    except Exception as e:
        logger.error(f"Error getting non-clashing slots: {str(e)}")
        await params.result_callback({
            "success": False, 
            "error": "Unable to retrieve available appointment slots at this time"
        })


async def get_all_doctors(params: FunctionCallParams):
    """
    Retrieve a list of all doctors available for appointments.
    
    This function queries the appointments database to get a unique list of all
    doctors who have appointment slots available. This is useful for showing
    users what doctors they can book appointments with.
    
    Args:
        params: Function call parameters (no arguments required)
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating if the query was successful
        - doctors: List of doctor names
        - error: Error message (if unsuccessful)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        logger.info("Retrieving list of all available doctors")
        
        # Query for unique doctor names from appointments table
        cursor.execute("SELECT DISTINCT doctor FROM appointments ORDER BY doctor")
        rows = cursor.fetchall()
        
        # Convert to list
        doctors = [row["doctor"] for row in rows]
        
        conn.close()
        
        logger.info(f"Found {len(doctors)} doctors available for appointments")
        await params.result_callback({
            "success": True,
            "doctors": doctors,
            "count": len(doctors)
        })
        
    except Exception as e:
        logger.error(f"Error getting doctors list: {str(e)}")
        await params.result_callback({
            "success": False, 
            "error": "Unable to retrieve doctors list at this time"
        })

async def query_health_kb(params: FunctionCallParams):
    """
    Query the AWS Bedrock Knowledge Base for health-related information.
    
    This function searches a curated health knowledge base to provide accurate
    information about symptoms, conditions, treatments, and general health topics.
    The knowledge base contains medical information that can help users understand
    their symptoms and provide context for their health concerns.
    
    Args:
        params: Function call parameters containing:
            - query_text: The health question or symptom description to search for
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating if the query was successful
        - retrieved_chunks: List of relevant text chunks from the knowledge base
        - error: Error message (if unsuccessful)
    
    Note:
        Requires AWS Bedrock Knowledge Base to be configured with AMAZON_BEDROCK_KB_ID
        environment variable. The knowledge base should contain medical/health content.
    """
    try:
        query_text = params.arguments.get("query_text")
        if not query_text:
            logger.warning("Health KB query attempted without query text")
            await params.result_callback({
                "success": False, 
                "error": "Please provide a health question or symptom description to search for."
            })
            return

        if not BEDROCK_AGENT_RUNTIME_CLIENT:
            logger.error("Bedrock client not available for health KB query")
            await params.result_callback({
                "success": False, 
                "error": "Health knowledge base is currently unavailable."
            })
            return

        knowledge_base_id = os.getenv("AMAZON_BEDROCK_KB_ID")
        if not knowledge_base_id:
            logger.error("AMAZON_BEDROCK_KB_ID environment variable not set")
            await params.result_callback({
                "success": False, 
                "error": "Health knowledge base is not configured."
            })
            return

        logger.info(f"Querying health knowledge base for: {query_text}")
        
        # Query the Bedrock Knowledge Base
        response = BEDROCK_AGENT_RUNTIME_CLIENT.retrieve(
            knowledgeBaseId=knowledge_base_id,
            retrievalQuery={
                'text': query_text
            },
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 3  # Retrieve top 3 most relevant results
                }
            }
        )
        
        # Extract relevant text chunks from the response
        retrieved_chunks = []
        if 'retrievalResults' in response:
            for result in response['retrievalResults']:
                if 'content' in result and 'text' in result['content']:
                    retrieved_chunks.append(result['content']['text'])
        
        if retrieved_chunks:
            logger.info(f"Successfully retrieved {len(retrieved_chunks)} relevant health information chunks")
            await params.result_callback({
                "success": True, 
                "retrieved_chunks": retrieved_chunks,
                "query": query_text
            })
        else:
            logger.info(f"No relevant health information found for query: {query_text}")
            await params.result_callback({
                "success": True, 
                "retrieved_chunks": [],
                "message": "No specific information found for your query. Please try rephrasing your question."
            })

    except Exception as e:
        logger.error(f"Error querying health knowledge base: {str(e)}")
        await params.result_callback({
            "success": False, 
            "error": "Unable to search health knowledge base at this time. Please try again later."
        })


# Tool Schema Definitions
# These schemas define the available functions that the AI can call

book_appointment_tool = FunctionSchema(
    name="book_appointment",
    description="Book a doctor appointment in the selected time slot.",
    properties={
        "slot_id": {
            "type": "string",
            "description": "The ID of the selected appointment slot."
        },
        "symptoms_summary": {
            "type": "object",
            "description": "A structured summary of the user's symptoms to include with the appointment booking.",
            "properties": {
                "symptoms": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "symptom": {"type": "string", "description": "The name of the symptom"},
                            "duration": {"type": "string", "description": "How long the symptom has been present"},
                            "intensity": {"type": "string", "description": "The severity or intensity of the symptom"}
                        }
                    }
                },
                "additional_notes": {"type": "string", "description": "Any additional notes about the symptoms or condition"}
            }
        }
    },
    required=["slot_id"]
)

query_health_kb_schema = FunctionSchema(
    name="query_health_kb",
    description="Search the health knowledge base for information about symptoms, conditions, treatments, or general health topics. Use this to provide accurate medical information to users.",
    properties={
        "query_text": {
            "type": "string",
            "description": "The health question, symptom description, or medical topic to search for. Examples: 'persistent cough treatment', 'symptoms of strep throat', 'when to see a doctor for headaches'",
        },
    },
    required=["query_text"],
)

get_non_clashing_slots_tool = FunctionSchema(
    name="get_non_clashing_slots",
    description="Get available appointment slots that don't conflict with the user's personal calendar events. Filters out appointments that would clash with existing commitments.",
    properties={
        "doctor_name": {
            "type": "string",
            "description": "Name or partial name of the doctor to find appointments for. Will match doctors whose names contain this text."
        },
        "unavailable_date": {
            "type": "string",
            "description": "Optional date in YYYY-MM-DD format when the user is not available. Slots on this date will be excluded from results."
        }
    },
    required=["doctor_name"]
)

get_all_doctors_tool = FunctionSchema(
    name="get_all_doctors",
    description="Retrieve a list of all doctors available for appointments, including their specialties and available time slots.",
    properties={},
    required=[]
)

# Tools Schema - defines which functions are available to the AI
tools_schema = ToolsSchema(
    standard_tools=[
        # Core appointment booking functionality
        book_appointment_tool,
        get_non_clashing_slots_tool,
        get_all_doctors_tool,
        
        # Health information lookup
        query_health_kb_schema,
    ]
)