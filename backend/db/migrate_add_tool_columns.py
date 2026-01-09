"""
Migration script to add tool_result and tool_args columns to tool_execution_log table
Run this once to update your existing database
"""
from sqlalchemy import create_engine, text
from backend.Configuration.config import Config

def migrate():
    """Add new columns to existing table"""
    db_config = Config.db_config
    handler = db_config.get_deleted_data_handler()
    
    if not handler:
        print("Error: Database not configured")
        return
    
    engine = handler.engine
    
    # Add the new columns
    with engine.connect() as conn:
        try:
            # Check if columns exist first
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='tool_execution_log' 
                AND column_name IN ('tool_result', 'tool_args')
            """))
            existing_columns = [row[0] for row in result]
            
            if 'tool_result' not in existing_columns:
                print("Adding tool_result column...")
                conn.execute(text("ALTER TABLE tool_execution_log ADD COLUMN tool_result TEXT"))
                conn.commit()
                print("✓ Added tool_result column")
            else:
                print("tool_result column already exists")
            
            if 'tool_args' not in existing_columns:
                print("Adding tool_args column...")
                conn.execute(text("ALTER TABLE tool_execution_log ADD COLUMN tool_args TEXT"))
                conn.commit()
                print("✓ Added tool_args column")
            else:
                print("tool_args column already exists")
            
            print("\nMigration completed successfully!")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            conn.rollback()

if __name__ == "__main__":
    migrate()
