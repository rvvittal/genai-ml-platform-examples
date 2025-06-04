"""AWS Knowledge Base adapter for destination search."""

import boto3
import json
import logging
from typing import List, Dict, Any, Optional
import os
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class KnowledgeBaseAdapter:
    """Adapter for AWS Knowledge Base queries."""
    
    def __init__(self, knowledge_base_id: Optional[str] = None):
        """Initialize the Knowledge Base adapter.
        
        Args:
            knowledge_base_id: Knowledge Base ID. If not provided, uses environment variable.
        """
        self.kb_id = knowledge_base_id or os.environ.get('KNOWLEDGE_BASE_ID')
        if not self.kb_id:
            raise ValueError("Knowledge Base ID not provided")
        
        # Initialize Bedrock Runtime client
        self.bedrock_runtime = boto3.client(
            'bedrock-agent-runtime',
            region_name=os.environ.get('AWS_REGION', 'us-west-2')
        )
        
        logger.info(f"Initialized Knowledge Base adapter with ID: {self.kb_id}")
    
    async def search_destinations(
        self,
        query: str,
        max_results: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for destinations using Knowledge Base.
        
        Args:
            query: Natural language search query
            max_results: Maximum number of results to return
            filters: Optional filters (e.g., continent, tags)
            
        Returns:
            List of matching destinations with relevance scores
        """
        try:
            # Build retrieval configuration
            retrieval_config = {
                'vectorSearchConfiguration': {
                    'numberOfResults': max_results * 2,  # Get more to filter
                }
            }
            
            # Add filters if provided
            if filters:
                filter_expressions = []
                if 'continent' in filters:
                    filter_expressions.append(f"continent = '{filters['continent']}'")
                if 'tags' in filters and isinstance(filters['tags'], list):
                    for tag in filters['tags']:
                        filter_expressions.append(f"'{tag}' in tags")
                
                if filter_expressions:
                    retrieval_config['vectorSearchConfiguration']['filter'] = {
                        'andAll': [{'equals': expr} for expr in filter_expressions]
                    }
            
            # Query Knowledge Base
            response = self.bedrock_runtime.retrieve(
                knowledgeBaseId=self.kb_id,
                retrievalQuery={
                    'text': query
                },
                retrievalConfiguration=retrieval_config
            )
            
            # Process results
            destinations = []
            seen_codes = set()
            
            for result in response.get('retrievalResults', []):
                metadata = result.get('metadata', {})
                
                # Skip if not a destination document or already seen
                if not metadata.get('code') or metadata['code'] in seen_codes:
                    continue
                
                seen_codes.add(metadata['code'])
                
                # Extract destination info
                destination = {
                    'code': metadata['code'],
                    'name': metadata.get('name', ''),
                    'country': metadata.get('country', ''),
                    'continent': metadata.get('continent', ''),
                    'description': self._extract_description(result.get('content', {}).get('text', '')),
                    'tags': metadata.get('tags', []),
                    'latitude': metadata.get('latitude', 0),
                    'longitude': metadata.get('longitude', 0),
                    'relevance_score': result.get('score', 0),
                    'match_reason': self._generate_match_reason(query, metadata, result)
                }
                
                destinations.append(destination)
                
                if len(destinations) >= max_results:
                    break
            
            # Sort by relevance score
            destinations.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            logger.info(f"Found {len(destinations)} destinations for query: {query}")
            return destinations
            
        except ClientError as e:
            logger.error(f"AWS error searching destinations: {e}")
            return []
        except Exception as e:
            logger.error(f"Error searching destinations: {e}")
            return []
    
    async def find_destinations_by_style(
        self,
        travel_style: str,
        preferences: Dict[str, Any],
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Find destinations matching a travel style and preferences.
        
        Args:
            travel_style: Travel style (e.g., "romantic", "adventure", "luxury")
            preferences: User preferences dictionary
            max_results: Maximum number of results
            
        Returns:
            List of matching destinations
        """
        # Build enhanced query
        query_parts = [f"{travel_style} travel destination"]
        
        if preferences.get('interests'):
            query_parts.append(f"with {', '.join(preferences['interests'])}")
        
        if preferences.get('climate'):
            query_parts.append(f"in {preferences['climate']} climate")
        
        if preferences.get('activities'):
            query_parts.append(f"for {', '.join(preferences['activities'])}")
        
        enhanced_query = ' '.join(query_parts)
        
        # Add filters based on preferences
        filters = {}
        if preferences.get('continent'):
            filters['continent'] = preferences['continent']
        
        return await self.search_destinations(enhanced_query, max_results, filters)
    
    async def get_hotel_recommendations(
        self,
        city_code: str,
        preferences: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get hotel recommendations for a city.
        
        Args:
            city_code: City code (e.g., 'CDG' for Paris)
            preferences: Optional hotel preferences
            
        Returns:
            List of recommended hotels
        """
        query = f"hotels in city code {city_code}"
        
        if preferences:
            if preferences.get('star_rating'):
                query += f" {preferences['star_rating']} star"
            if preferences.get('amenities'):
                query += f" with {', '.join(preferences['amenities'])}"
            if preferences.get('budget'):
                query += f" under ${preferences['budget']} per night"
        
        try:
            response = self.bedrock_runtime.retrieve(
                knowledgeBaseId=self.kb_id,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 10,
                        'filter': {
                            'equals': {
                                'key': 'city_code',
                                'value': city_code
                            }
                        }
                    }
                }
            )
            
            # Process hotel results
            hotels = []
            for result in response.get('retrievalResults', []):
                content = result.get('content', {}).get('text', '')
                metadata = result.get('metadata', {})
                
                # Extract hotel information from content
                hotels_data = self._parse_hotel_content(content, metadata)
                hotels.extend(hotels_data)
            
            return hotels[:5]  # Return top 5
            
        except Exception as e:
            logger.error(f"Error getting hotel recommendations: {e}")
            return []
    
    async def get_activity_suggestions(
        self,
        city_code: str,
        interests: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get activity suggestions for a city.
        
        Args:
            city_code: City code
            interests: Optional list of interests
            
        Returns:
            List of suggested activities
        """
        query = f"activities and things to do in city code {city_code}"
        
        if interests:
            query += f" for people interested in {', '.join(interests)}"
        
        try:
            response = self.bedrock_runtime.retrieve(
                knowledgeBaseId=self.kb_id,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 10,
                        'filter': {
                            'equals': {
                                'key': 'city_code',
                                'value': city_code
                            }
                        }
                    }
                }
            )
            
            # Process activity results
            activities = []
            for result in response.get('retrievalResults', []):
                content = result.get('content', {}).get('text', '')
                metadata = result.get('metadata', {})
                
                # Extract activity information
                activities_data = self._parse_activity_content(content, metadata)
                activities.extend(activities_data)
            
            return activities[:5]  # Return top 5
            
        except Exception as e:
            logger.error(f"Error getting activity suggestions: {e}")
            return []
    
    def _extract_description(self, text: str) -> str:
        """Extract clean description from document text."""
        # Look for Overview section
        if "## Overview" in text:
            start = text.find("## Overview") + len("## Overview")
            end = text.find("##", start)
            if end == -1:
                end = text.find("\n\n", start)
            if end != -1:
                return text[start:end].strip()
        
        # Fallback to first paragraph
        lines = text.strip().split('\n')
        for line in lines:
            if line.strip() and not line.startswith('#'):
                return line.strip()
        
        return "A wonderful travel destination"
    
    def _generate_match_reason(self, query: str, metadata: Dict, result: Dict) -> str:
        """Generate explanation for why destination matched."""
        score = result.get('score', 0)
        
        if score > 0.9:
            return "Excellent match for your search"
        elif score > 0.7:
            tags = metadata.get('tags', [])
            matching_tags = [tag for tag in tags if tag.lower() in query.lower()]
            if matching_tags:
                return f"Great for {', '.join(matching_tags)}"
            return "Highly relevant to your interests"
        else:
            return f"Located in {metadata.get('continent', 'this region')}"
    
    def _parse_hotel_content(self, content: str, metadata: Dict) -> List[Dict[str, Any]]:
        """Parse hotel information from document content."""
        hotels = []
        
        # Simple parsing - in production, use more robust parsing
        lines = content.split('\n')
        current_hotel = None
        
        for line in lines:
            if line.startswith('### '):
                if current_hotel:
                    hotels.append(current_hotel)
                
                # Extract hotel name and rating
                name_part = line[4:].strip()
                if '(' in name_part and '⭐' in name_part:
                    name = name_part[:name_part.find('(')].strip()
                    rating = name_part[name_part.find('(')+1:name_part.find('⭐')]
                else:
                    name = name_part
                    rating = "0"
                
                current_hotel = {
                    'name': name,
                    'star_rating': int(rating) if rating.isdigit() else 0,
                    'city_code': metadata.get('city_code', ''),
                    'amenities': []
                }
            
            elif current_hotel and '**Price Range**:' in line:
                # Extract price range
                price_text = line.split(':', 1)[1].strip()
                prices = [p.strip() for p in price_text.split('-')]
                if len(prices) == 2:
                    current_hotel['price_min'] = int(prices[0].replace('$', '').split()[0])
                    current_hotel['price_max'] = int(prices[1].replace('$', '').split()[0])
            
            elif current_hotel and '**Amenities**:' in line:
                amenities_text = line.split(':', 1)[1].strip()
                current_hotel['amenities'] = [a.strip() for a in amenities_text.split(',')]
        
        if current_hotel:
            hotels.append(current_hotel)
        
        return hotels
    
    def _parse_activity_content(self, content: str, metadata: Dict) -> List[Dict[str, Any]]:
        """Parse activity information from document content."""
        activities = []
        
        lines = content.split('\n')
        current_activity = None
        
        for line in lines:
            if line.startswith('### '):
                if current_activity:
                    activities.append(current_activity)
                
                current_activity = {
                    'name': line[4:].strip(),
                    'city_code': metadata.get('city_code', ''),
                    'type': 'general',
                    'categories': []
                }
            
            elif current_activity:
                if '**Type**:' in line:
                    current_activity['type'] = line.split(':', 1)[1].strip()
                elif '**Duration**:' in line:
                    duration_text = line.split(':', 1)[1].strip()
                    current_activity['duration_hours'] = float(duration_text.split()[0])
                elif '**Price**:' in line:
                    price_text = line.split(':', 1)[1].strip()
                    current_activity['price'] = int(price_text.replace('$', '').split()[0])
                elif '**Rating**:' in line:
                    rating_text = line.split(':', 1)[1].strip()
                    current_activity['rating'] = float(rating_text.split('/')[0])
                elif '**Categories**:' in line:
                    cat_text = line.split(':', 1)[1].strip()
                    current_activity['categories'] = [c.strip() for c in cat_text.split(',')]
        
        if current_activity:
            activities.append(current_activity)
        
        return activities