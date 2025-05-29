import os
from datetime import datetime
import sqlite3
from loguru import logger
from tools import DB_PATH, TODAY_DATE


class PromptManager:
    """
    Class responsible for loading and formatting prompt templates for the health assistant.
    Handles all prompt-related formatting and operations.
    """
    def __init__(self, override_date=None):
        """
        Initialize the PromptManager.
        
        Args:
            override_date (str, optional): Date string to override the current date for testing.
                                          Format: "Month Day, Year" (e.g., "Jun 5, 2025")
        """
        self.prompt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompt.txt")
        
        # Set the current date
        self.current_date = datetime.now().strftime("%B %d, %Y")
        if override_date:
            self.current_date = override_date
            
        logger.info(f"PromptManager initialized with date: {self.current_date}")
        
        # Load calendar information
        self.calendar_summary = self._get_calendar_summary()
        
    def _get_calendar_summary(self):
        """
        Generate a summary of the user's calendar for context.
        Includes past medical appointments and upcoming events.
        
        Returns:
            dict: A dictionary with past medical events and upcoming events
        """
        def get_past_calendar_events():
            """
            Fetch past calendar events to provide context to the agent.
            This is not registered as a tool but used internally to build agent context.
            
            Returns:
                list: A list of dictionaries containing past calendar events
            """
            try:
                current_date = TODAY_DATE.strftime("%Y-%m-%d")
                
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Query all past events (end_date earlier than current date)
                cursor.execute("""
                    SELECT * FROM personal_calendar 
                    WHERE end_date < ? 
                    ORDER BY end_date DESC
                """, (current_date,))
                
                past_events = []
                for row in cursor.fetchall():
                    event = dict(row)
                    formatted_event = {
                        "title": event["title"],
                        "start_date": event["start_date"],
                        "end_date": event["end_date"],
                        "location": event["location"] or "",
                        "details": event["details"] or "",
                        "event_type": event["event_type"]
                    }
                    
                    # Add time information for non-all-day events
                    if not event["all_day"] and event["start_time"] and event["end_time"]:
                        formatted_event["time"] = f"{event['start_time']} - {event['end_time']}"
                    
                    past_events.append(formatted_event)
                
                conn.close()
                return past_events
            except Exception as e:
                logger.error(f"Error fetching past calendar events: {str(e)}")
                return []

        def get_upcoming_calendar_events():
            """
            Fetch upcoming calendar events to provide context to the agent.
            This is not registered as a tool but used internally to build agent context.
            
            Returns:
                list: A list of dictionaries containing upcoming calendar events
            """
            try:
                current_date = TODAY_DATE.strftime("%Y-%m-%d")
                
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Query all upcoming events (start_date on or after current date)
                cursor.execute("""
                    SELECT * FROM personal_calendar 
                    WHERE start_date >= ? 
                    ORDER BY start_date ASC
                """, (current_date,))
                
                upcoming_events = []
                for row in cursor.fetchall():
                    event = dict(row)
                    formatted_event = {
                        "title": event["title"],
                        "start_date": event["start_date"],
                        "end_date": event["end_date"],
                        "location": event["location"] or "",
                        "details": event["details"] or "",
                        "event_type": event["event_type"]
                    }
                    
                    # Add time information for non-all-day events
                    if not event["all_day"] and event["start_time"] and event["end_time"]:
                        formatted_event["time"] = f"{event['start_time']} - {event['end_time']}"
                    else:
                        formatted_event["all_day"] = True
                    
                    upcoming_events.append(formatted_event)
                
                conn.close()
                return upcoming_events
            except Exception as e:
                logger.error(f"Error fetching upcoming calendar events: {str(e)}")
                return []
        
        past_events = get_past_calendar_events()
        upcoming_events = get_upcoming_calendar_events()
        
        past_medical = [event for event in past_events if event["event_type"] == "medical"]
        past_vacations = [event for event in past_events if event["event_type"] == "vacation"]
        upcoming_medical = [event for event in upcoming_events if event["event_type"] == "medical"]
        upcoming_vacations = [event for event in upcoming_events if event["event_type"] == "vacation"]
        upcoming_personal = [event for event in upcoming_events if event["event_type"] == "personal"]
        
        return {
            "past_medical_appointments": past_medical,
            "past_vacations": past_vacations,
            "upcoming_medical_appointments": upcoming_medical,
            "upcoming_vacations": upcoming_vacations,
            "upcoming_personal_events": upcoming_personal
        }
        
    def _format_date(self, date_str):
        """Format a date string to a human-readable format."""
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %d, %Y")
    
    def _format_event(self, event, include_time=True, include_date_range=False):
        """Format a single calendar event into a readable string."""
        if include_date_range:
            start_date = self._format_date(event["start_date"])
            end_date = self._format_date(event["end_date"])
            event_details = f"- {event['title']} from {start_date} to {end_date}"
        else:
            start_date = self._format_date(event["start_date"])
            event_details = f"- {event['title']} on {start_date}"
            
        if include_time and "time" in event:
            event_details += f" at {event['time']}"
            
        if event["location"]:
            event_details += f" at {event['location']}"
            
        return event_details + "\n"
    
    def format_medical_appointments(self, appointments):
        """Format a list of medical appointments into a formatted text block."""
        if not appointments:
            return ""
            
        formatted_text = ""
        for appt in appointments:
            formatted_text += self._format_event(appt, include_date_range=False)
        return formatted_text
    
    def format_vacations(self, vacations):
        """Format a list of vacation events into a formatted text block."""
        if not vacations:
            return ""
            
        formatted_text = ""
        for event in vacations:
            formatted_text += self._format_event(event, include_date_range=True)
        return formatted_text
        
    def format_personal_events(self, events):
        """Format a list of personal events into a formatted text block."""
        if not events:
            return ""
            
        formatted_text = ""
        for event in events:
            formatted_text += self._format_event(event, include_date_range=False)
        return formatted_text
    
    def create_system_instruction(self):
        """
        Create the system instruction by formatting the prompt template with calendar data.
        
        Returns:
            str: Formatted system instruction
        """
        past_medical_text = self.format_medical_appointments(self.calendar_summary["past_medical_appointments"])
        upcoming_medical_text = self.format_medical_appointments(self.calendar_summary["upcoming_medical_appointments"])
        past_vacation_text = self.format_vacations(self.calendar_summary["past_vacations"])
        upcoming_vacation_text = self.format_vacations(self.calendar_summary["upcoming_vacations"])
        upcoming_personal_text = self.format_personal_events(self.calendar_summary["upcoming_personal_events"])
        
        # Load system instruction from file
        try:
            with open(self.prompt_path, "r") as file:
                prompt_template = file.read()
                system_instruction = prompt_template.format(
                    current_date=self.current_date,
                    past_medical_text=past_medical_text,
                    upcoming_medical_text=upcoming_medical_text,
                    past_vacation_text=past_vacation_text,
                    upcoming_vacation_text=upcoming_vacation_text,
                    upcoming_personal_text=upcoming_personal_text
                )
                logger.info(f"Loaded system instruction from {self.prompt_path}")
        except FileNotFoundError:
            logger.error(f"prompt.txt file not found at {self.prompt_path}. Using default system instruction.")
            system_instruction = (
                f"You are a helpful health assistant. Today's date is {self.current_date}. "
                "You can help users understand their symptoms and book doctor appointments."
            )
            
        return system_instruction 