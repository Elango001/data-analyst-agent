"""
Example usage of Versioner and Revert classes
"""
import pandas as pd
from datetime import datetime
from backend.Configuration.config import Config
from backend.db.revert import Versioner, Revert

# Initialize Config
config = Config()

# Set up database configuration (required before using Versioner/Revert)
config.db_config.set_db_config(
    host="localhost",
    database="preprocessing_logs",
    user="postgres",
    password="__Elango2006",
    port=5432,
    csv_path="deleted_data.csv",
    version_dir="data_versions"  # Directory where version CSVs will be stored
)

# Example 1: Load some initial data
sample_data = pd.DataFrame({
    'A': [1, 2, 3, 4, 5],
    'B': ['a', 'b', 'c', 'd', 'e'],
    'C': [10.5, 20.3, 30.1, 40.8, 50.2]
})

config.data_config.set_df(sample_data)
print("Initial data loaded:")
print(config.data_config.get_df())
print()

# Example 2: Save a version
versioner = Versioner(config)

# Save version 1
timestamp1 = versioner.save_version("Initial data load - clean dataset")
print(f"Version 1 saved with timestamp: {timestamp1}")
print()

# Example 3: Modify the data
modified_data = config.data_config.get_df().copy()
modified_data = modified_data[modified_data['A'] > 2]  # Remove some rows
config.data_config.set_df(modified_data)
print("Data after modification (rows with A > 2):")
print(config.data_config.get_df())
print()

# Example 4: Save another version
timestamp2 = versioner.save_version("Removed rows where A <= 2")
print(f"Version 2 saved with timestamp: {timestamp2}")
print()

# Example 5: List all available versions
print("All available versions:")
all_versions = versioner.get_all_versions()
for version in all_versions:
    print(f"  - {version['timestamp']}: {version['tool_details']}")
print()

# Example 6: Revert to previous version
revert = Revert(config)

print("Reverting to version 1...")
revert.revert_to_version(timestamp1)
print("Data after revert:")
print(config.data_config.get_df())
print()

# Example 7: Preview a version without reverting
print("Previewing version 2 data without reverting:")
version2_data = revert.get_version_data(timestamp2)
print(version2_data)
print()

# Example 8: Check current data is still version 1
print("Current data in config (should still be version 1):")
print(config.data_config.get_df())
print()

print("Note: All versions remain stored in both PostgreSQL and local CSV files.")
print("Reverting copies data but does not delete old versions.")
