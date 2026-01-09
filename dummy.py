import os
from databricks import sql
from dotenv import load_dotenv

load_dotenv()

# From your screenshot
host = os.getenv("DATABRICKS_HOST")         # e.g. https://dbc-261ec4ed-96fe.cloud.databricks.com
http_path = os.getenv("DATABRICKS_HTTP_PATH")  # e.g. /sql/1.0/warehouses/bb2e478aa8a230b2
token = os.getenv("DATABRICKS_TOKEN")         # Your PAT

# Connect to SQL Warehouse
with sql.connect(
    server_hostname=host,
    http_path=http_path,
    access_token=token
) as connection:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 AS test")
        result = cursor.fetchall()
        print("✓ Connection successful!")
        print(result)
