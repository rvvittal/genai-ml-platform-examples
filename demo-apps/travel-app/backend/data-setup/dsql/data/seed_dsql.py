#!/usr/bin/env python3
"""
Seed DSQL with comprehensive travel planning data.
This seeds base data (cities, airlines, hotels, activities, flight routes) 
and automatically generates flights and hotel availability data.
"""

import sys
import os
# Add parent directory to path to find the database modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
import random
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Tuple
from src.database.hybrid_adapter import DatabaseManager
import logging
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DSQLSeeder:
    """Seed DSQL with travel planning data matching SQLite structure."""
    
    def __init__(self):
        # Force DSQL usage
        self.db = DatabaseManager(use_dsql=True)
        
        # ID counters for tables without sequences
        self.hotel_id_counter = 1
        self.room_id_counter = 1
        self.availability_id_counter = 1
        self.activity_id_counter = 1
        self.route_id_counter = 1
        self.flight_id_counter = 1
        self.plan_id_counter = 1
        self.booking_id_counter = 1
    
    # Demo cities configuration (from SQLite data_generator.py)
    DEMO_CITIES = [
        {
            'code': 'NYC',
            'name': 'New York',
            'country': 'United States',
            'continent': 'North America',
            'timezone': 'America/New_York',
            'latitude': 40.7128,
            'longitude': -74.0060,
            'description': 'The city that never sleeps, known for its iconic skyline, Broadway shows, world-class museums, and diverse culinary scene.',
            'tags': ['urban', 'cultural', 'business', 'shopping', 'nightlife', 'broadway']
        },
        {
            'code': 'GIG',
            'name': 'Rio de Janeiro',
            'country': 'Brazil',
            'continent': 'South America',
            'timezone': 'America/Sao_Paulo',
            'latitude': -22.9068,
            'longitude': -43.1729,
            'description': 'Cidade Maravilhosa with stunning beaches, Christ the Redeemer, vibrant carnival culture, and breathtaking mountain views.',
            'tags': ['beach', 'cultural', 'party', 'nature', 'adventure', 'carnival']
        },
        {
            'code': 'CDG',
            'name': 'Paris',
            'country': 'France',
            'continent': 'Europe',
            'timezone': 'Europe/Paris',
            'latitude': 48.8566,
            'longitude': 2.3522,
            'description': 'The City of Light, renowned for romance, art, fashion, gastronomy, and iconic landmarks like the Eiffel Tower and Louvre.',
            'tags': ['romantic', 'cultural', 'art', 'gourmet', 'fashion', 'historic']
        },
        {
            'code': 'CPT',
            'name': 'Cape Town',
            'country': 'South Africa',
            'continent': 'Africa',
            'timezone': 'Africa/Johannesburg',
            'latitude': -33.9249,
            'longitude': 18.4241,
            'description': 'Mother City featuring Table Mountain, pristine beaches, wine regions, and a perfect blend of natural beauty and urban sophistication.',
            'tags': ['nature', 'beach', 'wine', 'adventure', 'scenic', 'wildlife']
        },
        {
            'code': 'NRT',
            'name': 'Tokyo',
            'country': 'Japan',
            'continent': 'Asia',
            'timezone': 'Asia/Tokyo',
            'latitude': 35.6762,
            'longitude': 139.6503,
            'description': 'A fascinating blend of ancient traditions and cutting-edge technology, offering temples, gardens, cuisine, and neon-lit streets.',
            'tags': ['cultural', 'technology', 'gourmet', 'shopping', 'traditional', 'modern']
        },
        {
            'code': 'SYD',
            'name': 'Sydney',
            'country': 'Australia',            'continent': 'Oceania',
            'timezone': 'Australia/Sydney',
            'latitude': -33.8688,
            'longitude': 151.2093,
            'description': 'Harbor city famous for its Opera House, Harbour Bridge, beautiful beaches, and laid-back lifestyle.',
            'tags': ['beach', 'urban', 'nature', 'harbor', 'outdoor', 'cosmopolitan']
        },
        {
            'code': 'DPS',
            'name': 'Bali (Denpasar)',
            'country': 'Indonesia',
            'continent': 'Asia',
            'timezone': 'Asia/Makassar',
            'latitude': -8.6500,
            'longitude': 115.2167,
            'description': 'Island paradise known for stunning beaches, ancient temples, terraced rice fields, and spiritual culture.',
            'tags': ['beach', 'spiritual', 'romantic', 'nature', 'cultural', 'tropical']
        }
    ]
    
    # Airlines configuration
    AIRLINES = [
        {'code': 'AA', 'name': 'American Airlines', 'hub_cities': ['NYC', 'DFW', 'MIA']},
        {'code': 'UA', 'name': 'United Airlines', 'hub_cities': ['NYC', 'SFO', 'ORD']},
        {'code': 'DL', 'name': 'Delta Air Lines', 'hub_cities': ['NYC', 'ATL', 'LAX']},
        {'code': 'AF', 'name': 'Air France', 'hub_cities': ['CDG', 'ORY']},
        {'code': 'BA', 'name': 'British Airways', 'hub_cities': ['LHR', 'LGW']},
        {'code': 'LH', 'name': 'Lufthansa', 'hub_cities': ['FRA', 'MUC']},
        {'code': 'JL', 'name': 'Japan Airlines', 'hub_cities': ['NRT', 'HND']},
        {'code': 'NH', 'name': 'All Nippon Airways', 'hub_cities': ['NRT', 'HND']},
        {'code': 'QF', 'name': 'Qantas', 'hub_cities': ['SYD', 'MEL']},
        {'code': 'SA', 'name': 'South African Airways', 'hub_cities': ['JNB', 'CPT']},
        {'code': 'GA', 'name': 'Garuda Indonesia', 'hub_cities': ['CGK', 'DPS']},
        {'code': 'LA', 'name': 'LATAM Airlines', 'hub_cities': ['GRU', 'SCL', 'GIG']}
    ]
    
    # Aircraft types by route distance
    AIRCRAFT_TYPES = {
        'short': ['A320', 'B737', 'A319', 'E190'],
        'medium': ['A321', 'B737-900', 'A320neo', 'B757'],
        'long': ['A350', 'B787', 'A330', 'B777', 'A380']
    }
    
    def clear_existing_data(self):
        """Clear existing data from tables."""
        logger.info("Clearing existing data...")
        tables = ['bookings', 'travel_plans', 'hotel_availability', 'hotel_rooms', 
                 'activities', 'hotels', 'flights', 'flight_routes', 'airlines', 'cities']
        
        for table in tables:
            try:
                self.db.adapter.execute_query(f"DELETE FROM {table}")
                logger.info(f"Cleared {table}")
            except Exception as e:
                logger.warning(f"Could not clear {table}: {e}")
    
    def seed_cities(self):
        """Seed cities data."""
        logger.info("Seeding cities...")
        
        # Build batch insert
        values_list = []
        params_list = []
        
        for city in self.DEMO_CITIES:
            values_list.append("(%s, %s, %s, %s, %s, %s, %s, %s, %s)")
            params_list.extend([
                city['code'], city['name'], city['country'], city['continent'],
                city['timezone'], city['latitude'], city['longitude'],
                city['description'], json.dumps(city['tags'])
            ])
        
        query = f"""
            INSERT INTO cities (code, name, country, continent, timezone, 
                              latitude, longitude, description, tags)
            VALUES {', '.join(values_list)}
        """
        self.db.adapter.execute_query(query, tuple(params_list))
        
        logger.info(f"Seeded {len(self.DEMO_CITIES)} cities")
    
    def seed_airlines(self):
        """Seed airlines data."""
        logger.info("Seeding airlines...")
        
        # Build batch insert
        values_list = []
        params_list = []
        
        for airline in self.AIRLINES:
            values_list.append("(%s, %s, %s)")
            params_list.extend([airline['code'], airline['name'], json.dumps(airline['hub_cities'])])
        
        query = f"""
            INSERT INTO airlines (code, name, hub_cities)
            VALUES {', '.join(values_list)}
        """
        self.db.adapter.execute_query(query, tuple(params_list))
        
        logger.info(f"Seeded {len(self.AIRLINES)} airlines")
    
    def seed_flight_routes(self):
        """Seed flight routes between cities."""
        logger.info("Seeding flight routes...")
        
        city_codes = [c['code'] for c in self.DEMO_CITIES]
        
        # Build batch insert
        values_list = []
        params_list = []
        route_count = 0
        
        for i, origin in enumerate(city_codes):
            for j, destination in enumerate(city_codes):
                if i != j:  # No routes to same city
                    # Calculate approximate flight duration based on coordinates
                    origin_city = self.DEMO_CITIES[i]
                    dest_city = self.DEMO_CITIES[j]
                    distance = self._calculate_distance(
                        origin_city['latitude'], origin_city['longitude'],
                        dest_city['latitude'], dest_city['longitude']
                    )
                    
                    # Estimate flight time (roughly 500km/h average speed + 45min overhead)
                    flight_duration = int((distance / 500) * 60 + 45)
                    
                    # Determine aircraft types based on distance
                    if distance < 2000:
                        aircraft_types = self.AIRCRAFT_TYPES['short']
                    elif distance < 5000:
                        aircraft_types = self.AIRCRAFT_TYPES['medium']
                    else:
                        aircraft_types = self.AIRCRAFT_TYPES['long']
                    
                    # Select airlines that could fly this route
                    route_airlines = self._select_airlines_for_route(origin, destination)
                    
                    values_list.append("(%s, %s, %s, %s, %s, %s, %s)")
                    params_list.extend([
                        self.route_id_counter, origin, destination, json.dumps(route_airlines),
                        flight_duration, int(distance), json.dumps(aircraft_types)
                    ])
                    self.route_id_counter += 1
                    route_count += 1
        
        query = f"""
            INSERT INTO flight_routes (route_id, origin_code, destination_code, airlines,
                                     flight_duration_minutes, distance_km, typical_aircraft)
            VALUES {', '.join(values_list)}
        """
        self.db.adapter.execute_query(query, tuple(params_list))
        
        logger.info(f"Seeded {route_count} flight routes")
    
    def seed_flights(self):
        """Seed 60 days of flight data."""
        logger.info("Generating flights for 60 days...")
        
        start_date = date.today()
        end_date = start_date + timedelta(days=60)
        
        # Get all routes
        routes = self.db.adapter.execute_query("SELECT * FROM flight_routes")
        
        total_flights = 0
        current_date = start_date
        
        # Batch configuration
        BATCH_SIZE = 900
        flights_batch = []
        
        while current_date <= end_date:
            for route in routes:
                # Parse JSON fields
                airlines = route['airlines']
                aircraft_types = route['typical_aircraft']
                
                # Generate 2-6 flights per day depending on route
                num_flights = random.randint(2, 6)
                
                for flight_idx in range(num_flights):
                    airline = random.choice(airlines)
                    aircraft = random.choice(aircraft_types)
                    
                    # Generate flight times throughout the day
                    hour = 6 + (flight_idx * 3) + random.randint(0, 2)
                    if hour >= 24:
                        hour = hour % 24
                        
                    departure_time = time(hour, random.choice([0, 15, 30, 45]))
                    
                    # Calculate arrival time
                    departure_datetime = datetime.combine(current_date, departure_time)
                    arrival_datetime = departure_datetime + timedelta(minutes=route['flight_duration_minutes'])
                    
                    # Generate flight number
                    flight_number = f"{airline}{random.randint(100, 999)}"
                    
                    # Generate pricing based on various factors
                    base_economy_price = self._calculate_base_price(route['distance_km'])
                    economy_price = self._apply_pricing_factors(base_economy_price, current_date, departure_time)
                    
                    flight_data = (
                        self.flight_id_counter, flight_number, airline, route['origin_code'], route['destination_code'],
                        current_date, departure_time, arrival_datetime.date(), arrival_datetime.time(),
                        route['flight_duration_minutes'], aircraft,
                        random.randint(50, 180),  # economy seats
                        random.randint(10, 40),   # business seats
                        random.randint(4, 12),    # first class seats
                        round(economy_price, 2),
                        round(economy_price * 2.5, 2),  # business price
                        round(economy_price * 4, 2),    # first class price
                        'scheduled'
                    )
                    flights_batch.append(flight_data)
                    self.flight_id_counter += 1
                    total_flights += 1
                    
                    # Insert batch when it reaches the size limit
                    if len(flights_batch) >= BATCH_SIZE:
                        self._insert_flights_batch(flights_batch)
                        flights_batch = []
                        logger.info(f"  Inserted {total_flights} flights so far...")
            
            if current_date.day == 1 or current_date.day == 15:
                logger.info(f"  Generated flights up to {current_date.strftime('%Y-%m-%d')}")
            
            current_date += timedelta(days=1)
        
        # Insert remaining flights
        if flights_batch:
            self._insert_flights_batch(flights_batch)
        
        logger.info(f"Seeded {total_flights} flights")
    
    def _insert_flights_batch(self, flights_batch):
        """Insert a batch of flights using multi-value insert."""
        if not flights_batch:
            return
        
        # Build multi-value INSERT statement
        values_list = []
        params_list = []
        
        for flight in flights_batch:
            values_list.append("(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
            params_list.extend(flight)
        
        query = f"""
            INSERT INTO flights (flight_id, flight_number, airline_code, origin_code, destination_code,
                               departure_date, departure_time, arrival_date, arrival_time,
                               duration_minutes, aircraft_type, economy_seats_available,
                               business_seats_available, first_seats_available,
                               economy_price, business_price, first_price, status)
            VALUES {', '.join(values_list)}
        """
        
        self.db.adapter.execute_query(query, tuple(params_list))
    
    def seed_hotels(self):
        """Seed hotels data."""
        logger.info("Seeding hotels...")
        
        hotel_templates = {
            'luxury': {
                'names': ['Grand {city}', 'The {city} Palace', 'Four Seasons {city}', '{city} Ritz-Carlton', 'Mandarin Oriental {city}'],
                'base_price_range': (400, 1200),
                'star_rating': 5,
                'amenities': ['spa', 'pool', 'gym', 'restaurant', 'bar', 'concierge', 'room-service', 'valet-parking', 'business-center'],
                'room_types': ['deluxe', 'executive', 'suite', 'penthouse'],
                'tags': ['luxury', 'elegant', 'upscale', 'premium']
            },
            'boutique': {
                'names': ['Hotel {city} Boutique', 'The {city} House', '{city} Design Hotel', 'Artisan {city}', 'The {city} Collection'],
                'base_price_range': (200, 600),
                'star_rating': 4,
                'amenities': ['restaurant', 'bar', 'gym', 'concierge', 'room-service', 'wifi', 'laundry'],
                'room_types': ['standard', 'deluxe', 'suite'],
                'tags': ['boutique', 'stylish', 'intimate', 'unique', 'romantic']
            },
            'business': {
                'names': ['Hilton {city}', 'Marriott {city}', 'Hyatt {city}', 'Sheraton {city}', 'InterContinental {city}'],
                'base_price_range': (150, 400),
                'star_rating': 4,
                'amenities': ['business-center', 'meeting-rooms', 'gym', 'restaurant', 'bar', 'wifi', 'parking'],
                'room_types': ['standard', 'executive', 'suite'],
                'tags': ['business', 'convenient', 'professional', 'central']
            },
            'budget': {
                'names': ['Comfort Inn {city}', 'Holiday Inn Express {city}', '{city} Budget Hotel', 'EasyStay {city}', '{city} Hostel'],
                'base_price_range': (50, 150),
                'star_rating': 2,
                'amenities': ['wifi', 'breakfast', 'parking', '24-hour-desk'],
                'room_types': ['standard', 'double'],
                'tags': ['budget', 'affordable', 'basic', 'value']
            }
        }
        
        neighborhoods = {
            'NYC': ['Manhattan', 'Times Square', 'Central Park', 'Brooklyn', 'SoHo'],
            'CDG': ['Champs-Élysées', 'Le Marais', 'Saint-Germain', 'Montmartre', 'Latin Quarter'],
            'NRT': ['Shinjuku', 'Shibuya', 'Ginza', 'Asakusa', 'Roppongi'],
            'SYD': ['CBD', 'Darling Harbour', 'Bondi', 'The Rocks', 'Kings Cross'],
            'DPS': ['Seminyak', 'Ubud', 'Nusa Dua', 'Canggu', 'Kuta'],
            'CPT': ['V&A Waterfront', 'City Bowl', 'Camps Bay', 'Sea Point', 'Green Point'],
            'GIG': ['Copacabana', 'Ipanema', 'Centro', 'Santa Teresa', 'Barra da Tijuca']
        }
        
        # Build batch insert
        values_list = []
        params_list = []
        hotel_count = 0
        
        for city in self.DEMO_CITIES:
            city_code = city['code']
            city_name = city['name']
            city_neighborhoods = neighborhoods.get(city_code, ['Downtown', 'City Center', 'Business District'])
            
            # Generate 8-12 hotels per city across different categories
            for hotel_type, template in hotel_templates.items():
                num_hotels = 2 if hotel_type == 'luxury' else 3
                
                for i in range(num_hotels):
                    name_template = random.choice(template['names'])
                    hotel_name = name_template.replace('{city}', city_name)
                    
                    neighborhood = random.choice(city_neighborhoods)
                    
                    values_list.append("(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
                    params_list.extend([
                        self.hotel_id_counter, hotel_name, city_code,
                        f'{random.randint(1, 999)} {neighborhood} Street, {city_name}',
                        city['latitude'] + random.uniform(-0.1, 0.1),
                        city['longitude'] + random.uniform(-0.1, 0.1),
                        template['star_rating'], hotel_type,
                        json.dumps(template['amenities']),
                        json.dumps(template['room_types']),
                        f"A {hotel_type} hotel located in the heart of {neighborhood}, offering exceptional service and comfort.",
                        f"Located in {neighborhood}, one of {city_name}'s most vibrant areas.",
                        json.dumps(template['tags'] + city['tags'][:2]),
                        template['base_price_range'][0],
                        template['base_price_range'][1]
                    ])
                    self.hotel_id_counter += 1
                    hotel_count += 1
        
        query = f"""
            INSERT INTO hotels (hotel_id, name, city_code, address, latitude, longitude,
                              star_rating, hotel_type, amenities, room_types,
                              description, neighborhood_description, tags,
                              base_price_min, base_price_max)
            VALUES {', '.join(values_list)}
        """
        self.db.adapter.execute_query(query, tuple(params_list))
        
        logger.info(f"Seeded {hotel_count} hotels")
    
    def seed_hotel_availability(self):
        """Seed 60 days of hotel availability."""
        logger.info("Generating hotel availability for 60 days...")
        
        hotels = self.db.adapter.execute_query("SELECT * FROM hotels")
        start_date = date.today()
        end_date = start_date + timedelta(days=60)
        
        total_records = 0
        BATCH_SIZE = 900
        availability_batch = []
        
        for hotel in hotels:
            current_date = start_date
            
            while current_date <= end_date:
                # Base occupancy varies by day of week and season
                base_occupancy = self._calculate_base_occupancy(current_date, hotel['city_code'])
                
                # Calculate room availability based on occupancy
                total_standard_rooms = 30
                total_deluxe_rooms = 15
                total_suites = 5
                
                standard_available = int(total_standard_rooms * (1 - base_occupancy / 100))
                deluxe_available = int(total_deluxe_rooms * (1 - base_occupancy / 100))
                suite_available = int(total_suites * (1 - base_occupancy / 100))
                
                # Calculate pricing based on occupancy and other factors
                price_multiplier = 1 + (base_occupancy / 100) * 0.5  # Higher occupancy = higher price
                
                # Convert Decimal to float for calculations
                base_price = float(hotel['base_price_min'])
                
                availability_data = (
                    self.availability_id_counter, hotel['hotel_id'], current_date,
                    max(1, standard_available),
                    round(base_price * price_multiplier, 2),
                    max(0, deluxe_available),
                    round(base_price * 1.5 * price_multiplier, 2),
                    max(0, suite_available),
                    round(base_price * 2.5 * price_multiplier, 2),
                    base_occupancy
                )
                availability_batch.append(availability_data)
                self.availability_id_counter += 1
                total_records += 1
                
                # Insert batch when it reaches the size limit
                if len(availability_batch) >= BATCH_SIZE:
                    self._insert_hotel_availability_batch(availability_batch)
                    availability_batch = []
                    logger.info(f"  Inserted {total_records} availability records so far...")
                
                current_date += timedelta(days=1)
        
        # Insert remaining records
        if availability_batch:
            self._insert_hotel_availability_batch(availability_batch)
        
        logger.info(f"Seeded {total_records} hotel availability records")
    
    def _insert_hotel_availability_batch(self, availability_batch):
        """Insert a batch of hotel availability records using multi-value insert."""
        if not availability_batch:
            return
        
        # Build multi-value INSERT statement
        values_list = []
        params_list = []
        
        for availability in availability_batch:
            values_list.append("(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
            params_list.extend(availability)
        
        query = f"""
            INSERT INTO hotel_availability (availability_id, hotel_id, date, standard_rooms_available,
                                          standard_room_price, deluxe_rooms_available,
                                          deluxe_room_price, suite_rooms_available,
                                          suite_room_price, occupancy_rate)
            VALUES {', '.join(values_list)}
        """
        
        self.db.adapter.execute_query(query, tuple(params_list))
    
    def seed_activities(self):
        """Seed activities data."""
        logger.info("Seeding activities...")
        
        # Activity templates by city
        activity_templates = {
            'NYC': [
                {
                    'name': 'Statue of Liberty & Ellis Island Tour',
                    'category': 'sightseeing',
                    'description': 'Visit the iconic Statue of Liberty and explore the Immigration Museum at Ellis Island.',
                    'duration_hours': 4,
                    'price_adult': 25,
                    'price_child': 15,
                    'tags': ['iconic', 'historical', 'must-see'],
                    'includes': ['Ferry tickets', 'Audio guide', 'Museum access']
                },
                {
                    'name': 'Broadway Show Experience',
                    'category': 'cultural',
                    'description': 'Enjoy a world-class Broadway performance in the Theater District.',
                    'duration_hours': 3,
                    'price_adult': 150,
                    'price_child': 150,
                    'tags': ['entertainment', 'cultural', 'evening'],
                    'includes': ['Orchestra seats', 'Playbill']
                },
                {
                    'name': 'Central Park Bike Tour',
                    'category': 'adventure',
                    'description': 'Explore Central Park on two wheels with a knowledgeable guide.',
                    'duration_hours': 2,
                    'price_adult': 45,
                    'price_child': 30,
                    'tags': ['outdoor', 'active', 'nature'],
                    'includes': ['Bike rental', 'Helmet', 'Guide']
                }
            ],
            'CDG': [
                {
                    'name': 'Eiffel Tower Skip-the-Line & Summit',
                    'category': 'sightseeing',
                    'description': 'Skip the lines and ascend to the summit of the Eiffel Tower for breathtaking views.',
                    'duration_hours': 2,
                    'price_adult': 35,
                    'price_child': 20,
                    'tags': ['iconic', 'romantic', 'views'],
                    'includes': ['Skip-the-line tickets', 'Summit access']
                },
                {
                    'name': 'Louvre Museum Guided Tour',
                    'category': 'cultural',
                    'description': 'Discover masterpieces including the Mona Lisa with an expert guide.',
                    'duration_hours': 3,
                    'price_adult': 65,
                    'price_child': 45,
                    'tags': ['art', 'cultural', 'educational'],
                    'includes': ['Entry ticket', 'Professional guide', 'Audio headset']
                }
            ],
            'NRT': [
                {
                    'name': 'Mt. Fuji Day Trip',
                    'category': 'adventure',
                    'description': 'Journey to Japan\'s iconic mountain with stops at scenic viewpoints.',
                    'duration_hours': 10,
                    'price_adult': 120,
                    'price_child': 80,
                    'tags': ['nature', 'iconic', 'scenic'],
                    'includes': ['Transportation', 'Guide', 'Lunch']
                },
                {
                    'name': 'Traditional Tea Ceremony',
                    'category': 'cultural',
                    'description': 'Experience an authentic Japanese tea ceremony in a traditional setting.',
                    'duration_hours': 1.5,
                    'price_adult': 50,
                    'price_child': 35,
                    'tags': ['cultural', 'traditional', 'authentic'],
                    'includes': ['Tea ceremony', 'Traditional sweets', 'Cultural explanation']
                }
            ]
        }
        
        # Generic activities for cities without specific templates
        generic_activities = [
            {
                'name': 'City Walking Tour',
                'category': 'sightseeing',
                'duration_hours': 3,
                'price_adult': 30,
                'price_child': 15,
                'tags': ['cultural', 'historical', 'walking'],
                'includes': ['Professional guide', 'Map']
            },
            {
                'name': 'Food & Market Tour',
                'category': 'culinary',
                'duration_hours': 3.5,
                'price_adult': 75,
                'price_child': 50,
                'tags': ['food', 'cultural', 'local'],
                'includes': ['Food tastings', 'Market visit', 'Local guide']
            }
        ]
        
        activity_count = 0
        
        for city in self.DEMO_CITIES:
            city_code = city['code']
            city_name = city['name']
            
            # Get city-specific activities or use generic ones
            city_activities = activity_templates.get(city_code, generic_activities)
            
            for idx, activity_template in enumerate(city_activities):
                # Add location information
                location = f"{city_name} City Center"
                meeting_point = f"Main entrance, {random.randint(1, 100)} {city_name} Plaza"
                
                query = """
                    INSERT INTO activities (activity_id, name, city_code, location, category, description,
                                          duration_hours, duration_minutes, price_adult, price_child,
                                          rating, tags, includes, available_days, time_slots,
                                          meeting_point, latitude, longitude)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                            %s, %s, %s, %s, %s)
                """
                
                duration_minutes = int(activity_template['duration_hours'] * 60)
                rating = round(random.uniform(4.0, 5.0), 1)
                time_slots = ['09:00', '14:00'] if activity_template['duration_hours'] <= 4 else ['09:00']
                
                params = (
                    self.activity_id_counter,
                    activity_template['name'],
                    city_code,
                    location,
                    activity_template['category'],
                    activity_template.get('description', f"Experience the best of {city_name}"),
                    activity_template['duration_hours'],
                    duration_minutes,
                    activity_template['price_adult'],
                    activity_template['price_child'],
                    rating,
                    json.dumps(activity_template['tags']),
                    json.dumps(activity_template['includes']),
                    json.dumps(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']),
                    json.dumps(time_slots),
                    meeting_point,
                    city['latitude'] + random.uniform(-0.05, 0.05),
                    city['longitude'] + random.uniform(-0.05, 0.05)
                )
                self.db.adapter.execute_query(query, params)
                self.activity_id_counter += 1
                activity_count += 1
        
        logger.info(f"Seeded {activity_count} activities")
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in kilometers."""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _select_airlines_for_route(self, origin: str, destination: str) -> List[str]:
        """Select appropriate airlines for a route."""
        selected_airlines = []
        
        # Always include airlines that have hubs in either origin or destination
        for airline in self.AIRLINES:
            if origin in airline['hub_cities'] or destination in airline['hub_cities']:
                selected_airlines.append(airline['code'])
        
        # Add some random international carriers for variety
        if len(selected_airlines) < 2:
            other_airlines = [a['code'] for a in self.AIRLINES if a['code'] not in selected_airlines]
            selected_airlines.extend(random.sample(other_airlines, min(2, len(other_airlines))))
        
        return selected_airlines[:4]  # Limit to 4 airlines per route
    
    def _calculate_base_price(self, distance_km: int) -> float:
        """Calculate base economy price based on distance."""
        # Base pricing: $50 + $0.10 per km
        base = 50 + (distance_km * 0.10)
        
        # Add some randomness
        return base * random.uniform(0.8, 1.2)
    
    def _apply_pricing_factors(self, base_price: float, travel_date: date, departure_time: time) -> float:
        """Apply various pricing factors to the base price."""
        price = base_price
        
        # Day of week factor
        if travel_date.weekday() in [4, 5, 6]:  # Friday, Saturday, Sunday
            price *= 1.2
        
        # Season factor
        month = travel_date.month
        if month in [6, 7, 8, 12]:  # Summer and December
            price *= 1.3
        elif month in [1, 2]:  # Low season
            price *= 0.8
        
        # Time of day factor
        if 6 <= departure_time.hour <= 9 or 17 <= departure_time.hour <= 20:
            price *= 1.1  # Peak hours
        
        # Advance booking factor (random for demo)
        advance_days = random.randint(1, 180)
        if advance_days > 60:
            price *= 0.85
        elif advance_days < 7:
            price *= 1.5
        
        return price
    
    def _calculate_base_occupancy(self, check_date: date, city_code: str) -> float:
        """Calculate base hotel occupancy rate."""
        base = 60.0
        
        # Weekend boost
        if check_date.weekday() in [4, 5]:
            base += 20
        
        # Seasonal adjustments
        month = check_date.month
        if month in [6, 7, 8]:  # Summer
            base += 15
        elif month in [12]:  # December holidays
            base += 25
        elif month in [1, 2]:  # Low season
            base -= 20
        
        # City-specific adjustments
        if city_code in ['NYC', 'CDG', 'NRT']:
            base += 10  # Major cities have higher occupancy
        
        # Add some randomness
        base += random.uniform(-10, 10)
        
        return min(95, max(20, base))  # Cap between 20% and 95%
    
    def create_summary(self):
        """Create a summary of seeded data."""
        logger.info("\n=== Seeding Summary ===")
        
        tables = ['cities', 'airlines', 'hotels', 'activities', 'flight_routes', 'flights', 'hotel_availability']
        for table in tables:
            count = self.db.adapter.get_table_count(table)
            logger.info(f"{table.capitalize()}: {count:,} records")
        
        # Show some sample data
        logger.info("\nSample cities:")
        cities = self.db.adapter.execute_query("SELECT code, name, country FROM cities ORDER BY code LIMIT 7")
        for city in cities:
            logger.info(f"  {city['code']} - {city['name']}, {city['country']}")
        
        logger.info("\nSample airlines:")
        airlines = self.db.adapter.execute_query("SELECT code, name FROM airlines ORDER BY code LIMIT 5")
        for airline in airlines:
            logger.info(f"  {airline['code']} - {airline['name']}")
    
    def run(self, clear_existing=True):
        """Run the seeding process."""
        try:
            logger.info("Starting DSQL seeding process...")
            logger.info("This will generate data matching the SQLite database structure...")
            
            if clear_existing:
                self.clear_existing_data()
            
            # Seed in dependency order
            self.seed_cities()
            self.seed_airlines()
            self.seed_flight_routes()
            self.seed_hotels()
            self.seed_activities()
            
            # Generate time-based data
            logger.info("\nGenerating time-based data (this may take a few minutes)...")
            self.seed_flights()
            self.seed_hotel_availability()
            
            self.create_summary()
            
            logger.info("\n✅  DSQL seeding completed successfully!")
            logger.info("   Data volume generated:")
            logger.info("   - 7 cities with full details")
            logger.info("   - 12 airlines")
            logger.info("   - ~10,000 scheduled flights (60 days)")
            logger.info("   - 70+ hotels with availability (60 days)")
            logger.info("   - Activities in each city")
            
        except Exception as e:
            logger.error(f"Seeding failed: {e}")
            raise


def main():
    """Main function to seed all data."""
    try:
        logger.info("=== Starting DSQL Database Seeding ===")
        logger.info("This will generate all travel planning data including:")
        logger.info("  • Cities and destinations")
        logger.info("  • Airlines and flight routes") 
        logger.info("  • Hotels and accommodations")
        logger.info("  • Activities and experiences")
        logger.info("  • Flights and hotel availability")
        logger.info("")
        
        # Use the comprehensive DSQLSeeder
        seeder = DSQLSeeder()
        seeder.run()
        
    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}")
        raise


if __name__ == "__main__":
    main()