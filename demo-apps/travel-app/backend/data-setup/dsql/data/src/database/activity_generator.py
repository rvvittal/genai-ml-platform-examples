"""Generate activity data for demo cities."""

import sqlite3
import json
import os
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class ActivityDataGenerator:
    """Generate realistic activity data for travel destinations."""
    
    # Activity templates by category
    ACTIVITY_TEMPLATES = {
        'sightseeing': [
            {
                'name': '{city} Landmarks Tour',
                'description': 'Explore the most iconic landmarks and monuments of {city} with an expert guide',
                'duration_hours': 3.5,
                'price_adult': 65,
                'price_child': 35,
                'tags': ['guided', 'walking', 'photography', 'landmarks'],
                'includes': ['Professional guide', 'Entrance fees', 'Audio headset'],
                'available_days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                'time_slots': ['09:00', '14:00']
            },
            {
                'name': 'Hop-on Hop-off Bus Tour',
                'description': 'See {city} at your own pace with a flexible bus tour covering all major attractions',
                'duration_hours': 24,  # 24-hour ticket
                'price_adult': 45,
                'price_child': 25,
                'tags': ['flexible', 'family-friendly', 'audio-guide'],
                'includes': ['24-hour ticket', 'Audio guide in 15 languages', 'Free WiFi'],
                'available_days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                'time_slots': ['09:00']
            }
        ],
        'cultural': [
            {
                'name': '{city} Museum Pass',
                'description': 'Skip the lines at major museums and galleries in {city}',
                'duration_hours': 48,  # 2-day pass
                'price_adult': 75,
                'price_child': 0,  # Free for children
                'tags': ['museums', 'art', 'history', 'skip-the-line'],
                'includes': ['Access to 30+ museums', 'Skip-the-line entry', 'Digital guide app'],
                'available_days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                'time_slots': ['10:00']
            },
            {
                'name': 'Local Art Gallery Walking Tour',
                'description': 'Discover contemporary art scene with visits to hidden galleries and artist studios',
                'duration_hours': 3,
                'price_adult': 55,
                'price_child': 30,
                'tags': ['art', 'walking', 'local', 'contemporary'],
                'includes': ['Expert art guide', 'Gallery entries', 'Welcome drink'],
                'available_days': ['Wed', 'Thu', 'Fri', 'Sat'],
                'time_slots': ['11:00', '15:00']
            }
        ],
        'dining': [
            {
                'name': '{city} Food Tour',
                'description': 'Taste your way through {city} with stops at local markets and eateries',
                'duration_hours': 3.5,
                'price_adult': 85,
                'price_child': 45,
                'tags': ['food', 'walking', 'local', 'tasting'],
                'includes': ['6-8 food tastings', 'Local guide', 'One drink pairing'],
                'available_days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
                'time_slots': ['10:30', '18:00']
            },
            {
                'name': 'Cooking Class with Market Visit',
                'description': 'Shop for ingredients at local market then cook traditional dishes',
                'duration_hours': 4,
                'price_adult': 120,
                'price_child': 60,
                'tags': ['cooking', 'hands-on', 'market', 'cultural'],
                'includes': ['Market tour', 'All ingredients', 'Recipe booklet', 'Wine pairing'],
                'available_days': ['Tue', 'Thu', 'Sat'],
                'time_slots': ['09:30', '16:00']
            }
        ],
        'romantic': [
            {
                'name': 'Sunset River Cruise',
                'description': 'Romantic evening cruise with champagne and live music',
                'duration_hours': 2,
                'price_adult': 95,
                'price_child': 50,
                'tags': ['romantic', 'sunset', 'cruise', 'champagne'],
                'includes': ['Welcome champagne', 'Live music', 'Light appetizers'],
                'available_days': ['Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                'time_slots': ['18:30', '19:30']  # Adjusted for sunset
            },
            {
                'name': 'Private Wine Tasting Experience',
                'description': 'Exclusive wine tasting in historic cellar with sommelier',
                'duration_hours': 2.5,
                'price_adult': 150,
                'price_child': 0,  # Adults only
                'tags': ['romantic', 'wine', 'exclusive', 'intimate'],
                'includes': ['5 premium wines', 'Cheese pairing', 'Private sommelier'],
                'available_days': ['Thu', 'Fri', 'Sat'],
                'time_slots': ['16:00', '19:00']
            }
        ],
        'adventure': [
            {
                'name': '{city} Bike Tour',
                'description': 'Explore {city} on two wheels with stops at major sights and hidden gems',
                'duration_hours': 3,
                'price_adult': 45,
                'price_child': 25,
                'tags': ['active', 'outdoor', 'eco-friendly', 'guided'],
                'includes': ['Bike rental', 'Helmet', 'Local guide', 'Water bottle'],
                'available_days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                'time_slots': ['09:00', '14:30']
            },
            {
                'name': 'Day Trip Adventure',
                'description': 'Escape the city for hiking, swimming, or adventure activities',
                'duration_hours': 8,
                'price_adult': 125,
                'price_child': 75,
                'tags': ['outdoor', 'nature', 'full-day', 'adventure'],
                'includes': ['Transport', 'Guide', 'Lunch', 'Equipment'],
                'available_days': ['Tue', 'Thu', 'Sat', 'Sun'],
                'time_slots': ['08:00']
            }
        ]
    }
    
    # City-specific activities
    CITY_SPECIFIC = {
        'CDG': [  # Paris
            {
                'name': 'Eiffel Tower Skip-the-Line & Summit',
                'category': 'sightseeing',
                'description': 'Skip the lines and ascend to the summit of the Eiffel Tower',
                'duration_hours': 2,
                'price_adult': 85,
                'price_child': 45,
                'tags': ['iconic', 'skip-the-line', 'views', 'must-see'],
                'includes': ['Skip-the-line tickets', 'Summit access', 'Audio guide'],
                'available_days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                'time_slots': ['09:30', '14:00', '19:00']
            },
            {
                'name': 'Louvre Museum Guided Tour',
                'category': 'cultural',
                'description': 'Expert-led tour of the Louvre highlights including Mona Lisa',
                'duration_hours': 3,
                'price_adult': 75,
                'price_child': 35,
                'tags': ['art', 'history', 'guided', 'skip-the-line'],
                'includes': ['Skip-the-line entry', 'Expert guide', 'Headsets'],
                'available_days': ['Mon', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                'time_slots': ['10:00', '14:30']
            },
            {
                'name': 'Seine River Dinner Cruise',
                'category': 'romantic',
                'description': 'Elegant dinner cruise past illuminated Paris landmarks',
                'duration_hours': 2.5,
                'price_adult': 145,
                'price_child': 75,
                'tags': ['romantic', 'dinner', 'cruise', 'night'],
                'includes': ['3-course dinner', 'Wine pairing', 'Live music'],
                'available_days': ['Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                'time_slots': ['20:00']
            }
        ],
        'FCO': [  # Rome
            {
                'name': 'Colosseum & Roman Forum Tour',
                'category': 'sightseeing',
                'description': 'Skip-the-line tour of ancient Rome\'s most famous sites',
                'duration_hours': 3,
                'price_adult': 65,
                'price_child': 35,
                'tags': ['history', 'ancient', 'skip-the-line', 'guided'],
                'includes': ['Skip-the-line tickets', 'Expert guide', 'Headsets'],
                'available_days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                'time_slots': ['09:00', '13:30']
            },
            {
                'name': 'Vatican Museums & Sistine Chapel',
                'category': 'cultural',
                'description': 'Early access tour of Vatican treasures before the crowds',
                'duration_hours': 3.5,
                'price_adult': 95,
                'price_child': 50,
                'tags': ['art', 'religious', 'early-access', 'must-see'],
                'includes': ['Early access', 'Expert guide', 'St. Peter\'s Basilica'],
                'available_days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
                'time_slots': ['07:45']
            }
        ],
        'DPS': [  # Bali
            {
                'name': 'Sunrise Mount Batur Trek',
                'category': 'adventure',
                'description': 'Trek to summit of active volcano for spectacular sunrise views',
                'duration_hours': 6,
                'price_adult': 65,
                'price_child': 45,
                'tags': ['hiking', 'sunrise', 'nature', 'challenging'],
                'includes': ['Guide', 'Breakfast', 'Flashlight', 'Transport'],
                'available_days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                'time_slots': ['02:00']  # Early morning start
            },
            {
                'name': 'Traditional Balinese Spa Day',
                'category': 'romantic',
                'description': 'Full day of relaxation with traditional treatments',
                'duration_hours': 5,
                'price_adult': 120,
                'price_child': 0,  # Adults only
                'tags': ['spa', 'wellness', 'relaxation', 'traditional'],
                'includes': ['Multiple treatments', 'Healthy lunch', 'Herbal teas'],
                'available_days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                'time_slots': ['10:00', '14:00']
            }
        ],
        'NRT': [  # Tokyo
            {
                'name': 'Tsukiji Market & Sushi Making',
                'category': 'dining',
                'description': 'Tour famous market then learn to make sushi from master chef',
                'duration_hours': 4,
                'price_adult': 135,
                'price_child': 70,
                'tags': ['food', 'hands-on', 'cultural', 'market'],
                'includes': ['Market tour', 'All ingredients', 'Sushi lunch', 'Certificate'],
                'available_days': ['Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
                'time_slots': ['09:00']
            },
            {
                'name': 'Tokyo Night Tour',
                'category': 'sightseeing',
                'description': 'Experience Tokyo\'s neon-lit districts and hidden izakayas',
                'duration_hours': 4,
                'price_adult': 95,
                'price_child': 50,
                'tags': ['nightlife', 'food', 'local', 'walking'],
                'includes': ['Local guide', '3 food stops', '1 drink', 'Train tickets'],
                'available_days': ['Wed', 'Thu', 'Fri', 'Sat'],
                'time_slots': ['18:00']
            }
        ]
    }
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    def _get_connection(self):
        """Get database connection."""
        return sqlite3.connect(self.db_path)
        
    def generate_activities(self):
        """Generate activities for all cities."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get all cities
        cursor.execute("SELECT code, name FROM cities")
        cities = cursor.fetchall()
        
        activities_count = 0
        
        for city_code, city_name in cities:
            # Add general activities for each category
            for category, templates in self.ACTIVITY_TEMPLATES.items():
                for template in templates:
                    activity = {
                        'name': template['name'].replace('{city}', city_name),
                        'city_code': city_code,
                        'category': category,
                        'description': template['description'].replace('{city}', city_name),
                        'duration_hours': template['duration_hours'],
                        'price_adult': template['price_adult'],
                        'price_child': template['price_child'],
                        'tags': json.dumps(template['tags']),
                        'includes': json.dumps(template['includes']),
                        'available_days': json.dumps(template['available_days']),
                        'time_slots': json.dumps(template['time_slots']),
                        'meeting_point': f"{city_name} city center"
                    }
                    
                    cursor.execute("""
                        INSERT INTO activities (
                            name, city_code, category, description, duration_hours,
                            price_adult, price_child, tags, includes, available_days,
                            time_slots, meeting_point
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        activity['name'], activity['city_code'], activity['category'],
                        activity['description'], activity['duration_hours'],
                        activity['price_adult'], activity['price_child'],
                        activity['tags'], activity['includes'], activity['available_days'],
                        activity['time_slots'], activity['meeting_point']
                    ))
                    activities_count += 1
            
            # Add city-specific activities
            if city_code in self.CITY_SPECIFIC:
                for activity_data in self.CITY_SPECIFIC[city_code]:
                    cursor.execute("""
                        INSERT INTO activities (
                            name, city_code, category, description, duration_hours,
                            price_adult, price_child, tags, includes, available_days,
                            time_slots, meeting_point
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        activity_data['name'], city_code, activity_data['category'],
                        activity_data['description'], activity_data['duration_hours'],
                        activity_data['price_adult'], activity_data['price_child'],
                        json.dumps(activity_data['tags']), json.dumps(activity_data['includes']),
                        json.dumps(activity_data['available_days']), json.dumps(activity_data['time_slots']),
                        activity_data.get('meeting_point', f"{city_name} city center")
                    ))
                    activities_count += 1
        
        conn.commit()
        conn.close()
        
        logger.info(f"Generated {activities_count} activities for {len(cities)} cities")
        return activities_count


def main():
    """Generate activity data."""
    db_path = os.path.join(os.path.dirname(__file__), 'travel_demo.db')
    
    generator = ActivityDataGenerator(db_path)
    count = generator.generate_activities()
    
    print(f"✅ Generated {count} activities")
    
    # Verify data
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Show sample activities
    cursor.execute("""
        SELECT a.name, a.category, c.name as city, a.price_adult
        FROM activities a
        JOIN cities c ON a.city_code = c.code
        LIMIT 10
    """)
    
    print("\nSample activities:")
    for row in cursor.fetchall():
        print(f"  - {row[0]} ({row[1]}) in {row[2]} - ${row[3]}")
    
    conn.close()


if __name__ == "__main__":
    main()