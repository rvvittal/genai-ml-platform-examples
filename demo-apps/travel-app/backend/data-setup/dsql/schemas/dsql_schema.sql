-- Aurora DSQL Minimal Schema for Travel Planner
-- Working within Aurora DSQL's current limitations

-- Drop existing tables if needed
DROP TABLE IF EXISTS bookings CASCADE;
DROP TABLE IF EXISTS travel_plans CASCADE;
DROP TABLE IF EXISTS hotel_availability CASCADE;
DROP TABLE IF EXISTS hotel_rooms CASCADE;
DROP TABLE IF EXISTS activities CASCADE;
DROP TABLE IF EXISTS hotels CASCADE;
DROP TABLE IF EXISTS flights CASCADE;
DROP TABLE IF EXISTS flight_routes CASCADE;
DROP TABLE IF EXISTS airlines CASCADE;
DROP TABLE IF EXISTS cities CASCADE;

-- Cities table
CREATE TABLE cities (
    code VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    continent VARCHAR(50),
    timezone VARCHAR(50),
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7),
    description TEXT,
    tags TEXT DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Airlines table
CREATE TABLE airlines (
    code VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    hub_cities TEXT DEFAULT '[]'
);

-- Hotels table
CREATE TABLE hotels (
    hotel_id INTEGER PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    city_code VARCHAR(10) NOT NULL,
    address TEXT,
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7),
    star_rating INTEGER CHECK (star_rating >= 1 AND star_rating <= 5),
    hotel_type VARCHAR(50),
    amenities TEXT DEFAULT '[]',
    room_types TEXT DEFAULT '[]',
    description TEXT,
    neighborhood_description TEXT,
    tags TEXT DEFAULT '[]',
    base_price_min NUMERIC(10, 2),
    base_price_max NUMERIC(10, 2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Hotel room types
CREATE TABLE hotel_rooms (
    room_id INTEGER PRIMARY KEY,
    hotel_id INTEGER NOT NULL,
    room_type VARCHAR(50) NOT NULL,
    price_per_night NUMERIC(10, 2) NOT NULL,
    max_occupancy INTEGER DEFAULT 2
);

-- Hotel availability
CREATE TABLE hotel_availability (
    availability_id INTEGER PRIMARY KEY,
    hotel_id INTEGER NOT NULL,
    date DATE NOT NULL,
    standard_rooms_available INTEGER DEFAULT 10,
    standard_room_price NUMERIC(10, 2),
    deluxe_rooms_available INTEGER DEFAULT 5,
    deluxe_room_price NUMERIC(10, 2),
    suite_rooms_available INTEGER DEFAULT 2,
    suite_room_price NUMERIC(10, 2),
    occupancy_rate NUMERIC(5, 2) DEFAULT 50.0,
    UNIQUE(hotel_id, date)
);

-- Activities table
CREATE TABLE activities (
    activity_id INTEGER PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    city_code VARCHAR(10) NOT NULL,
    location VARCHAR(200),
    category VARCHAR(50),
    description TEXT,
    duration_hours NUMERIC(4, 2),
    duration_minutes INTEGER,
    price_adult NUMERIC(10, 2),
    price_child NUMERIC(10, 2),
    rating NUMERIC(3, 2) CHECK (rating >= 0 AND rating <= 5),
    tags TEXT DEFAULT '[]',
    includes TEXT DEFAULT '[]',
    available_days TEXT DEFAULT '["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]',
    time_slots TEXT DEFAULT '[]',
    availability TEXT DEFAULT '{}',
    meeting_point TEXT,
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Flight routes table
CREATE TABLE flight_routes (
    route_id INTEGER PRIMARY KEY,
    origin_code VARCHAR(10) NOT NULL,
    destination_code VARCHAR(10) NOT NULL,
    airlines TEXT DEFAULT '[]',
    flight_duration_minutes INTEGER NOT NULL,
    distance_km INTEGER,
    typical_aircraft TEXT DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(origin_code, destination_code)
);

-- Flights table
CREATE TABLE flights (
    flight_id INTEGER PRIMARY KEY,
    flight_number VARCHAR(20) NOT NULL,
    airline_code VARCHAR(10) NOT NULL,
    origin_code VARCHAR(10) NOT NULL,
    destination_code VARCHAR(10) NOT NULL,
    departure_date DATE NOT NULL,
    departure_time TIME NOT NULL,
    arrival_date DATE NOT NULL,
    arrival_time TIME NOT NULL,
    duration_minutes INTEGER NOT NULL,
    aircraft_type VARCHAR(50),
    economy_seats_available INTEGER DEFAULT 100,
    business_seats_available INTEGER DEFAULT 30,
    first_seats_available INTEGER DEFAULT 10,
    economy_price NUMERIC(10, 2) NOT NULL,
    business_price NUMERIC(10, 2),
    first_price NUMERIC(10, 2),
    status VARCHAR(20) DEFAULT 'scheduled',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Travel plans table
CREATE TABLE travel_plans (
    id INTEGER PRIMARY KEY,
    plan_id VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'draft',
    origin_city VARCHAR(10) NOT NULL,
    destinations TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    travelers INTEGER DEFAULT 1,
    budget NUMERIC(10, 2),
    preferences TEXT DEFAULT '{}',
    itinerary TEXT DEFAULT '{}',
    total_cost NUMERIC(10, 2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bookings table
CREATE TABLE bookings (
    booking_id INTEGER PRIMARY KEY,
    booking_reference VARCHAR(100) UNIQUE NOT NULL,
    booking_type VARCHAR(50) NOT NULL,
    plan_id VARCHAR(100),
    user_id VARCHAR(100),
    booking_data TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'confirmed',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes (all ASYNC as required by Aurora DSQL)
CREATE INDEX ASYNC idx_cities_name ON cities(name);
CREATE INDEX ASYNC idx_cities_country ON cities(country);

CREATE INDEX ASYNC idx_hotels_city_code ON hotels(city_code);
CREATE INDEX ASYNC idx_hotels_star_rating ON hotels(star_rating);

CREATE INDEX ASYNC idx_hotel_availability ON hotel_availability(hotel_id, date);

CREATE INDEX ASYNC idx_activities_city_code ON activities(city_code);
CREATE INDEX ASYNC idx_activities_category ON activities(category);

CREATE INDEX ASYNC idx_flight_routes_origin ON flight_routes(origin_code);
CREATE INDEX ASYNC idx_flight_routes_destination ON flight_routes(destination_code);

CREATE INDEX ASYNC idx_flights_route ON flights(origin_code, destination_code, departure_date);
CREATE INDEX ASYNC idx_flights_airline ON flights(airline_code);
CREATE INDEX ASYNC idx_flights_departure ON flights(departure_date, departure_time);

CREATE INDEX ASYNC idx_travel_plans_user_id ON travel_plans(user_id);
CREATE INDEX ASYNC idx_travel_plans_status ON travel_plans(status);

CREATE INDEX ASYNC idx_bookings_plan_id ON bookings(plan_id);
CREATE INDEX ASYNC idx_bookings_reference ON bookings(booking_reference);
CREATE INDEX ASYNC idx_bookings_type ON bookings(booking_type);
CREATE INDEX ASYNC idx_bookings_status ON bookings(status);