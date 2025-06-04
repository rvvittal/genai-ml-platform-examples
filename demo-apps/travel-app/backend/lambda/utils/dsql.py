"""
DSQL connection management for Lambda
Uses IAM authentication for secure database access
"""

import os
import subprocess
import logging
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
import boto3

logger = logging.getLogger(__name__)

class DSQLConnection:
    """Manages DSQL connections with IAM authentication."""
    
    def __init__(self):
        self.endpoint = os.environ.get('DSQL_ENDPOINT')
        self.region = os.environ.get('KB_REGION', 'us-west-2')  # Use KB_REGION since AWS_REGION is reserved
        self.database = os.environ.get('DSQL_DATABASE', 'postgres')  # DSQL uses 'postgres' by default
        self.user = os.environ.get('DSQL_USER', 'admin')
        
        if not self.endpoint:
            logger.warning("DSQL_ENDPOINT not set, DSQL functionality will be limited")
            self.endpoint = None
        
    def _generate_auth_token(self) -> str:
        """Generate IAM auth token for DSQL."""
        try:
            # Primary method: Use DSQL client with boto3 >= 1.38.27
            dsql_client = boto3.client('dsql', region_name=self.region)
            
            # The DSQL client returns a string directly (not a dict)
            token = dsql_client.generate_db_connect_admin_auth_token(
                Hostname=self.endpoint,
                Region=self.region
            )
            
            logger.info(f"Generated DSQL auth token successfully (length: {len(token)})")
            return token
            
        except Exception as e:
            logger.error(f"Failed to generate DSQL auth token: {e}")
            # Fallback to RDS client method
            try:
                rds_client = boto3.client('rds', region_name=self.region) 
                token = rds_client.generate_db_auth_token(
                    DBHostname=self.endpoint,
                    Port=5432,
                    DBUsername=self.user,
                    Region=self.region
                )
                logger.info(f"Generated RDS auth token successfully (length: {len(token)})")
                return token
            except Exception as rds_error:
                logger.error(f"RDS auth fallback failed: {rds_error}")
                pass
            raise Exception(f"Could not generate auth token: {e}")
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with IAM authentication."""
        if not self.endpoint:
            raise Exception("DSQL_ENDPOINT not configured")
            
        auth_token = self._generate_auth_token()
        
        conn = psycopg2.connect(
            host=self.endpoint,
            port=5432,
            database=self.database,
            user=self.user,
            password=auth_token,
            sslmode='require',
            cursor_factory=RealDictCursor,
            connect_timeout=10
        )
        
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
    
    def execute_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        """Execute a query and return the first result."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchone()
    
    def execute_write(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount


# Global connection instance
try:
    dsql = DSQLConnection()
except Exception as e:
    logger.error(f"Failed to initialize DSQL connection: {e}")
    dsql = None


# Utility functions for common queries
def search_flights(origin: str, destination: str, date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search for flights between cities."""
    if not dsql:
        logger.warning("DSQL not available, returning empty result")
        return []
        
    # Updated query to match actual schema (flight routes table)
    query = """
        SELECT 
            fr.route_id as id,
            'Multiple' as flight_number,
            fr.airlines,
            c1.name as origin_city,
            c2.name as destination_city,
            fr.flight_duration_minutes,
            fr.distance_km
        FROM flight_routes fr
        JOIN cities c1 ON fr.origin_code = c1.code
        JOIN cities c2 ON fr.destination_code = c2.code
        WHERE c1.code = %s AND c2.code = %s
        LIMIT 10
    """
    
    try:
        return dsql.execute_query(query, (origin.upper(), destination.upper()))
    except Exception as e:
        logger.error(f"Error executing flight search query: {e}")
        return []


def search_hotels(city_code: str, check_in: Optional[str] = None, 
                  check_out: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search for hotels in a city."""
    if not dsql:
        logger.warning("DSQL not available, returning empty result")
        return []
        
    # Updated query to match actual schema (hotels table)
    query = """
        SELECT 
            h.hotel_id as id,
            h.name,
            h.description,
            h.star_rating,
            h.amenities,
            h.address,
            h.base_price_min,
            h.base_price_max,
            c.name as city_name
        FROM hotels h
        JOIN cities c ON h.city_code = c.code
        WHERE c.code = %s
        ORDER BY h.star_rating DESC
        LIMIT 20
    """
    
    try:
        return dsql.execute_query(query, (city_code.upper(),))
    except Exception as e:
        logger.error(f"Error executing hotel search query: {e}")
        return []


def search_activities(city_code: str, activity_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search for activities in a city."""
    if not dsql:
        logger.warning("DSQL not available, returning empty result")
        return []
        
    query = """
        SELECT 
            a.activity_id as id,
            a.name,
            a.description,
            a.category as activity_type,
            a.duration_hours,
            a.price_adult as base_price,
            a.rating,
            a.tags,
            c.name as city_name
        FROM activities a
        JOIN cities c ON a.city_code = c.code
        WHERE c.code = %s
    """
    
    params = [city_code.upper()]
    
    if activity_type:
        query += " AND a.activity_type = %s"
        params.append(activity_type)
    
    query += " ORDER BY a.price_adult LIMIT 20"
    
    try:
        return dsql.execute_query(query, tuple(params))
    except Exception as e:
        logger.error(f"Error executing activity search query: {e}")
        return []


def get_city_info(city_code: str) -> Optional[Dict[str, Any]]:
    """Get information about a city."""
    if not dsql:
        logger.warning("DSQL not available, returning None")
        return None
        
    query = """
        SELECT 
            id,
            code,
            name,
            country,
            description,
            tags,
            timezone,
            currency,
            language
        FROM cities
        WHERE code = %s
    """
    
    try:
        return dsql.execute_one(query, (city_code.upper(),))
    except Exception as e:
        logger.error(f"Error executing city info query: {e}")
        return None