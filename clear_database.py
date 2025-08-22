#!/usr/bin/env python3
"""
Clear Database Script
Clears all data from database tables without deleting the database file
"""

import sys
import gc
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from loguru import logger

def clear_database():
    """Clear all data from database tables"""
    try:
        from database_manager import DatabaseManager
        
        # Create database manager
        db_manager = DatabaseManager()
        
        # Get connection and clear all tables
        import sqlite3
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.cursor()
            
            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            # Clear each table
            for table in tables:
                table_name = table[0]
                if table_name != 'sqlite_sequence':  # Skip system table
                    cursor.execute(f"DELETE FROM {table_name}")
                    logger.info(f"Cleared table: {table_name}")
            
            # Reset auto-increment counters
            cursor.execute("DELETE FROM sqlite_sequence")
            
            conn.commit()
        
        logger.info("All database tables cleared successfully")
        
        # Verify empty database
        stats = db_manager.get_dashboard_stats()
        logger.info(f"Database clear complete. Stats: {stats}")
        
        # Close connection
        del db_manager
        gc.collect()
        
        return True
        
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        return False

def main():
    """Main function"""
    print("🧹 Clearing Database Tables")
    print("=" * 50)
    
    success = clear_database()
    
    if success:
        print("\n✅ Database cleared successfully!")
        print("💡 Next steps:")
        print("   1. Run 'python upload_resume_and_search.py' to scrape real jobs")
        print("   2. Or use the web interface to search for jobs")
    else:
        print("\n❌ Database clear failed.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
