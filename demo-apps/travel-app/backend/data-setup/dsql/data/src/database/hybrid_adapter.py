"""Hybrid database adapter for smooth migration from SQLite to Aurora DSQL."""

import os
import sqlite3
import psycopg2
import psycopg2.extras
from typing import Any, List, Tuple, Optional, Dict, Union
from contextlib import contextmanager
import json
import logging

logger = logging.getLogger(__name__)

class HybridDatabaseAdapter:
    """Adapter that can work with both SQLite and DSQL."""
    
    def __init__(self, use_dsql: bool = None):
        """Initialize adapter with database selection."""
        if use_dsql:
            self.use_dsql = use_dsql
        else:
            self.use_dsql = False
            
        logger.info(f"HybridDatabaseAdapter initialized - Using {'DSQL' if self.use_dsql else 'SQLite'}")
        
    @contextmanager
    def get_connection(self):
        """Get database connection based on configuration."""
        connection_method = os.environ.get('DSQL_CONNECTION_METHOD', 'direct')
        
        if connection_method == 'iam':
            # Use IAM authentication (recommended for DSQL)
            from test_framework.dsql_iam_connection import DSQLIAMConnection
            manager = DSQLIAMConnection()
            conn_params = manager.get_connection_params()
            conn = psycopg2.connect(
                **conn_params,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            logger.debug("Connected to DSQL via IAM authentication")
        else:
            # Direct connection (when running in VPC)
            conn = psycopg2.connect(
                host=os.environ.get('DSQL_ENDPOINT', 'localhost'),
                port=5432,
                database='postgres',
                user=os.environ.get('DSQL_USER', 'postgres'),
                password=os.environ.get('DSQL_PASSWORD'),
                sslmode='require' if not os.environ.get('DSQL_LOCAL_TEST') else 'prefer',
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            logger.debug("Connected to DSQL directly")
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: Union[Tuple, Dict] = None) -> List[Dict[str, Any]]:
        """Execute a query with automatic SQL dialect handling."""
        # Convert SQL syntax if needed
        if self.use_dsql:
            query, params = self._sqlite_to_postgresql(query, params)
        else:
            query, params = self._postgresql_to_sqlite(query, params)
        
        logger.debug(f"Executing query: {query[:100]}...")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Only fetch results for SELECT queries
            query_lower = query.strip().lower()
            if query_lower.startswith('select') or 'returning' in query_lower:
                if hasattr(cursor, 'fetchall'):
                    rows = cursor.fetchall()
                    
                    # Convert to list of dicts
                    if self.use_dsql:
                        # psycopg2 with RealDictCursor returns dicts
                        return [dict(row) for row in rows]
                    else:
                        # SQLite with Row factory
                        return [dict(row) for row in rows]
            return []
    
    def execute_many(self, query: str, params_list: List[Union[Tuple, Dict]]) -> None:
        """Execute many queries (for bulk inserts)."""
        if self.use_dsql:
            query, _ = self._sqlite_to_postgresql(query, None)
        else:
            query, _ = self._postgresql_to_sqlite(query, None)
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
    
    def _sqlite_to_postgresql(self, query: str, params: Union[Tuple, Dict]) -> Tuple[str, Union[Tuple, Dict]]:
        """Convert SQLite syntax to PostgreSQL."""
        # Handle parameter placeholders
        if isinstance(params, tuple):
            # Convert ? to %s for positional parameters
            param_count = query.count('?')
            for i in range(param_count):
                query = query.replace('?', '%s', 1)
        
        # Convert data types
        query = query.replace(' TEXT', ' VARCHAR(255)')
        query = query.replace(' REAL', ' NUMERIC')
        query = query.replace(' INTEGER PRIMARY KEY AUTOINCREMENT', ' SERIAL PRIMARY KEY')
        
        # Handle JSON operations
        query = query.replace('json_extract(', 'jsonb_extract_path_text(')
        query = query.replace("json_array_length(", "jsonb_array_length(")
        
        # Handle string concatenation
        query = query.replace(' || ', ' || ')  # PostgreSQL uses same operator
        
        # Handle JSONB casting for parameters
        if '::jsonb' not in query and params:
            # Auto-detect JSON parameters and add casting
            if isinstance(params, tuple):
                new_params = []
                for i, param in enumerate(params):
                    if isinstance(param, (dict, list)):
                        # Find the parameter position in query
                        param_positions = [j for j, c in enumerate(query) if c == '%']
                        if i < len(param_positions):
                            # Add ::jsonb casting after the parameter
                            pos = param_positions[i] + 2  # After %s
                            query = query[:pos] + '::jsonb' + query[pos:]
                        new_params.append(json.dumps(param))
                    else:
                        new_params.append(param)
                params = tuple(new_params)
        
        return query, params
    
    def _postgresql_to_sqlite(self, query: str, params: Union[Tuple, Dict]) -> Tuple[str, Union[Tuple, Dict]]:
        """Convert PostgreSQL syntax to SQLite."""
        # Handle parameter placeholders
        if isinstance(params, tuple):
            # Convert %s to ? for positional parameters
            param_count = query.count('%s')
            for i in range(param_count):
                query = query.replace('%s', '?', 1)
        
        # Remove PostgreSQL-specific casting
        query = query.replace('::jsonb', '')
        query = query.replace('::json', '')
        query = query.replace('::text', '')
        query = query.replace('::integer', '')
        
        # Convert data types
        query = query.replace(' VARCHAR(255)', ' TEXT')
        query = query.replace(' VARCHAR', ' TEXT')
        query = query.replace(' NUMERIC', ' REAL')
        query = query.replace(' SERIAL PRIMARY KEY', ' INTEGER PRIMARY KEY AUTOINCREMENT')
        query = query.replace(' TIMESTAMPTZ', ' TIMESTAMP')
        
        # Handle JSON operations
        query = query.replace('jsonb_extract_path_text(', 'json_extract(')
        query = query.replace('jsonb_array_length(', 'json_array_length(')
        
        # Handle NOW()
        query = query.replace('NOW()', "datetime('now')")
        query = query.replace('CURRENT_TIMESTAMP', "datetime('now')")
        
        # Convert JSON parameters back to strings for SQLite
        if params and isinstance(params, tuple):
            new_params = []
            for param in params:
                if isinstance(param, (dict, list)):
                    new_params.append(json.dumps(param))
                else:
                    new_params.append(param)
            params = tuple(new_params)
        
        return query, params
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        if self.use_dsql:
            query = """
                SELECT EXISTS (
                    SELECT FROM pg_tables
                    WHERE schemaname = 'public'
                    AND tablename = %s
                )
            """
            result = self.execute_query(query, (table_name,))
            return result[0]['exists'] if result else False
        else:
            query = """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?
            """
            result = self.execute_query(query, (table_name,))
            return len(result) > 0
    
    def get_table_count(self, table_name: str) -> int:
        """Get row count for a table."""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.execute_query(query)
        return result[0]['count'] if result else 0


class DatabaseManager:
    """Database manager using hybrid adapter for travel planner."""
    
    def __init__(self, use_dsql: Optional[bool] = None):
        self.adapter = HybridDatabaseAdapter(use_dsql)
    
    def get_city(self, city_code: str) -> Optional[Dict[str, Any]]:
        """Get city information."""
        query = "SELECT * FROM cities WHERE code = ? OR LOWER(name) = LOWER(?)"
        results = self.adapter.execute_query(query, (city_code, city_code))
        
        if results:
            city = results[0]
            # Parse JSON fields if they're strings
            if isinstance(city.get('tags'), str):
                city['tags'] = json.loads(city['tags'])
            return city
        return None
    
    def search_cities(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search cities by name or country."""
        query = """
            SELECT * FROM cities 
            WHERE LOWER(name) LIKE LOWER(?)
               OR LOWER(country) LIKE LOWER(?)
            LIMIT ?
        """
        search_pattern = f"%{search_term}%"
        results = self.adapter.execute_query(
            query, 
            (search_pattern, search_pattern, limit)
        )
        
        # Parse JSON fields
        for city in results:
            if isinstance(city.get('tags'), str):
                city['tags'] = json.loads(city['tags'])
        
        return results
    
    def get_hotels_in_city(self, city_code: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get hotels in a specific city."""
        query = """
            SELECT * FROM hotels
            WHERE city_code = ?
            ORDER BY star_rating DESC, base_price_min ASC
            LIMIT ?
        """
        results = self.adapter.execute_query(query, (city_code, limit))
        
        # Parse JSON fields
        for hotel in results:
            for field in ['amenities', 'room_types', 'tags']:
                if isinstance(hotel.get(field), str):
                    hotel[field] = json.loads(hotel[field])
        
        return results
    
    def get_activities_in_city(self, city_code: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get activities in a specific city."""
        if category:
            query = """
                SELECT * FROM activities
                WHERE city_code = ? AND category = ?
                ORDER BY rating DESC
            """
            params = (city_code, category)
        else:
            query = """
                SELECT * FROM activities
                WHERE city_code = ?
                ORDER BY rating DESC
            """
            params = (city_code,)
        
        results = self.adapter.execute_query(query, params)
        
        # Parse JSON fields
        for activity in results:
            for field in ['tags', 'includes', 'available_days', 'time_slots']:
                if isinstance(activity.get(field), str):
                    activity[field] = json.loads(activity[field])
        
        return results
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            query = "SELECT 1 as test"
            result = self.adapter.execute_query(query)
            return len(result) > 0 and result[0]['test'] == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False