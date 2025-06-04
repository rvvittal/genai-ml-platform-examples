#!/usr/bin/env python3
"""Create Knowledge Base documents directly"""

import json
import os
from pathlib import Path
from datetime import datetime

# Destination data from populate_destinations.py
DESTINATIONS = [
    {
        'code': 'CDG',
        'name': 'Paris',
        'country': 'France',
        'continent': 'Europe',
        'latitude': 48.8566,
        'longitude': 2.3522,
        'description': 'The City of Light captivates with iconic landmarks, world-class art, exquisite cuisine, and timeless romance. From the Eiffel Tower to charming cafés, Paris offers unforgettable experiences.',
        'tags': ['romantic', 'cultural', 'art', 'gourmet', 'fashion', 'historic', 'museums', 'nightlife', 'shopping'],
        'best_for': ['couples', 'art lovers', 'food enthusiasts', 'fashionistas'],
        'highlights': ['Eiffel Tower', 'Louvre Museum', 'Notre-Dame', 'Champs-Élysées', 'Montmartre', 'Seine River']
    },
    {
        'code': 'NRT',
        'name': 'Tokyo',
        'country': 'Japan',
        'continent': 'Asia',
        'latitude': 35.6762,
        'longitude': 139.6503,
        'description': 'Ultra-modern metropolis where ancient traditions meet cutting-edge technology. Experience serene temples, bustling markets, innovative cuisine, and neon-lit streets.',
        'tags': ['modern', 'cultural', 'technology', 'gourmet', 'shopping', 'traditional', 'urban', 'anime'],
        'best_for': ['tech enthusiasts', 'foodies', 'culture seekers', 'shoppers'],
        'highlights': ['Senso-ji Temple', 'Shibuya Crossing', 'Mt. Fuji views', 'Tsukiji Market', 'Cherry blossoms']
    },
    {
        'code': 'DPS',
        'name': 'Bali',
        'country': 'Indonesia',
        'continent': 'Asia',
        'latitude': -8.4095,
        'longitude': 115.1889,
        'description': 'Island paradise offering pristine beaches, ancient temples, terraced rice fields, yoga retreats, and spiritual experiences. Perfect blend of relaxation and adventure.',
        'tags': ['beach', 'spiritual', 'romantic', 'nature', 'cultural', 'tropical', 'wellness', 'surfing'],
        'best_for': ['honeymooners', 'surfers', 'spiritual seekers', 'nature lovers'],
        'highlights': ['Uluwatu Temple', 'Ubud rice terraces', 'Seminyak beaches', 'Mount Batur', 'Tanah Lot']
    },
    {
        'code': 'NYC',
        'name': 'New York',
        'country': 'USA',
        'continent': 'North America',
        'latitude': 40.7128,
        'longitude': -74.0060,
        'description': 'The city that never sleeps offers world-class museums, Broadway shows, diverse neighborhoods, incredible dining, and iconic landmarks. The ultimate urban adventure.',
        'tags': ['urban', 'cultural', 'shopping', 'nightlife', 'museums', 'theater', 'business', 'diverse'],
        'best_for': ['urban enthusiasts', 'culture seekers', 'foodies', 'theater lovers'],
        'highlights': ['Statue of Liberty', 'Central Park', 'Times Square', 'Broadway', 'Metropolitan Museum']
    },
    {
        'code': 'SYD',
        'name': 'Sydney',
        'country': 'Australia',
        'continent': 'Oceania',
        'latitude': -33.8688,
        'longitude': 151.2093,
        'description': 'Harbor city featuring iconic Opera House, beautiful beaches, cosmopolitan culture, and outdoor lifestyle. Where urban sophistication meets beach culture.',
        'tags': ['beach', 'urban', 'harbor', 'outdoor', 'cosmopolitan', 'surfing', 'nature'],
        'best_for': ['beach lovers', 'urban explorers', 'outdoor enthusiasts', 'surfers'],
        'highlights': ['Opera House', 'Harbour Bridge', 'Bondi Beach', 'Blue Mountains', 'Darling Harbour']
    },
    {
        'code': 'CPT',
        'name': 'Cape Town',
        'country': 'South Africa',
        'continent': 'Africa',
        'latitude': -33.9249,
        'longitude': 18.4241,
        'description': 'Mother City where mountains meet ocean, offering world-class wine, diverse culture, stunning landscapes, and adventure activities in a cosmopolitan setting.',
        'tags': ['nature', 'beach', 'wine', 'adventure', 'cultural', 'scenic', 'outdoor'],
        'best_for': ['nature lovers', 'wine enthusiasts', 'adventure seekers', 'beach lovers'],
        'highlights': ['Table Mountain', 'Cape of Good Hope', 'V&A Waterfront', 'Robben Island', 'Wine estates']
    },
    {
        'code': 'GIG',
        'name': 'Rio de Janeiro',
        'country': 'Brazil',
        'continent': 'South America',
        'latitude': -22.9068,
        'longitude': -43.1729,
        'description': 'Marvelous city combining stunning beaches, samba rhythms, carnival celebrations, and dramatic mountain landscapes. Experience Brazilian passion and natural beauty.',
        'tags': ['beach', 'party', 'cultural', 'nature', 'carnival', 'music', 'outdoor'],
        'best_for': ['beach lovers', 'party enthusiasts', 'nature lovers', 'culture seekers'],
        'highlights': ['Christ the Redeemer', 'Copacabana Beach', 'Sugarloaf Mountain', 'Carnival', 'Ipanema']
    }
]

# Sample hotel data
HOTELS = [
    # Paris hotels
    {'city_code': 'CDG', 'name': 'Hotel des Grands Boulevards', 'star_rating': 4, 'price_min': 110, 'price_max': 145, 'amenities': ['WiFi', 'Restaurant', 'Bar'], 'description': 'Stylish boutique hotel in central Paris'},
    {'city_code': 'CDG', 'name': 'Le Marais Boutique', 'star_rating': 3, 'price_min': 85, 'price_max': 120, 'amenities': ['WiFi', 'Breakfast'], 'description': 'Charming hotel in the historic Marais district'},
    {'city_code': 'CDG', 'name': 'Ritz Paris', 'star_rating': 5, 'price_min': 800, 'price_max': 1200, 'amenities': ['Spa', 'Restaurant', 'Pool', 'Concierge'], 'description': 'Legendary luxury hotel on Place Vendôme'},
    
    # Tokyo hotels
    {'city_code': 'NRT', 'name': 'Park Hyatt Tokyo', 'star_rating': 5, 'price_min': 500, 'price_max': 800, 'amenities': ['Spa', 'Pool', 'Restaurant', 'Bar'], 'description': 'Luxury hotel featured in Lost in Translation'},
    {'city_code': 'NRT', 'name': 'Shinjuku Capsule Hotel', 'star_rating': 2, 'price_min': 30, 'price_max': 50, 'amenities': ['WiFi', 'Lounge'], 'description': 'Authentic Japanese capsule hotel experience'},
    
    # Bali hotels
    {'city_code': 'DPS', 'name': 'Alila Villas Uluwatu', 'star_rating': 5, 'price_min': 400, 'price_max': 600, 'amenities': ['Pool', 'Spa', 'Beach', 'Restaurant'], 'description': 'Clifftop luxury resort with ocean views'},
    {'city_code': 'DPS', 'name': 'Ubud Eco Lodge', 'star_rating': 3, 'price_min': 60, 'price_max': 90, 'amenities': ['Yoga', 'Organic Restaurant', 'Pool'], 'description': 'Sustainable retreat in rice paddies'},
    
    # NYC hotels
    {'city_code': 'NYC', 'name': 'The Plaza', 'star_rating': 5, 'price_min': 600, 'price_max': 1000, 'amenities': ['Spa', 'Restaurant', 'Concierge', 'Fitness'], 'description': 'Iconic luxury hotel on Fifth Avenue'},
    {'city_code': 'NYC', 'name': 'Pod Times Square', 'star_rating': 3, 'price_min': 100, 'price_max': 150, 'amenities': ['WiFi', 'Rooftop Bar'], 'description': 'Modern budget hotel in heart of Manhattan'},
    
    # Sydney hotels
    {'city_code': 'SYD', 'name': 'Park Hyatt Sydney', 'star_rating': 5, 'price_min': 450, 'price_max': 700, 'amenities': ['Spa', 'Harbor View', 'Restaurant'], 'description': 'Luxury hotel with Opera House views'},
    {'city_code': 'SYD', 'name': 'Bondi Beach House', 'star_rating': 3, 'price_min': 120, 'price_max': 180, 'amenities': ['Beach Access', 'WiFi'], 'description': 'Beachfront accommodation near Bondi'},
]

# Sample activities
ACTIVITIES = [
    # Paris activities
    {'city_code': 'CDG', 'name': 'Eiffel Tower Skip-the-Line', 'type': 'Sightseeing', 'duration': 2, 'price': 35, 'description': 'Fast-track access to Paris icon'},
    {'city_code': 'CDG', 'name': 'Louvre Museum Tour', 'type': 'Cultural', 'duration': 3, 'price': 65, 'description': 'Guided tour of world-famous art museum'},
    {'city_code': 'CDG', 'name': 'Seine River Dinner Cruise', 'type': 'Dining', 'duration': 2.5, 'price': 120, 'description': 'Romantic dinner cruise with city views'},
    
    # Tokyo activities
    {'city_code': 'NRT', 'name': 'Tsukiji Fish Market Tour', 'type': 'Food', 'duration': 3, 'price': 80, 'description': 'Early morning market tour with sushi breakfast'},
    {'city_code': 'NRT', 'name': 'Mt. Fuji Day Trip', 'type': 'Nature', 'duration': 12, 'price': 150, 'description': 'Full day excursion to iconic mountain'},
    
    # Bali activities
    {'city_code': 'DPS', 'name': 'Ubud Rice Terrace Trek', 'type': 'Nature', 'duration': 4, 'price': 45, 'description': 'Guided walk through scenic rice paddies'},
    {'city_code': 'DPS', 'name': 'Surf Lesson Seminyak', 'type': 'Sport', 'duration': 2, 'price': 50, 'description': 'Beginner-friendly surf instruction'},
]


def create_destination_documents():
    """Create individual documents for each destination."""
    output_dir = Path("kb_data/destinations")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📍 Creating {len(DESTINATIONS)} destination documents...")
    
    for dest in DESTINATIONS:
        # Create rich content for better semantic search
        content = f"""# {dest['name']}, {dest['country']}

## Overview
{dest['description']}

## Destination Details
- **Location**: {dest['continent']}
- **Coordinates**: {dest['latitude']}, {dest['longitude']}
- **Airport Code**: {dest['code']}

## What Makes {dest['name']} Special
This destination is perfect for {', '.join(dest['best_for'])}. 
Known for its {', '.join(dest['tags'][:3])} atmosphere.

## Top Attractions
{chr(10).join(f'- {highlight}' for highlight in dest['highlights'])}

## Travel Style Tags
{', '.join(dest['tags'])}

## Best For
{', '.join(dest['best_for'])}
"""
        
        # Create document
        doc = {
            "documentId": f"destination-{dest['code'].lower()}",
            "title": f"{dest['name']}, {dest['country']} - Travel Destination",
            "content": {"text": content},
            "contentType": "text/plain",
            "metadata": {
                "type": "destination",
                "code": dest['code'],
                "name": dest['name'],
                "country": dest['country'],
                "continent": dest['continent'],
                "tags": dest['tags'],
                "latitude": dest['latitude'],
                "longitude": dest['longitude']
            }
        }
        
        # Save document
        filename = output_dir / f"{dest['code'].lower()}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
        
        print(f"  ✅ {dest['name']}")
    
    print(f"✅ Created {len(DESTINATIONS)} destination documents")


def create_hotel_documents():
    """Create individual documents for each hotel."""
    output_dir = Path("kb_data/hotels")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n🏨 Creating {len(HOTELS)} hotel documents...")
    
    # Get destination names for context
    dest_map = {d['code']: d for d in DESTINATIONS}
    
    for i, hotel in enumerate(HOTELS):
        dest = dest_map.get(hotel['city_code'], {})
        city_name = dest.get('name', hotel['city_code'])
        country = dest.get('country', 'Unknown')
        
        # Create content
        content = f"""# {hotel['name']}

## Hotel Overview
{hotel['description']}

## Location
- **City**: {city_name}, {country}
- **Airport Code**: {hotel['city_code']}

## Accommodation Details
- **Star Rating**: {hotel['star_rating']} stars
- **Price Range**: ${hotel['price_min']} - ${hotel['price_max']} per night
- **Amenities**: {', '.join(hotel['amenities'])}

## Why Stay Here
{hotel['description']}. This {hotel['star_rating']}-star property offers excellent {'value' if hotel['star_rating'] <= 3 else 'luxury'} accommodation in {city_name}.

## Guest Amenities
{chr(10).join(f'- {amenity}' for amenity in hotel['amenities'])}
"""
        
        # Create document
        doc = {
            "documentId": f"hotel-{hotel['city_code'].lower()}-{i}",
            "title": f"{hotel['name']} - {city_name} Hotel",
            "content": {"text": content},
            "contentType": "text/plain",
            "metadata": {
                "type": "hotel",
                "city_code": hotel['city_code'],
                "city_name": city_name,
                "name": hotel['name'],
                "star_rating": hotel['star_rating'],
                "price_min": hotel['price_min'],
                "price_max": hotel['price_max'],
                "amenities": hotel['amenities']
            }
        }
        
        # Save document
        filename = output_dir / f"{hotel['city_code'].lower()}_{hotel['name'].lower().replace(' ', '_')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
        
        print(f"  ✅ {hotel['name']} ({city_name})")
    
    print(f"✅ Created {len(HOTELS)} hotel documents")


def create_activity_documents():
    """Create individual documents for each activity."""
    output_dir = Path("kb_data/activities")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n🎭 Creating {len(ACTIVITIES)} activity documents...")
    
    # Get destination names for context
    dest_map = {d['code']: d for d in DESTINATIONS}
    
    for i, activity in enumerate(ACTIVITIES):
        dest = dest_map.get(activity['city_code'], {})
        city_name = dest.get('name', activity['city_code'])
        country = dest.get('country', 'Unknown')
        
        # Create content
        content = f"""# {activity['name']}

## Activity Overview
{activity['description']}

## Location
- **City**: {city_name}, {country}
- **Destination Code**: {activity['city_code']}

## Activity Details
- **Type**: {activity['type']}
- **Duration**: {activity['duration']} hours
- **Price**: ${activity['price']} per person

## What to Expect
{activity['description']}. This {activity['type'].lower()} experience takes approximately {activity['duration']} hours and is suitable for most travelers visiting {city_name}.

## Booking Information
- **Duration**: {activity['duration']} hours
- **Price**: ${activity['price']} per person
- **Category**: {activity['type']}
"""
        
        # Create document
        doc = {
            "documentId": f"activity-{activity['city_code'].lower()}-{i}",
            "title": f"{activity['name']} - {city_name} Activity",
            "content": {"text": content},
            "contentType": "text/plain",
            "metadata": {
                "type": "activity",
                "city_code": activity['city_code'],
                "city_name": city_name,
                "name": activity['name'],
                "activity_type": activity['type'],
                "duration_hours": activity['duration'],
                "price_per_person": activity['price']
            }
        }
        
        # Save document
        filename = output_dir / f"{activity['city_code'].lower()}_{activity['name'].lower().replace(' ', '_')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
        
        print(f"  ✅ {activity['name']} ({city_name})")
    
    print(f"✅ Created {len(ACTIVITIES)} activity documents")


def create_metadata():
    """Create metadata file for the Knowledge Base."""
    metadata = {
        "version": "1.0",
        "created_at": datetime.now().isoformat(),
        "description": "Travel planner Knowledge Base documents",
        "statistics": {
            "destinations": len(DESTINATIONS),
            "hotels": len(HOTELS),
            "activities": len(ACTIVITIES),
            "total_documents": len(DESTINATIONS) + len(HOTELS) + len(ACTIVITIES)
        },
        "document_types": {
            "destination": "Travel destination information",
            "hotel": "Hotel accommodation details",
            "activity": "Activities and experiences"
        }
    }
    
    with open("kb_data/metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n📋 Created metadata file")


def main():
    """Create all Knowledge Base documents."""
    print("🚀 Creating Knowledge Base Documents")
    print("=" * 50)
    
    # Create all document types
    create_destination_documents()
    create_hotel_documents()
    create_activity_documents()
    create_metadata()
    
    print("\n✨ Knowledge Base documents created successfully!")
    print(f"📁 Output directory: {Path('kb_data').absolute()}")
    print("\nNext steps:")
    print("1. Deploy the CDK Knowledge Base stack")
    print("2. Upload kb_data/* to the S3 bucket")
    print("3. Start Knowledge Base ingestion")


if __name__ == "__main__":
    main()