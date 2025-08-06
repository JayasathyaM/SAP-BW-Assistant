#!/usr/bin/env python3
"""
SAP BW Weekly Data Loader

This script loads comprehensive weekly SAP BW process chain data
for realistic chatbot testing and demonstration.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def load_weekly_data(db_path: str = "sap_bw_demo.db", 
                    schema_file: str = "database/schema.sql",
                    data_file: str = "database/weekly_data.sql"):
    """
    Load comprehensive weekly SAP BW data
    
    Args:
        db_path: Path to SQLite database file
        schema_file: Path to schema SQL file
        data_file: Path to weekly data SQL file
    """
    
    print("🗄️  SAP BW Weekly Data Loader")
    print("=" * 60)
    
    # Remove existing database if it exists
    db_file = Path(db_path)
    if db_file.exists():
        print(f"📂 Removing existing database: {db_file}")
        db_file.unlink()
    else:
        print("📂 No existing database found")
    
    # Create fresh database
    print(f"🆕 Creating fresh database: {db_file}")
    
    try:
        # Connect to database (creates file)
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
        
        # Load schema
        schema_path = Path(schema_file)
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        print(f"📋 Loading schema from: {schema_path}")
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Execute schema
        try:
            conn.executescript(schema_sql)
            print("✅ Schema loaded successfully")
        except Exception as e:
            print(f"❌ Schema loading failed: {e}")
            raise
        
        # Load weekly data
        data_path = Path(data_file)
        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found: {data_path}")
        
        print(f"📊 Loading weekly data from: {data_path}")
        
        # Temporarily disable foreign key constraints for data loading
        conn.execute("PRAGMA foreign_keys = OFF")
        
        with open(data_path, 'r', encoding='utf-8') as f:
            data_sql = f.read()
        
        # Execute data
        try:
            conn.executescript(data_sql)
            conn.commit()
            print("✅ Weekly data loaded successfully")
        except Exception as e:
            print(f"❌ Data loading failed: {e}")
            raise
        
        # Re-enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Verify data load
        cursor = conn.cursor()
        
        # Check table counts
        tables = ['RSPCCHAIN', 'RSPCLOGCHAIN', 'RSPCPROCESSLOG', 'RSPCVARIANT']
        print("\n📈 Data Verification:")
        print("-" * 40)
        
        total_records = 0
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table:15}: {count:4} records")
            total_records += count
        
        print("-" * 40)
        print(f"{'TOTAL':15}: {total_records:4} records")
        
        # Test views
        print("\n🔍 Testing Views:")
        print("-" * 40)
        
        # Test VW_LATEST_CHAIN_RUNS
        cursor.execute("SELECT COUNT(*) FROM VW_LATEST_CHAIN_RUNS WHERE rn = 1")
        latest_count = cursor.fetchone()[0]
        print(f"Latest chain runs: {latest_count}")
        
        # Test VW_CHAIN_SUMMARY
        cursor.execute("SELECT COUNT(*) FROM VW_CHAIN_SUMMARY")
        summary_count = cursor.fetchone()[0]
        print(f"Chain summaries: {summary_count}")
        
        # Test current status distribution
        cursor.execute("""
            SELECT STATUS_OF_PROCESS, COUNT(*) as count 
            FROM VW_LATEST_CHAIN_RUNS 
            WHERE rn = 1 
            GROUP BY STATUS_OF_PROCESS
        """)
        status_dist = cursor.fetchall()
        print(f"\nStatus Distribution:")
        for status, count in status_dist:
            emoji = {'SUCCESS': '✅', 'FAILED': '❌', 'RUNNING': '🔄', 'WAITING': '⏳', 'CANCELLED': '🚫'}.get(status, '❓')
            print(f"  {emoji} {status:8}: {count}")
        
        # Show sample recent activity
        print("\n📋 Recent Process Chain Activity:")
        print("-" * 40)
        cursor.execute("""
            SELECT CHAIN_ID, STATUS_OF_PROCESS, "CURRENT_DATE", "TIME"
            FROM VW_LATEST_CHAIN_RUNS 
            WHERE rn = 1 
            ORDER BY "CURRENT_DATE" DESC, "TIME" DESC 
            LIMIT 8
        """)
        
        for row in cursor.fetchall():
            chain_id, status, date, time = row
            status_emoji = {
                'SUCCESS': '✅',
                'FAILED': '❌', 
                'RUNNING': '🔄',
                'WAITING': '⏳',
                'CANCELLED': '🚫'
            }.get(status, '❓')
            print(f"{status_emoji} {chain_id:25} {status:8} {date} {time}")
        
        # Show failure analysis
        print("\n🔍 Failure Analysis:")
        print("-" * 40)
        cursor.execute("""
            SELECT CHAIN_ID, 
                   total_runs,
                   failed_runs,
                   success_rate_percent
            FROM VW_CHAIN_SUMMARY
            ORDER BY failed_runs DESC, success_rate_percent ASC
        """)
        
        for row in cursor.fetchall():
            chain_id, total, failed, success_rate = row
            if failed > 0:
                print(f"⚠️  {chain_id:25} {failed}/{total} failures ({success_rate:.1f}% success)")
            else:
                print(f"✅ {chain_id:25} {total}/{total} success ({success_rate:.1f}% success)")
        
        conn.close()
        
        print("\n🎉 Weekly data setup completed successfully!")
        print(f"📍 Database location: {db_file.absolute()}")
        print("🚀 Ready for comprehensive chatbot testing!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading weekly data: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load SAP BW weekly test data")
    parser.add_argument("--db-path", default="sap_bw_demo.db", 
                       help="SQLite database file path")
    parser.add_argument("--schema", default="database/schema.sql",
                       help="Schema SQL file path")
    parser.add_argument("--data", default="database/weekly_data.sql",
                       help="Weekly data SQL file path")
    parser.add_argument("--force", action="store_true",
                       help="Force overwrite existing database")
    
    args = parser.parse_args()
    
    # Check if database exists and confirm overwrite
    if Path(args.db_path).exists() and not args.force:
        response = input(f"Database {args.db_path} exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Operation cancelled.")
            return
    
    # Load the data
    success = load_weekly_data(args.db_path, args.schema, args.data)
    
    if success:
        print("\n✨ Next steps:")
        print("   1. Test queries: python database/db_manager_sqlite.py --status PC_SALES_DAILY")
        print("   2. Run setup test: python test_setup.py")
        print("   3. Test AI components: python llm/query_processor.py --test")
        print("   4. Start chatbot: streamlit run app.py")
    else:
        print("\n🔧 Please fix the errors and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main() 