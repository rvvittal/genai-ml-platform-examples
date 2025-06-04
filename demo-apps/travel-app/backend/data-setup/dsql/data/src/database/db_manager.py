"""Database manager for travel planning demo."""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_path: str = "travel_demo.db"):
        self.db_path = db_path
        self.conn = None
        
    def __enter__(self):
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        
    def connect(self):
        """Connect to the database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            
    def init_database(self):
        """Initialize the database with schema."""
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, 'r') as f:
            schema = f.read()
            
        self.conn.executescript(schema)
        self.conn.commit()
        logger.info("Database initialized successfully")
        
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a query and return results as list of dicts."""
        cursor = self.conn.execute(query, params)
        columns = [col[0] for col in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results
        
    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """Execute an insert query and return the last row id."""
        cursor = self.conn.execute(query, params)
        self.conn.commit()
        return cursor.lastrowid
        
    def execute_many(self, query: str, params_list: List[tuple]):
        """Execute many insert/update queries."""
        self.conn.executemany(query, params_list)
        self.conn.commit()
        
    # City operations
    def insert_city(self, city_data: Dict[str, Any]) -> int:
        """Insert a city into the database."""
        query = """
        INSERT INTO cities (code, name, country, continent, timezone, 
                          latitude, longitude, description, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            city_data['code'],
            city_data['name'],
            city_data['country'],
            city_data['continent'],
            city_data['timezone'],
            city_data['latitude'],
            city_data['longitude'],
            city_data['description'],
            json.dumps(city_data['tags'])
        )
        return self.execute_insert(query, params)
        
    def get_city_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Get a city by its IATA code."""
        query = "SELECT * FROM cities WHERE code = ?"
        results = self.execute_query(query, (code,))
        if results:
            city = results[0]
            city['tags'] = json.loads(city['tags'])
            return city
        return None
        
    # Airline operations
    def insert_airline(self, airline_data: Dict[str, Any]) -> int:
        """Insert an airline into the database."""
        query = """
        INSERT INTO airlines (code, name, hub_cities)
        VALUES (?, ?, ?)
        """
        params = (
            airline_data['code'],
            airline_data['name'],
            json.dumps(airline_data['hub_cities'])
        )
        return self.execute_insert(query, params)
        
    # Flight operations
    def insert_flight_route(self, route_data: Dict[str, Any]) -> int:
        """Insert a flight route."""
        query = """
        INSERT INTO flight_routes (origin_code, destination_code, airlines,
                                 flight_duration_minutes, distance_km, typical_aircraft)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (
            route_data['origin_code'],
            route_data['destination_code'],
            json.dumps(route_data['airlines']),
            route_data['flight_duration_minutes'],
            route_data['distance_km'],
            json.dumps(route_data['typical_aircraft'])
        )
        return self.execute_insert(query, params)
        
    def insert_flights_batch(self, flights: List[Dict[str, Any]]):
        """Insert multiple flights in batch."""
        query = """
        INSERT INTO flights (flight_number, airline_code, origin_code, destination_code,
                           departure_date, departure_time, arrival_date, arrival_time,
                           duration_minutes, aircraft_type, economy_seats_available,
                           economy_price, business_seats_available, business_price,
                           first_seats_available, first_price, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params_list = []
        for flight in flights:
            params = (
                flight['flight_number'],
                flight['airline_code'],
                flight['origin_code'],
                flight['destination_code'],
                flight['departure_date'],
                flight['departure_time'],
                flight['arrival_date'],
                flight['arrival_time'],
                flight['duration_minutes'],
                flight['aircraft_type'],
                flight['economy_seats_available'],
                flight['economy_price'],
                flight['business_seats_available'],
                flight['business_price'],
                flight['first_seats_available'],
                flight['first_price'],
                flight['status']
            )
            params_list.append(params)
        self.execute_many(query, params_list)
        
    def search_flights(self, origin: str, destination: str, departure_date: str,
                      cabin_class: str = 'economy', passengers: int = 1) -> List[Dict[str, Any]]:
        """Search for flights."""
        query = f"""
        SELECT f.*, a.name as airline_name, 
               c1.name as origin_city, c2.name as destination_city
        FROM flights f
        JOIN airlines a ON f.airline_code = a.code
        JOIN cities c1 ON f.origin_code = c1.code
        JOIN cities c2 ON f.destination_code = c2.code
        WHERE f.origin_code = ? 
          AND f.destination_code = ?
          AND f.departure_date = ?
          AND f.{cabin_class}_seats_available >= ?
          AND f.status = 'scheduled'
        ORDER BY f.departure_time
        """
        return self.execute_query(query, (origin, destination, departure_date, passengers))
        
    # Hotel operations
    def insert_hotel(self, hotel_data: Dict[str, Any]) -> int:
        """Insert a hotel."""
        query = """
        INSERT INTO hotels (name, city_code, address, latitude, longitude,
                          star_rating, hotel_type, amenities, room_types,
                          description, neighborhood_description, tags,
                          base_price_min, base_price_max)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            hotel_data['name'],
            hotel_data['city_code'],
            hotel_data['address'],
            hotel_data['latitude'],
            hotel_data['longitude'],
            hotel_data['star_rating'],
            hotel_data['hotel_type'],
            json.dumps(hotel_data['amenities']),
            json.dumps(hotel_data['room_types']),
            hotel_data['description'],
            hotel_data['neighborhood_description'],
            json.dumps(hotel_data['tags']),
            hotel_data['base_price_min'],
            hotel_data['base_price_max']
        )
        return self.execute_insert(query, params)
        
    def insert_hotel_availability_batch(self, availability_data: List[Dict[str, Any]]):
        """Insert hotel availability data in batch."""
        query = """
        INSERT INTO hotel_availability (hotel_id, date, standard_rooms_available,
                                      standard_room_price, deluxe_rooms_available,
                                      deluxe_room_price, suite_rooms_available,
                                      suite_room_price, occupancy_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params_list = []
        for avail in availability_data:
            params = (
                avail['hotel_id'],
                avail['date'],
                avail['standard_rooms_available'],
                avail['standard_room_price'],
                avail['deluxe_rooms_available'],
                avail['deluxe_room_price'],
                avail['suite_rooms_available'],
                avail['suite_room_price'],
                avail['occupancy_rate']
            )
            params_list.append(params)
        self.execute_many(query, params_list)
        
    def search_hotels(self, city_code: str, check_in: str, check_out: str,
                     star_rating: Optional[List[int]] = None,
                     hotel_type: Optional[str] = None,
                     max_price: Optional[float] = None) -> List[Dict[str, Any]]:
        """Search for hotels with availability."""
        query = """
        SELECT DISTINCT h.*, 
               MIN(ha.standard_room_price) as min_price,
               MAX(ha.suite_room_price) as max_price,
               AVG(ha.occupancy_rate) as avg_occupancy
        FROM hotels h
        JOIN hotel_availability ha ON h.id = ha.hotel_id
        WHERE h.city_code = ?
          AND ha.date >= ? AND ha.date < ?
          AND (ha.standard_rooms_available > 0 
               OR ha.deluxe_rooms_available > 0 
               OR ha.suite_rooms_available > 0)
        """
        params = [city_code, check_in, check_out]
        
        if star_rating:
            placeholders = ','.join('?' * len(star_rating))
            query += f" AND h.star_rating IN ({placeholders})"
            params.extend(star_rating)
            
        if hotel_type:
            query += " AND h.hotel_type = ?"
            params.append(hotel_type)
            
        if max_price:
            query += " AND ha.standard_room_price <= ?"
            params.append(max_price)
            
        query += " GROUP BY h.id ORDER BY h.star_rating DESC, min_price"
        
        results = self.execute_query(query, tuple(params))
        
        # Parse JSON fields
        for hotel in results:
            hotel['amenities'] = json.loads(hotel['amenities'])
            hotel['room_types'] = json.loads(hotel['room_types'])
            hotel['tags'] = json.loads(hotel['tags'])
            
        return results
        
    # Activity operations
    def insert_activity(self, activity_data: Dict[str, Any]) -> int:
        """Insert an activity."""
        query = """
        INSERT INTO activities (name, city_code, category, description,
                              duration_hours, price_adult, price_child,
                              tags, includes, available_days, time_slots,
                              meeting_point, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            activity_data['name'],
            activity_data['city_code'],
            activity_data['category'],
            activity_data['description'],
            activity_data['duration_hours'],
            activity_data['price_adult'],
            activity_data['price_child'],
            json.dumps(activity_data['tags']),
            json.dumps(activity_data['includes']),
            json.dumps(activity_data['available_days']),
            json.dumps(activity_data['time_slots']),
            activity_data['meeting_point'],
            activity_data['latitude'],
            activity_data['longitude']
        )
        return self.execute_insert(query, params)
        
    def search_activities(self, city_code: str, category: Optional[str] = None,
                         tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search for activities."""
        query = "SELECT * FROM activities WHERE city_code = ?"
        params = [city_code]
        
        if category:
            query += " AND category = ?"
            params.append(category)
            
        results = self.execute_query(query, tuple(params))
        
        # Parse JSON fields and filter by tags if provided
        filtered_results = []
        for activity in results:
            activity['tags'] = json.loads(activity['tags'])
            activity['includes'] = json.loads(activity['includes'])
            activity['available_days'] = json.loads(activity['available_days'])
            activity['time_slots'] = json.loads(activity['time_slots'])
            
            if tags:
                if any(tag in activity['tags'] for tag in tags):
                    filtered_results.append(activity)
            else:
                filtered_results.append(activity)
                
        return filtered_results