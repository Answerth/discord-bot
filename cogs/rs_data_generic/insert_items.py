import os
import json
import pandas as pd
import requests
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert  # PostgreSQL-specific insert
from datetime import datetime
import math

# Load database configuration from dbconfig.json
config_path = os.path.join(os.path.expanduser("~"), 'discordbot10s', 'dbconfig.json')
with open(config_path) as config_file:
    config = json.load(config_file)

# Create the SQLAlchemy engine using the loaded configuration
engine = create_engine(f"postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}")

def log_message(message, row_data=None):
    """Logs informational messages with optional row data for context."""
    print("INFO:", message)
    if row_data is not None:
        print("Row Data:", row_data)

def log_error(error_message, row_data=None):
    """Logs error messages with optional row data for context."""
    print("ERROR:", error_message)
    if row_data is not None:
        print("Row Data:", row_data)

def adjust_dataframe_structure(df, table_columns):
    """Ensures the DataFrame structure aligns with the database table columns."""
    for col in table_columns:
        if col not in df.columns:
            if col == "id":
                continue  # 'id' is handled separately as primary key
            df[col] = None
    df = df[[col for col in df.columns if col in table_columns]]
    return df

def log_conflict(message, row_data, log_file="data_insert_conflict_log.txt"):
    """Logs skipped rows due to conflict to a specified log file."""
    with open(log_file, "a") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"[{timestamp}] CONFLICT: {message}\n")
        file.write(f"Row Data: {row_data}\n\n")

def sanitize_row(row_dict):
    """
    Replace NaN with None for integer columns and convert floats to integers where appropriate.
    """
    integer_columns = ['limit', 'highalch', 'lowalch', 'value', 'price', 'last', 'volume']
    
    for col in integer_columns:
        if col in row_dict:
            value = row_dict[col]
            if isinstance(value, float):
                if math.isnan(value):
                    row_dict[col] = None
                else:
                    # Convert float to int if it's a whole number
                    if value.is_integer():
                        row_dict[col] = int(value)
                    else:
                        # Handle cases where float is not a whole number
                        row_dict[col] = int(round(value))
            elif isinstance(value, str):
                # Attempt to convert string numbers to integers
                try:
                    row_dict[col] = int(value)
                except ValueError:
                    row_dict[col] = None
    return row_dict

def validate_required_fields(row_dict):
    """Ensure that required fields are present and not None."""
    required_fields = ['id', 'name']
    for field in required_fields:
        if field not in row_dict or row_dict[field] is None:
            return False
    return True

def insert_items(engine, df, table_name, unique_column="id"):
    print(f"Processing {len(df)} rows")  # This should display 50 rows if slicing works correctly
    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=engine)
    table_columns = [column.name for column in table.columns]

    df = adjust_dataframe_structure(df, table_columns)

    with engine.begin() as conn:
        for _, row in df.iterrows():
            try:
                row_dict = row.to_dict()
                row_dict = sanitize_row(row_dict)  # Sanitize row data

                # Validate required fields
                if not validate_required_fields(row_dict):
                    log_error(f"Missing required fields for item ID: {row_dict.get('id')}", row_dict)
                    continue  # Skip this row

                # Upsert logic: Insert new rows or update existing ones based on unique_column
                insert_stmt = insert(table).values(**row_dict)
                upsert_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=[unique_column],
                    set_={col: insert_stmt.excluded[col] for col in row_dict if col != unique_column}
                )
                conn.execute(upsert_stmt)
                log_message(f"Upserted row with {unique_column}: {row_dict[unique_column]}")
            except SQLAlchemyError as e:
                log_error(f"Database error while inserting row with {unique_column}: {row_dict.get(unique_column)}", row_dict)
                log_error(str(e))
            except Exception as e:
                log_error(f"Unexpected error while inserting row with {unique_column}: {row_dict.get(unique_column)}", row_dict)
                log_error(str(e))

def download_and_prepare_data(url):
    """Downloads JSON data from the specified URL and prepares it as a DataFrame."""
    response = requests.get(url)
    if response.status_code == 200:
        try:
            data = response.json()
            # Save raw JSON for inspection
            with open("raw_rs_dump.json", "w") as f:
                json.dump(data, f, indent=4)
            # Flatten the JSON: convert dict of dicts to list of dicts
            items_list = []
            for item_id, item_data in data.items():
                try:
                    # Attempt to convert the item_id to an integer
                    int_id = int(item_id)
                    item_data['id'] = int_id  # Ensure 'id' is integer
                    items_list.append(item_data)
                except ValueError:
                    # If conversion fails, skip this entry and log the issue
                    log_error(f"Skipping item with non-integer ID: {item_id}", item_data)
            df = pd.DataFrame(items_list)
            return df
        except json.JSONDecodeError as jde:
            raise Exception("Failed to parse JSON. The response might not be valid JSON.")
    else:
        raise Exception(f"Failed to download data. Status code: {response.status_code}")

if __name__ == "__main__":
    # URL of the item database
    url = "https://chisel.weirdgloop.org/gazproj/gazbot/rs_dump.json"
    
    try:
        # Download and prepare data
        df_items = download_and_prepare_data(url)
        log_message("JSON data downloaded and converted to DataFrame.")
        
        # Limit df for experimentation
        #df_items_limited = df_items.head(50)
        #print(f"Limited DataFrame to {len(df_items_limited)} rows.")
        
        # Insert data into 'items' table with upsert logic
        insert_items(engine, df_items, 'items', unique_column="id")
        log_message("Data insertion into 'items' table completed successfully.")
    except Exception as e:
        log_error("An error occurred during the data download or insertion process.", None)
        log_error(str(e))
