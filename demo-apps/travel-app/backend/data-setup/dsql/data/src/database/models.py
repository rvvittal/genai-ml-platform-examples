"""Database models for travel planning demo."""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, date, time
import json


@dataclass
class City:
    code: str
    name: str
    country: str
    continent: str
    timezone: str
    latitude: float
    longitude: float
    description: str
    tags: List[str]
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'country': self.country,
            'continent': self.continent,
            'timezone': self.timezone,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'description': self.description,
            'tags': self.tags
        }


@dataclass
class Airline:
    code: str
    name: str
    hub_cities: List[str]
    id: Optional[int] = None


@dataclass
class FlightRoute:
    origin_code: str
    destination_code: str
    airlines: List[str]
    flight_duration_minutes: int
    distance_km: int
    typical_aircraft: List[str]
    id: Optional[int] = None


@dataclass
class Flight:
    flight_number: str
    airline_code: str
    origin_code: str
    destination_code: str
    departure_date: date
    departure_time: time
    arrival_date: date
    arrival_time: time
    duration_minutes: int
    aircraft_type: str
    economy_seats_available: int
    economy_price: float
    business_seats_available: int
    business_price: float
    first_seats_available: int
    first_price: float
    status: str = 'scheduled'
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'flight_number': self.flight_number,
            'airline_code': self.airline_code,
            'origin_code': self.origin_code,
            'destination_code': self.destination_code,
            'departure_date': self.departure_date.isoformat() if isinstance(self.departure_date, date) else self.departure_date,
            'departure_time': self.departure_time.isoformat() if isinstance(self.departure_time, time) else self.departure_time,
            'arrival_date': self.arrival_date.isoformat() if isinstance(self.arrival_date, date) else self.arrival_date,
            'arrival_time': self.arrival_time.isoformat() if isinstance(self.arrival_time, time) else self.arrival_time,
            'duration_minutes': self.duration_minutes,
            'aircraft_type': self.aircraft_type,
            'economy_seats_available': self.economy_seats_available,
            'economy_price': self.economy_price,
            'business_seats_available': self.business_seats_available,
            'business_price': self.business_price,
            'first_seats_available': self.first_seats_available,
            'first_price': self.first_price,
            'status': self.status
        }


@dataclass
class Hotel:
    name: str
    city_code: str
    address: str
    latitude: float
    longitude: float
    star_rating: int
    hotel_type: str
    amenities: List[str]
    room_types: List[str]
    description: str
    neighborhood_description: str
    tags: List[str]
    base_price_min: float
    base_price_max: float
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'city_code': self.city_code,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'star_rating': self.star_rating,
            'hotel_type': self.hotel_type,
            'amenities': self.amenities,
            'room_types': self.room_types,
            'description': self.description,
            'neighborhood_description': self.neighborhood_description,
            'tags': self.tags,
            'base_price_min': self.base_price_min,
            'base_price_max': self.base_price_max
        }


@dataclass
class HotelAvailability:
    hotel_id: int
    date: date
    standard_rooms_available: int
    standard_room_price: float
    deluxe_rooms_available: int
    deluxe_room_price: float
    suite_rooms_available: int
    suite_room_price: float
    occupancy_rate: float
    id: Optional[int] = None


@dataclass
class Activity:
    name: str
    city_code: str
    category: str
    description: str
    duration_hours: float
    price_adult: float
    price_child: float
    tags: List[str]
    includes: List[str]
    available_days: List[str]
    time_slots: List[str]
    meeting_point: str
    latitude: float
    longitude: float
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'city_code': self.city_code,
            'category': self.category,
            'description': self.description,
            'duration_hours': self.duration_hours,
            'price_adult': self.price_adult,
            'price_child': self.price_child,
            'tags': self.tags,
            'includes': self.includes,
            'available_days': self.available_days,
            'time_slots': self.time_slots,
            'meeting_point': self.meeting_point,
            'latitude': self.latitude,
            'longitude': self.longitude
        }