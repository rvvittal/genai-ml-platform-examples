"""Data generator for travel planning demo database."""

import random
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Tuple
import logging

from .models import City, Airline, FlightRoute, Flight, Hotel, Activity
from .db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class DataGenerator:
    """Generate realistic travel data for demo purposes."""
    
    # Demo cities configuration
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
            'country': 'Australia',
            'continent': 'Oceania',
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
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        
    def generate_all_data(self):
        """Generate all data for the demo."""
        logger.info("Starting data generation...")
        
        # Insert cities
        logger.info("Inserting cities...")
        self._insert_cities()
        
        # Insert airlines
        logger.info("Inserting airlines...")
        self._insert_airlines()
        
        # Generate flight routes
        logger.info("Generating flight routes...")
        self._generate_flight_routes()
        
        # Generate flights for 12 months
        logger.info("Generating flights...")
        self._generate_flights()
        
        # Generate hotels
        logger.info("Generating hotels...")
        self._generate_hotels()
        
        # Generate hotel availability
        logger.info("Generating hotel availability...")
        self._generate_hotel_availability()
        
        # Generate activities
        logger.info("Generating activities...")
        self._generate_activities()
        
        logger.info("Data generation complete!")
        
    def _insert_cities(self):
        """Insert demo cities into database."""
        for city_data in self.DEMO_CITIES:
            self.db.insert_city(city_data)
            
    def _insert_airlines(self):
        """Insert airlines into database."""
        for airline_data in self.AIRLINES:
            self.db.insert_airline(airline_data)
            
    def _generate_flight_routes(self):
        """Generate flight routes between cities."""
        city_codes = [c['code'] for c in self.DEMO_CITIES]
        
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
                    
                    route_data = {
                        'origin_code': origin,
                        'destination_code': destination,
                        'airlines': route_airlines,
                        'flight_duration_minutes': flight_duration,
                        'distance_km': int(distance),
                        'typical_aircraft': aircraft_types
                    }
                    self.db.insert_flight_route(route_data)
                    
    def _generate_flights(self):
        """Generate 12 months of flight data."""
        start_date = date.today()
        end_date = start_date + timedelta(days=365)
        
        # Get all routes
        routes = self.db.execute_query("SELECT * FROM flight_routes")
        
        current_date = start_date
        while current_date <= end_date:
            flights_batch = []
            
            for route in routes:
                # Parse JSON fields
                airlines = eval(route['airlines'])  # Safe since we control the data
                aircraft_types = eval(route['typical_aircraft'])
                
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
                    
                    flight_data = {
                        'flight_number': flight_number,
                        'airline_code': airline,
                        'origin_code': route['origin_code'],
                        'destination_code': route['destination_code'],
                        'departure_date': current_date.isoformat(),
                        'departure_time': departure_time.isoformat(),
                        'arrival_date': arrival_datetime.date().isoformat(),
                        'arrival_time': arrival_datetime.time().isoformat(),
                        'duration_minutes': route['flight_duration_minutes'],
                        'aircraft_type': aircraft,
                        'economy_seats_available': random.randint(50, 180),
                        'economy_price': round(economy_price, 2),
                        'business_seats_available': random.randint(10, 40),
                        'business_price': round(economy_price * 2.5, 2),
                        'first_seats_available': random.randint(4, 12),
                        'first_price': round(economy_price * 4, 2),
                        'status': 'scheduled'
                    }
                    flights_batch.append(flight_data)
                    
            # Insert batch of flights for this day
            if flights_batch:
                self.db.insert_flights_batch(flights_batch)
                
            current_date += timedelta(days=1)
            
    def _generate_hotels(self):
        """Generate hotels for each city."""
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
                    
                    hotel_data = {
                        'name': hotel_name,
                        'city_code': city_code,
                        'address': f'{random.randint(1, 999)} {neighborhood} Street, {city_name}',
                        'latitude': city['latitude'] + random.uniform(-0.1, 0.1),
                        'longitude': city['longitude'] + random.uniform(-0.1, 0.1),
                        'star_rating': template['star_rating'],
                        'hotel_type': hotel_type,
                        'amenities': template['amenities'],
                        'room_types': template['room_types'],
                        'description': f"A {hotel_type} hotel located in the heart of {neighborhood}, offering exceptional service and comfort.",
                        'neighborhood_description': f"Located in {neighborhood}, one of {city_name}'s most vibrant areas.",
                        'tags': template['tags'] + city['tags'][:2],  # Include some city tags
                        'base_price_min': template['base_price_range'][0],
                        'base_price_max': template['base_price_range'][1]
                    }
                    self.db.insert_hotel(hotel_data)
                    
    def _generate_hotel_availability(self):
        """Generate 12 months of hotel availability."""
        hotels = self.db.execute_query("SELECT * FROM hotels")
        start_date = date.today()
        end_date = start_date + timedelta(days=365)
        
        for hotel in hotels:
            availability_batch = []
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
                
                base_price = hotel['base_price_min']
                
                availability_data = {
                    'hotel_id': hotel['hotel_id'],
                    'date': current_date.isoformat(),
                    'standard_rooms_available': max(1, standard_available),
                    'standard_room_price': round(base_price * price_multiplier, 2),
                    'deluxe_rooms_available': max(0, deluxe_available),
                    'deluxe_room_price': round(base_price * 1.5 * price_multiplier, 2),
                    'suite_rooms_available': max(0, suite_available),
                    'suite_room_price': round(base_price * 2.5 * price_multiplier, 2),
                    'occupancy_rate': base_occupancy
                }
                availability_batch.append(availability_data)
                
                current_date += timedelta(days=1)
                
            # Insert batch of availability for this hotel
            if availability_batch:
                self.db.insert_hotel_availability_batch(availability_batch)
                
    def _generate_activities(self):
        """Generate activities for each city."""
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
                    'name': 'Seine River Dinner Cruise',
                    'category': 'romantic',
                    'description': 'Romantic evening cruise with gourmet French cuisine and live music.',
                    'duration_hours': 2.5,
                    'price_adult': 120,
                    'price_child': 60,
                    'tags': ['romantic', 'dining', 'evening'],
                    'includes': ['3-course dinner', 'Wine', 'Live music']
                },
                {
                    'name': 'Louvre Museum Guided Tour',
                    'category': 'cultural',
                    'description': 'Expert-led tour of the world\'s most visited museum.',
                    'duration_hours': 3,
                    'price_adult': 65,
                    'price_child': 30,
                    'tags': ['art', 'cultural', 'educational'],
                    'includes': ['Skip-the-line entry', 'Expert guide', 'Headsets']
                }
            ],
            'DPS': [
                {
                    'name': 'Sunrise Trek to Mount Batur',
                    'category': 'adventure',
                    'description': 'Early morning trek to watch the sunrise from an active volcano.',
                    'duration_hours': 6,
                    'price_adult': 60,
                    'price_child': 40,
                    'tags': ['adventure', 'nature', 'sunrise'],
                    'includes': ['Hotel pickup', 'Guide', 'Breakfast', 'Flashlight']
                },
                {
                    'name': 'Ubud Rice Terrace & Temple Tour',
                    'category': 'cultural',
                    'description': 'Visit the famous Tegallalang Rice Terraces and ancient temples.',
                    'duration_hours': 8,
                    'price_adult': 45,
                    'price_child': 25,
                    'tags': ['cultural', 'nature', 'photography'],
                    'includes': ['Transport', 'Guide', 'Temple entrance fees']
                },
                {
                    'name': 'Balinese Spa Experience',
                    'category': 'romantic',
                    'description': 'Traditional Balinese spa treatment with massage and flower bath.',
                    'duration_hours': 3,
                    'price_adult': 80,
                    'price_child': 0,
                    'tags': ['relaxation', 'romantic', 'wellness'],
                    'includes': ['90-min massage', 'Flower bath', 'Herbal tea']
                }
            ]
        }
        
        # Generate similar activities for other cities
        for city in self.DEMO_CITIES:
            city_code = city['code']
            
            # Use template activities if available, otherwise generate generic ones
            if city_code in activity_templates:
                activities = activity_templates[city_code]
            else:
                # Generate generic activities based on city tags
                activities = self._generate_generic_activities(city)
                
            for activity in activities:
                activity_data = {
                    'name': activity['name'],
                    'city_code': city_code,
                    'category': activity['category'],
                    'description': activity['description'],
                    'duration_hours': activity['duration_hours'],
                    'price_adult': activity['price_adult'],
                    'price_child': activity['price_child'],
                    'tags': activity['tags'],
                    'includes': activity['includes'],
                    'available_days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    'time_slots': ['09:00', '14:00', '16:00'] if 'evening' not in activity['tags'] else ['18:00', '19:00', '20:00'],
                    'meeting_point': f"Hotel pickup available or meet at {city['name']} city center",
                    'latitude': city['latitude'] + random.uniform(-0.05, 0.05),
                    'longitude': city['longitude'] + random.uniform(-0.05, 0.05)
                }
                self.db.insert_activity(activity_data)
                
    def _generate_generic_activities(self, city: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate generic activities based on city characteristics."""
        activities = []
        
        # City tour
        activities.append({
            'name': f'{city["name"]} City Highlights Tour',
            'category': 'sightseeing',
            'description': f'Comprehensive tour of {city["name"]}\'s main attractions and hidden gems.',
            'duration_hours': 4,
            'price_adult': 50,
            'price_child': 25,
            'tags': ['sightseeing', 'cultural', 'must-see'],
            'includes': ['Transport', 'Guide', 'Entrance fees']
        })
        
        # Food tour if gourmet tag
        if 'gourmet' in city['tags'] or 'cultural' in city['tags']:
            activities.append({
                'name': f'{city["name"]} Food & Market Tour',
                'category': 'culinary',
                'description': f'Taste the flavors of {city["name"]} with visits to local markets and restaurants.',
                'duration_hours': 3,
                'price_adult': 75,
                'price_child': 40,
                'tags': ['culinary', 'cultural', 'walking'],
                'includes': ['Food tastings', 'Guide', 'Market visits']
            })
            
        # Beach activity if beach tag
        if 'beach' in city['tags']:
            activities.append({
                'name': f'{city["name"]} Beach & Water Sports',
                'category': 'adventure',
                'description': 'Enjoy beach activities and water sports at the best local beaches.',
                'duration_hours': 4,
                'price_adult': 60,
                'price_child': 40,
                'tags': ['beach', 'adventure', 'water-sports'],
                'includes': ['Equipment', 'Instruction', 'Beach access']
            })
            
        return activities
        
    # Helper methods
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate approximate distance between two points in kilometers."""
        import math
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
        # For demo, just select 2-4 airlines that could plausibly fly the route
        available_airlines = []
        
        # Always include some major carriers
        available_airlines.extend(['AA', 'UA', 'DL'])
        
        # Add regional carriers based on continents
        if origin == 'CDG' or destination == 'CDG':
            available_airlines.extend(['AF', 'BA', 'LH'])
        if origin == 'NRT' or destination == 'NRT':
            available_airlines.extend(['JL', 'NH'])
        if origin == 'SYD' or destination == 'SYD':
            available_airlines.append('QF')
        if origin == 'CPT' or destination == 'CPT':
            available_airlines.append('SA')
        if origin == 'DPS' or destination == 'DPS':
            available_airlines.append('GA')
        if origin == 'GIG' or destination == 'GIG':
            available_airlines.append('LA')
            
        # Return unique airlines, limited to 4
        return list(set(available_airlines))[:4]
        
    def _calculate_base_price(self, distance_km: int) -> float:
        """Calculate base economy price based on distance."""
        # Rough pricing: $50 base + $0.10 per km
        return 50 + (distance_km * 0.10)
        
    def _apply_pricing_factors(self, base_price: float, travel_date: date, departure_time: time) -> float:
        """Apply various pricing factors to base price."""
        price = base_price
        
        # Day of week factor
        if travel_date.weekday() in [4, 5, 6]:  # Friday, Saturday, Sunday
            price *= 1.2
        elif travel_date.weekday() in [1, 2, 3]:  # Tuesday, Wednesday, Thursday
            price *= 0.9
            
        # Advance booking factor (random for demo)
        days_advance = random.randint(1, 180)
        if days_advance < 7:
            price *= 1.5
        elif days_advance < 14:
            price *= 1.3
        elif days_advance > 60:
            price *= 0.85
            
        # Time of day factor
        if departure_time.hour < 6 or departure_time.hour > 22:  # Red-eye
            price *= 0.8
        elif 7 <= departure_time.hour <= 9 or 17 <= departure_time.hour <= 19:  # Peak
            price *= 1.1
            
        # Seasonal factor (summer/holidays more expensive)
        if travel_date.month in [6, 7, 8, 12]:
            price *= 1.25
            
        return price
        
    def _calculate_base_occupancy(self, check_date: date, city_code: str) -> float:
        """Calculate base hotel occupancy rate."""
        # Base occupancy
        occupancy = 60.0
        
        # Day of week factor
        if check_date.weekday() in [4, 5]:  # Friday, Saturday
            occupancy += 20
        elif check_date.weekday() in [0, 1, 2, 3]:  # Monday-Thursday
            if city_code in ['NYC', 'NRT', 'CDG']:  # Business cities
                occupancy += 15
                
        # Seasonal factor
        if check_date.month in [6, 7, 8]:  # Summer
            if city_code in ['CDG', 'DPS', 'SYD']:
                occupancy += 25
        elif check_date.month in [12, 1]:  # Holiday season
            occupancy += 20
            
        # Add some randomness
        occupancy += random.uniform(-10, 10)
        
        return min(95, max(30, occupancy))  # Keep between 30-95%