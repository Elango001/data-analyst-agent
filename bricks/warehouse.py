"""
Simple SQL Warehouse connection using Databricks SDK
"""
from databricks.sdk import WorkspaceClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_warehouse_connection():
    """
    Test connection to Databricks SQL Warehouse using SDK
    """
    try:
        # Get connection parameters from environment
        host = os.getenv("DATABRICKS_HOST")
        token = os.getenv("DATABRICKS_TOKEN")
        
        if not all([host, token]):
            raise ValueError("Missing required environment variables: DATABRICKS_HOST or DATABRICKS_TOKEN")
        
        # Initialize Databricks client with explicit credentials
        w = WorkspaceClient(
            host=host,
            token=token
        )
        
        # Test connection by getting current user info
        current_user = w.current_user.me()
        print("✓ Connection successful!")
        print(f"Host: {host}")
        print(f"Current user: {current_user.user_name}")
        print(f"User ID: {current_user.id}")
        
        # Optionally test SQL Warehouse if warehouse ID is provided
        warehouse_id = os.getenv("DATABRICKS_WAREHOUSE_ID")
        if warehouse_id:
            result = w.statement_execution.execute_statement(
                warehouse_id=warehouse_id,
                statement="SELECT 1 as test"
            )
            print(f"\n✓ SQL Warehouse test successful!")
            print(f"Warehouse ID: {warehouse_id}")
            print(f"Statement ID: {result.statement_id}")
            if result.status:
                print(f"Status: {result.status.state}")
        
        return True
        
    except Exception as e:
        print(f"✗ Connection failed: {str(e)}")
        return False


if __name__ == "__main__":
    test_warehouse_connection()
