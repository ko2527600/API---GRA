#!/usr/bin/env python
"""Setup PostgreSQL database for testing"""
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    """Create the API_s_GRA database if it doesn't exist"""
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(
            user='postgres',
            password='postgres',
            host='localhost',
            port='5432',
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'API_s_GRA'")
        exists = cur.fetchone()
        
        if not exists:
            cur.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier('API_s_GRA')
            ))
            print("✓ Database 'API_s_GRA' created successfully")
        else:
            print("✓ Database 'API_s_GRA' already exists")
        
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Error creating database: {e}")
        return False

if __name__ == "__main__":
    if create_database():
        print("\nNow run: python init_db.py")
    else:
        print("\nFailed to create database")
