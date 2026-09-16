"""
Database Integration - PostgreSQL, MySQL, SQLite support
Execute queries and manage database connections
"""

import logging
from typing import Dict, List, Any, Optional, Union
import json

logger = logging.getLogger(__name__)


class DatabaseIntegration:
    """
    Multi-database integration supporting PostgreSQL, MySQL, SQLite
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize database integration

        Args:
            config: Configuration dict with:
                - db_type: 'postgresql', 'mysql', or 'sqlite'
                - host: Database host (for PostgreSQL/MySQL)
                - port: Database port (for PostgreSQL/MySQL)
                - database: Database name
                - username: Database username (for PostgreSQL/MySQL)
                - password: Database password (for PostgreSQL/MySQL)
                - db_path: Database file path (for SQLite)
        """
        self.config = config
        self.db_type = config.get('db_type', 'sqlite').lower()
        self.connection = None

    def connect(self) -> Dict[str, Any]:
        """
        Establish database connection

        Returns:
            Dict with connection status
        """
        try:
            if self.db_type == 'postgresql':
                return self._connect_postgresql()
            elif self.db_type == 'mysql':
                return self._connect_mysql()
            elif self.db_type == 'sqlite':
                return self._connect_sqlite()
            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")

        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def _connect_postgresql(self) -> Dict[str, Any]:
        """Connect to PostgreSQL"""
        try:
            import psycopg2
        except ImportError:
            return {
                'status': 'error',
                'error': 'psycopg2 not installed. Run: pip install psycopg2-binary'
            }

        try:
            self.connection = psycopg2.connect(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 5432),
                database=self.config.get('database'),
                user=self.config.get('username'),
                password=self.config.get('password')
            )

            logger.info(f"Connected to PostgreSQL: {self.config.get('database')}")
            return {
                'status': 'success',
                'db_type': 'postgresql',
                'database': self.config.get('database')
            }

        except Exception as e:
            raise Exception(f"PostgreSQL connection failed: {e}")

    def _connect_mysql(self) -> Dict[str, Any]:
        """Connect to MySQL"""
        try:
            import mysql.connector
        except ImportError:
            return {
                'status': 'error',
                'error': 'mysql-connector-python not installed. Run: pip install mysql-connector-python'
            }

        try:
            self.connection = mysql.connector.connect(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 3306),
                database=self.config.get('database'),
                user=self.config.get('username'),
                password=self.config.get('password')
            )

            logger.info(f"Connected to MySQL: {self.config.get('database')}")
            return {
                'status': 'success',
                'db_type': 'mysql',
                'database': self.config.get('database')
            }

        except Exception as e:
            raise Exception(f"MySQL connection failed: {e}")

    def _connect_sqlite(self) -> Dict[str, Any]:
        """Connect to SQLite"""
        import sqlite3

        try:
            db_path = self.config.get('db_path', 'workflows.db')
            self.connection = sqlite3.connect(db_path)
            self.connection.row_factory = sqlite3.Row

            logger.info(f"Connected to SQLite: {db_path}")
            return {
                'status': 'success',
                'db_type': 'sqlite',
                'db_path': db_path
            }

        except Exception as e:
            raise Exception(f"SQLite connection failed: {e}")

    def execute_query(
        self,
        query: str,
        params: Optional[Union[tuple, dict]] = None,
        fetch: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a SQL query

        Args:
            query: SQL query string
            params: Query parameters (tuple or dict)
            fetch: Whether to fetch results (for SELECT)

        Returns:
            Dict with results or status
        """
        if not self.connection:
            connect_result = self.connect()
            if connect_result['status'] == 'error':
                return connect_result

        try:
            cursor = self.connection.cursor()

            # Execute query
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Fetch results if needed
            if fetch:
                if self.db_type == 'sqlite':
                    rows = cursor.fetchall()
                    results = [dict(row) for row in rows]
                else:
                    rows = cursor.fetchall()
                    if cursor.description:
                        columns = [desc[0] for desc in cursor.description]
                        results = [dict(zip(columns, row)) for row in rows]
                    else:
                        results = []

                logger.info(f"Query executed, {len(results)} rows returned")
                return {
                    'status': 'success',
                    'rows': results,
                    'row_count': len(results)
                }
            else:
                self.connection.commit()
                row_count = cursor.rowcount

                logger.info(f"Query executed, {row_count} rows affected")
                return {
                    'status': 'success',
                    'rows_affected': row_count
                }

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'query': query
            }

        finally:
            cursor.close()

    def execute_many(
        self,
        query: str,
        params_list: List[Union[tuple, dict]]
    ) -> Dict[str, Any]:
        """
        Execute a query multiple times with different parameters

        Args:
            query: SQL query string
            params_list: List of parameter tuples/dicts

        Returns:
            Dict with status
        """
        if not self.connection:
            connect_result = self.connect()
            if connect_result['status'] == 'error':
                return connect_result

        try:
            cursor = self.connection.cursor()
            cursor.executemany(query, params_list)
            self.connection.commit()

            row_count = cursor.rowcount

            logger.info(f"Batch query executed, {row_count} rows affected")
            return {
                'status': 'success',
                'rows_affected': row_count,
                'batch_size': len(params_list)
            }

        except Exception as e:
            logger.error(f"Batch query failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

        finally:
            cursor.close()

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")


class DatabaseAgent:
    """
    Agent wrapper for database integration
    Compatible with workflow engine
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize database agent"""
        self.integration = DatabaseIntegration(config)
        self.name = "database_agent"
        self.description = "Execute database queries (PostgreSQL, MySQL, SQLite)"

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute database operation

        Context should contain:
            - query: SQL query string
            - params: Query parameters (optional)
            - fetch: Whether to fetch results (default: True)
        """
        try:
            query = context.get('query')

            if not query:
                return {
                    'status': 'error',
                    'error': 'query is required'
                }

            result = self.integration.execute_query(
                query=query,
                params=context.get('params'),
                fetch=context.get('fetch', True)
            )

            return result

        except Exception as e:
            logger.error(f"Database agent error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

        finally:
            # Close connection after execution
            self.integration.close()


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['DatabaseIntegration', 'DatabaseAgent']
