"""
Database connection and utility functions for Placement Management System.
Uses MySQL with connection pooling and parameterized queries.
"""

import mysql.connector
from mysql.connector import pooling, Error
import os
from dotenv import load_dotenv
import logging

# Always reload .env so the pool picks up the latest credentials
load_dotenv(override=True)

logger = logging.getLogger(__name__)


def _build_db_config() -> dict:
    """Build DB config dict from environment variables (re-read each call)."""
    return {
        "host":      os.getenv("DB_HOST", "localhost"),
        "port":      int(os.getenv("DB_PORT", 3306)),
        "database":  os.getenv("DB_NAME", "placement_management"),
        "user":      os.getenv("DB_USER", "root"),
        "password":  os.getenv("DB_PASSWORD", ""),
        "charset":   "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
        "autocommit": False,
    }


# Module-level config snapshot (read once at import time)
DB_CONFIG = _build_db_config()

_connection_pool = None
_pool_config_key = None          # detect .env changes between restarts


def _config_key(cfg: dict) -> str:
    """Stable string key for detecting config changes."""
    return f"{cfg['host']}:{cfg['port']}:{cfg['database']}:{cfg['user']}"


def get_connection_pool():
    """Initialize (or re-initialize) and return MySQL connection pool."""
    global _connection_pool, _pool_config_key

    current_cfg = _build_db_config()
    current_key = _config_key(current_cfg)

    # Reset pool if credentials changed (e.g. .env edited between runs)
    if _connection_pool is not None and _pool_config_key != current_key:
        _connection_pool = None

    if _connection_pool is None:
        try:
            _connection_pool = pooling.MySQLConnectionPool(
                pool_name="placement_pool",
                pool_size=5,
                pool_reset_session=True,
                **current_cfg,
            )
            _pool_config_key = current_key
        except Error as e:
            logger.error(f"Error creating connection pool: {e}")
            raise
    return _connection_pool


def get_connection():
    """Get a connection from the pool."""
    try:
        pool = get_connection_pool()
        return pool.get_connection()
    except Error as e:
        logger.error(f"Error getting connection from pool: {e}")
        raise


def execute_query(query: str, params: tuple = None, fetch: str = None):
    """
    Execute a parameterized SQL query.
    
    Args:
        query: SQL query string with %s placeholders
        params: Tuple of parameters for the query
        fetch: 'one', 'all', or None for INSERT/UPDATE/DELETE
    
    Returns:
        Query results or affected row count
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        if fetch == "one":
            result = cursor.fetchone()
            conn.commit()
            return result
        elif fetch == "all":
            result = cursor.fetchall()
            conn.commit()
            return result
        else:
            conn.commit()
            return cursor.rowcount
            
    except Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}\nQuery: {query}\nParams: {params}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def execute_many(query: str, params_list: list):
    """Execute a query with multiple parameter sets."""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.executemany(query, params_list)
        conn.commit()
        return cursor.rowcount
    except Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error in execute_many: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def execute_transaction(queries: list):
    """
    Execute multiple queries as a transaction.
    
    Args:
        queries: List of (query, params) tuples
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        results = []
        for query, params in queries:
            cursor.execute(query, params or ())
            results.append(cursor.lastrowid)
        conn.commit()
        return results
    except Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Transaction error: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def test_connection():
    """Test database connectivity. Returns (True, msg) or (False, error_msg)."""
    try:
        cfg = _build_db_config()
        conn = mysql.connector.connect(
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            database=cfg["database"],
            connection_timeout=5,
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return True, "Connection successful"
    except Error as e:
        return False, str(e)


def get_db_config_summary() -> str:
    """Return a safe (no password) summary of current DB config for error display."""
    cfg = _build_db_config()
    return (
        f"Host: {cfg['host']}  |  "
        f"Port: {cfg['port']}  |  "
        f"Database: {cfg['database']}  |  "
        f"User: {cfg['user']}  |  "
        f"Password: {'(set)' if cfg['password'] else '(empty — not set)'}"
    )


def init_database():
    """Initialize database schema if not exists."""
    try:
        cfg = _build_db_config()
        conn = mysql.connector.connect(
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            connection_timeout=5,
        )
        cursor = conn.cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{cfg['database']}` "
            f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Error as e:
        logger.error(f"Error initializing database: {e}")
        return False
