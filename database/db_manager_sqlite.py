"""
SAP BW Process Chain Database Manager (SQLite)

This module provides database connection management, query execution,
and utility functions for the SQLite database with persistent data.
"""

import os
import sys
import sqlite3
import logging
from typing import Optional, List, Dict, Any, Union
from contextlib import contextmanager
from pathlib import Path

import pandas as pd  # type: ignore
from sqlalchemy import create_engine, text  # type: ignore
from sqlalchemy.orm import sessionmaker  # type: ignore

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    SQLite Database connection and query management for SAP BW Process Chain data
    Maintains same interface as PostgreSQL version for seamless migration
    """
    
    def __init__(self, 
                 db_path: str = "sap_bw_demo.db",
                 **kwargs):
        """
        Initialize SQLite database manager
        
        Args:
            db_path: Path to SQLite database file
            **kwargs: Ignored for compatibility with PostgreSQL version
        """
        self.db_path = Path(db_path)
        self.is_connected = False
        
        # For compatibility with PostgreSQL interface
        self.host = "localhost"  
        self.port = 0
        self.database = str(self.db_path)
        self.user = "sqlite"
        self.min_connections = 1
        self.max_connections = 1
        
        # SQLAlchemy engine for pandas integration
        self._engine = None
        
        logger.info(f"SQLite DatabaseManager initialized: {self.db_path.absolute()}")
    
    def initialize_pool(self) -> bool:
        """
        Initialize database connection (compatibility method)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Test connection
            conn = sqlite3.connect(self.db_path)
            conn.close()
            
            # Initialize SQLAlchemy engine
            self._engine = create_engine(f"sqlite:///{self.db_path}")
            
            self.is_connected = True
            logger.info("SQLite connection initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"SQLite initialization failed: {e}")
            return False
    
    def close_pool(self):
        """Close database connections (compatibility method)"""
        if self._engine:
            self._engine.dispose()
        self.is_connected = False
        logger.info("SQLite connections closed")
    
    @contextmanager
    def get_connection(self):
        """
        Get database connection context manager
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute SELECT query and return results as list of dictionaries
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of dictionaries representing query results
        """
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row  # Enable column name access
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                results = cursor.fetchall()
                # Convert sqlite3.Row to dictionaries
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def execute_query_to_dataframe(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """
        Execute query and return results as pandas DataFrame
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            pandas DataFrame with query results
        """
        try:
            if not self._engine:
                self._engine = create_engine(f"sqlite:///{self.db_path}")
            
            if params:
                # For parameterized queries, use pandas directly with sqlite3
                with self.get_connection() as conn:
                    return pd.read_sql_query(query, conn, params=params)
            else:
                return pd.read_sql_query(query, self._engine)
                
        except Exception as e:
            logger.error(f"DataFrame query execution failed: {e}")
            raise
    
    def execute_non_query(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Execute INSERT, UPDATE, DELETE query
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Number of affected rows
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                conn.commit()
                return cursor.rowcount
                
        except Exception as e:
            logger.error(f"Non-query execution failed: {e}")
            raise
    
    def execute_script(self, script_path: Union[str, Path]) -> bool:
        """
        Execute SQL script from file
        
        Args:
            script_path: Path to SQL script file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            script_path = Path(script_path)
            if not script_path.exists():
                logger.error(f"Script file not found: {script_path}")
                return False
            
            with open(script_path, 'r', encoding='utf-8') as file:
                script_content = file.read()
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executescript(script_content)
                conn.commit()
            
            logger.info(f"Script executed successfully: {script_path}")
            return True
            
        except Exception as e:
            logger.error(f"Script execution failed: {e}")
            return False
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            bool: True if table exists, False otherwise
        """
        try:
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
            result = self.execute_query(query, (table_name,))
            return len(result) > 0
        except Exception:
            return False
    
    def get_table_count(self, table_name: str) -> int:
        """
        Get number of records in a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            int: Number of records, 0 if table doesn't exist
        """
        try:
            if not self.table_exists(table_name):
                return 0
            
            query = f"SELECT COUNT(*) as count FROM {table_name}"
            result = self.execute_query(query)
            return result[0]['count'] if result else 0
            
        except Exception as e:
            logger.error(f"Error getting table count for {table_name}: {e}")
            return 0
    
    def is_database_populated(self) -> bool:
        """
        Check if database has been populated with data
        
        Returns:
            bool: True if database has data, False if empty
        """
        try:
            tables = ['RSPCCHAIN', 'RSPCLOGCHAIN', 'RSPCPROCESSLOG', 'RSPCVARIANT']
            
            for table in tables:
                count = self.get_table_count(table)
                if count == 0:
                    return False
            
            logger.info("Database is already populated with data")
            return True
            
        except Exception as e:
            logger.error(f"Error checking database population: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get information about the database
        
        Returns:
            Dictionary with database information
        """
        try:
            info = {
                "database_path": str(self.db_path.absolute()),
                "database_exists": self.db_path.exists(),
                "database_size_mb": 0,
                "tables": {},
                "is_populated": False
            }
            
            if self.db_path.exists():
                info["database_size_mb"] = round(self.db_path.stat().st_size / (1024 * 1024), 2)
                
                # Get table information
                tables = ['RSPCCHAIN', 'RSPCLOGCHAIN', 'RSPCPROCESSLOG', 'RSPCVARIANT']
                for table in tables:
                    info["tables"][table] = self.get_table_count(table)
                
                info["is_populated"] = self.is_database_populated()
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {"error": str(e)}

class SAPBWQueries:
    """
    Pre-defined SAP BW specific queries for common chatbot operations
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize with database manager
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db = db_manager
    
    def get_latest_chain_status(self, chain_id: Optional[str] = None) -> pd.DataFrame:
        """
        Get latest status of process chains
        
        Args:
            chain_id: Specific chain ID, or None for all chains
            
        Returns:
            DataFrame with latest chain status
        """
        if chain_id:
            query = """
            SELECT CHAIN_ID, STATUS_OF_PROCESS, CURRENT_DATE, TIME, LOG_ID
            FROM VW_LATEST_CHAIN_RUNS 
            WHERE rn = 1 AND CHAIN_ID = ?
            """
            return self.db.execute_query_to_dataframe(query, (chain_id,))
        else:
            query = """
            SELECT CHAIN_ID, STATUS_OF_PROCESS, CURRENT_DATE, TIME, LOG_ID
            FROM VW_LATEST_CHAIN_RUNS 
            WHERE rn = 1
            ORDER BY CURRENT_DATE DESC, TIME DESC
            """
            return self.db.execute_query_to_dataframe(query)
    
    def get_chain_success_rates(self, limit: int = 10) -> pd.DataFrame:
        """
        Get success rates for process chains
        
        Args:
            limit: Number of chains to return
            
        Returns:
            DataFrame with success rates
        """
        query = """
        SELECT CHAIN_ID, total_runs, successful_runs, failed_runs, 
               success_rate_percent, last_run_time
        FROM VW_CHAIN_SUMMARY
        ORDER BY success_rate_percent DESC
        LIMIT ?
        """
        return self.db.execute_query_to_dataframe(query, (limit,))
    
    def get_failed_chains(self) -> list:
        """
        Get all failed process chains (backward compatibility)
        
        Returns:
            List of dictionaries with failed chain information
        """
        query = """
        SELECT CHAIN_ID, PROCESS_TYPE, STATUS_OF_PROCESS as STATUS, CURRENT_DATE, TIME
        FROM VW_LATEST_CHAIN_RUNS
        WHERE STATUS_OF_PROCESS = 'FAILED' AND rn = 1
        ORDER BY CURRENT_DATE DESC, TIME DESC
        """
        return self.db.execute_query(query)
    
    def get_chain_performance_summary(self) -> list:
        """
        Get performance summary for all chains (backward compatibility)
        
        Returns:
            List of dictionaries with performance information
        """
        query = """
        SELECT 
            CHAIN_ID,
            COUNT(*) as total_runs,
            SUM(CASE WHEN STATUS_OF_PROCESS = 'SUCCESS' THEN 1 ELSE 0 END) as successful_runs,
            ROUND(100.0 * SUM(CASE WHEN STATUS_OF_PROCESS = 'SUCCESS' THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
        FROM VW_LATEST_CHAIN_RUNS
        GROUP BY CHAIN_ID
        ORDER BY success_rate DESC
        """
        return self.db.execute_query(query)
    
    def get_failed_chains_today(self) -> pd.DataFrame:
        """
        Get process chains that failed today
        
        Returns:
            DataFrame with failed chains
        """
        query = """
        SELECT CHAIN_ID, STATUS_OF_PROCESS, CURRENT_DATE, TIME
        FROM VW_TODAYS_ACTIVITY
        WHERE STATUS_OF_PROCESS = 'FAILED'
        ORDER BY TIME DESC
        """
        return self.db.execute_query_to_dataframe(query)
    
    def get_chain_history(self, chain_id: str, limit: int = 20) -> pd.DataFrame:
        """
        Get execution history for a specific chain
        
        Args:
            chain_id: Process chain ID
            limit: Number of records to return
            
        Returns:
            DataFrame with chain execution history
        """
        query = """
        SELECT LOG_ID, STATUS_OF_PROCESS, CURRENT_DATE, TIME, CREATED_TIMESTAMP
        FROM RSPCLOGCHAIN
        WHERE CHAIN_ID = ?
        ORDER BY CREATED_TIMESTAMP DESC
        LIMIT ?
        """
        return self.db.execute_query_to_dataframe(query, (chain_id, limit))

# Convenience functions for backward compatibility
def create_connection_pool(**kwargs) -> DatabaseManager:
    """Create a database manager instance"""
    return DatabaseManager(**kwargs)

def main():
    """Command line interface for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SAP BW SQLite Database Manager CLI")
    parser.add_argument("--db-path", default="sap_bw_demo.db", help="SQLite database file path")
    parser.add_argument("--test", action="store_true", help="Run connection test")
    parser.add_argument("--info", action="store_true", help="Show database information")
    parser.add_argument("--status", help="Get status of specific chain")
    
    args = parser.parse_args()
    
    # Create database manager
    db = DatabaseManager(args.db_path)
    
    if args.test:
        print("Testing SQLite connection...")
        if db.initialize_pool():
            print("✅ Connection successful")
            
            # Test basic query
            try:
                result = db.execute_query("SELECT sqlite_version()")
                print(f"SQLite version: {result[0]['sqlite_version()']}")
            except Exception as e:
                print(f"❌ Query test failed: {e}")
                
            db.close_pool()
        else:
            print("❌ Connection failed")
    
    if args.info:
        print("Database Information:")
        info = db.get_database_info()
        for key, value in info.items():
            print(f"  {key}: {value}")
    
    if args.status:
        print(f"Getting status for chain: {args.status}")
        if db.initialize_pool():
            queries = SAPBWQueries(db)
            status_df = queries.get_latest_chain_status(args.status)
            
            if not status_df.empty:
                print(status_df.to_string(index=False))
            else:
                print("No data found for this chain")
                
            db.close_pool()

if __name__ == "__main__":
    main() 