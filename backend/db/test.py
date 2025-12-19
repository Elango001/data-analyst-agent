import pandas as pd
from backend.Configuration.config import Config
from backend.tools.cleaner_tools import remove_outliers, drop_columns, dropna

df = pd.read_csv("/home/elango/Documents/projects/statathon/backend/uploads/df.csv")

Config.data_config.set_df(df)

Config.db_config.set_db_config(
    host="localhost",
    database="preprocessing_logs",
    user="postgres",
    password="__Elango2006",
    port=5432,
    csv_path="/home/elango/Documents/projects/statathon/backend/updates/deleted_data.csv"
)


result1 = dropna.invoke({"columns": ["FWI"], "strategy": "mean"})
print("Result:", result1)

print("\n" + "="*50)
print("Testing remove_outliers tool...")
print("="*50)
result2 = remove_outliers.invoke({"column": "FWI", "strategy": "iqr"})
print("Result:", result2)

print("\n" + "="*50)
print("Testing drop_columns tool...")
print("="*50)
result3 = drop_columns.invoke({"columns": ["FWI"]})
print("Result:", result3)

print("\n" + "="*50)
print("All tool logs from database:")
print("="*50)
for log in Config.db_config.get_deleted_data_handler().get_all_tool_logs():
    print(log)
    if log['deleted_data']:
        deleted_data = Config.db_config.get_deleted_data_handler().get_deleted_data(log['id'])
        if deleted_data is not None:
            print(f"  -> Retrieved {len(deleted_data)} deleted rows from CSV")

print("\nFinal DataFrame shape:", Config.data_config.get_df().shape)

# Config.db_config.