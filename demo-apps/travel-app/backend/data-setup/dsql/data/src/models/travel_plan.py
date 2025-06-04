"""Travel Plan data models for the Strands-based backend."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


class TravelPlanStatus(str, Enum):
    """Status of the travel planning process."""
    INITIALIZED = "initialized"
    IN_PROGRESS = "in_progress"
    PENDING_USER_INPUT = "pending_user_input"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActionType(str, Enum):
    """Available action types for the planner."""
    # Search Actions
    SEARCH_FLIGHTS = "SEARCH_FLIGHTS"
    SEARCH_HOTELS = "SEARCH_HOTELS"
    SEARCH_DESTINATIONS = "SEARCH_DESTINATIONS"
    SEARCH_ACTIVITIES = "SEARCH_ACTIVITIES"
    
    # Recommendation Actions
    RECOMMEND_DESTINATION = "RECOMMEND_DESTINATION"
    RECOMMEND_HOTELS = "RECOMMEND_HOTELS"
    RECOMMEND_FLIGHTS = "RECOMMEND_FLIGHTS"
    RECOMMEND_ACTIVITIES = "RECOMMEND_ACTIVITIES"
    
    # Budget Actions
    ANALYZE_BUDGET = "ANALYZE_BUDGET"
    SUGGEST_SAVINGS = "SUGGEST_SAVINGS"
    ADJUST_ALLOCATION = "ADJUST_ALLOCATION"
    SET_BUDGET = "SET_BUDGET"
    
    # Booking Actions
    BOOK_FLIGHT = "BOOK_FLIGHT"
    BOOK_HOTEL = "BOOK_HOTEL"
    BOOK_ACTIVITY = "BOOK_ACTIVITY"
    
    # User Interaction
    ASK_USER_CLARIFICATION = "ASK_USER_CLARIFICATION"
    ASK_USER_CONFIRMATION = "ASK_USER_CONFIRMATION"
    
    # Planning Actions
    CREATE_ITINERARY = "CREATE_ITINERARY"
    UPDATE_ITINERARY = "UPDATE_ITINERARY"
    FINALIZE_PLAN = "FINALIZE_PLAN"
    
    # Control Actions
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"


class Flight(BaseModel):
    """Flight information model."""
    flight_number: str
    airline: str
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    price: float
    cabin_class: str = "economy"
    duration_minutes: int
    stops: int = 0
    available_seats: Optional[int] = None


class Hotel(BaseModel):
    """Hotel information model."""
    hotel_id: str
    name: str
    location: str
    address: str
    star_rating: float = Field(ge=1, le=5)
    price_per_night: float
    amenities: List[str] = []
    room_type: str = "standard"
    availability: bool = True
    images: List[str] = []
    review_score: Optional[float] = Field(None, ge=0, le=10)


class Activity(BaseModel):
    """Activity information model."""
    activity_id: str
    name: str
    description: str
    location: str
    duration_hours: float
    price_per_person: float
    category: str
    available_times: List[str] = []
    min_participants: int = 1
    max_participants: Optional[int] = None


class Destination(BaseModel):
    """Destination information model."""
    destination_id: str
    name: str
    country: str
    region: Optional[str] = None
    description: str
    best_time_to_visit: List[str] = []
    average_temperature: Dict[str, float] = {}
    popular_activities: List[str] = []
    travel_warnings: List[str] = []


class Budget(BaseModel):
    """Budget breakdown model."""
    total_budget: float
    spent: float = 0
    flights: float = 0
    accommodation: float = 0
    activities: float = 0
    food: float = 0
    transport: float = 0
    miscellaneous: float = 0
    currency: str = "USD"


class UserPreferences(BaseModel):
    """User preferences for travel planning."""
    budget: Optional[float] = None
    travel_style: Optional[str] = None  # luxury, budget, mid-range
    accommodation_type: Optional[str] = None  # hotel, hostel, resort, airbnb
    activities: List[str] = []  # beach, hiking, culture, food, etc.
    dietary_restrictions: List[str] = []
    accessibility_needs: List[str] = []
    preferred_airlines: List[str] = []
    avoided_airlines: List[str] = []


class TravelPlan(BaseModel):
    """Complete travel plan model."""
    plan_id: str
    user_id: str
    status: TravelPlanStatus = TravelPlanStatus.INITIALIZED
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # User Input
    user_goal: str
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    
    # Plan Details
    destination: Optional[Destination] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    travelers_count: int = 1
    
    # Bookings
    flights: List[Flight] = []
    hotels: List[Hotel] = []
    activities: List[Activity] = []
    
    # Budget
    budget: Optional[Budget] = None
    
    # Itinerary
    itinerary: Dict[str, List[Dict[str, Any]]] = {}  # date -> list of activities
    
    # Metadata
    conversation_history: List[Dict[str, Any]] = []
    execution_metadata: Dict[str, Any] = {}
    
    def model_post_init(self, __context):
        """Post-initialization to ensure updated_at is set."""
        self.updated_at = datetime.now()


class AgentAction(BaseModel):
    """Action to be taken by an agent."""
    type: ActionType
    parameters: Dict[str, Any] = {}
    reasoning: str
    confidence: float = Field(ge=0, le=1)
    is_complete: bool = False
    requires_user_input: bool = False


class AgentResponse(BaseModel):
    """Standard response from any agent."""
    success: bool
    action_taken: Optional[AgentAction] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    state_updates: Dict[str, Any] = {}
    next_suggested_action: Optional[ActionType] = None