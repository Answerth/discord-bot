# insert_data.py
import os
import json
import pandas as pd
from sqlalchemy import create_engine, Table, MetaData, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime

# Load database configuration from dbconfig.json in the parent directory
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
                continue
            df[col] = None
    df = df[[col for col in df.columns if col in table_columns]]
    return df

def insert_data(engine, df, table_name, unique_column=None):
    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=engine)
    table_columns = [column.name for column in table.columns]

    df = adjust_dataframe_structure(df, table_columns)

    with engine.begin() as conn:
        for _, row in df.iterrows():
            try:
                if table_name == "members" and unique_column:
                    # Upsert for members table to handle changes
                    insert_stmt = insert(table).values(**row.to_dict())
                    upsert_stmt = insert_stmt.on_conflict_do_update(
                        index_elements=[unique_column],
                        set_={col: insert_stmt.excluded[col] for col in row.index if col != unique_column}
                    )
                    conn.execute(upsert_stmt)
                    log_message(f"Upserted row for {unique_column}: {row[unique_column]}")
                elif table_name == "activities":
                    # Insert for activities with conflict handling
                    insert_stmt = insert(table).values(**row.to_dict())
                    do_nothing_stmt = insert_stmt.on_conflict_do_nothing()
                    result = conn.execute(do_nothing_stmt)

                    # Check if the row was inserted by counting affected rows
                    if result.rowcount == 0:
                        log_conflict("Conflict skipped for activity row", row.to_dict())
                    else:
                        log_message(f"Inserted activity row for member: {row.get('member_name', row.get('name'))}")
                else:
                    # Generic insert for other tables if any
                    conn.execute(insert(table).values(**row.to_dict()))
                    log_message(f"Inserted row into {table_name}: {row.to_dict()}")

            except SQLAlchemyError as e:
                log_error(f"Database error while inserting row for {unique_column}: {row.get(unique_column)}", row.to_dict())
                log_error(str(e))

def log_conflict(message, row_data, log_file="data_insert_conflict_log.txt"):
    """Logs skipped rows due to conflict to a specified log file."""
    with open(log_file, "a") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"[{timestamp}] CONFLICT: {message}\n")
        file.write(f"Row Data: {row_data}\n\n")

# Load data from the pickle files
data_dir = os.path.dirname(__file__)
members_df = pd.read_pickle(os.path.join(data_dir, "./fetch_and_flatten_data_files/members_data.pkl"))
activities_df = pd.read_pickle(os.path.join(data_dir, "./fetch_and_flatten_data_files/activities_data.pkl"))

# Adjust column names to match the database structure
members_df = members_df.rename(columns={"name": "name"})
activities_df = activities_df.rename(columns={"name": "member_name"})

# Insert the data into the respective tables
insert_data(engine, members_df, 'members', unique_column="name")
insert_data(engine, activities_df, 'activities')

print("Data insertion process completed.")

