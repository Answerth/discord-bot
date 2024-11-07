# classify_activities.py
import os
import pandas as pd
from sqlalchemy import create_engine, Table, MetaData, select, update
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import quote
import json
from datetime import datetime, timedelta

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

def classify_activity(text, details):
    """Classify the activity based on its text and details."""
    if not text:
        return None

    text = text.lower()
    details = details.lower() if details else None

    if text == 'visited my clan citadel.':
        return 'clan - citadel visit'
    elif text == 'capped at my clan citadel.':
        return 'clan - citadel cap'
    elif 'i found' in text and 'pet' in text:
        return 'pet drop'
    elif 'i killed' in text or 'i defeated' in text:
        return 'combat'
    elif 'i found' in text:
        return 'item drop'
    elif 'xp in' in text:
        return 'xp milestone'
    elif 'levelled up' in text or 'i levelled' in text:
        return 'level'
    elif 'total levels' in text or 'levelled all skills' in text:
        return 'total levels'
    elif 'quest complete' in text:
        return 'quest'
    elif 'treasure trail' in text:
        return 'clue'
    elif 'treasure hunter' in details:
        return 'mtx'
    elif 'clan fealty' in text:
        return 'clan - fealty'
    elif 'dungeon floor' in text:
        return 'dungeoneering'
    elif 'archaeological mystery' in text or 'tetracompass' in text:
        return 'archaeology'
    elif 'quest points obtained' in text:
        return 'quest milestone'
    elif "daemonheim's history uncovered" in text:
        return 'dungeoneering'
    elif 'challenged by the skeleton champion' in text:
        return 'distraction and diversion'
    elif 'songs unlocked' in text:
        return 'songs'
    else:
        return None

def classify_and_update(engine):
    metadata = MetaData()
    activities_table = Table('activities', metadata, autoload_with=engine)

    with engine.begin() as conn:
        # Classify activities where activity_type is NULL
        select_stmt = select(activities_table).where(activities_table.c.activity_type.is_(None))
        result = conn.execute(select_stmt)
        activities = result.fetchall()

        for activity in activities:
            activity_id = activity.id
            text = activity.text
            details = activity.details
            classification = classify_activity(text, details)

            if classification:
                update_stmt = (
                    update(activities_table)
                    .where(activities_table.c.id == activity_id)
                    .values(activity_type=classification)
                )
                conn.execute(update_stmt)
                log_message(f"Classified activity ID {activity_id} as '{classification}'.")
            else:
                # Log unclassified activities
                with open(os.path.join(os.path.dirname(__file__), "digest.log"), "a") as digest_file:
                    digest_entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Unclassified Activity ID {activity_id}: Text='{text}', Details='{details}'\n"
                    digest_file.write(digest_entry)
                log_message(f"Unclassified activity ID {activity_id} logged to digest.")

    #Update status for activities older than 10 days to 'exempt'
    cleanup = True
    if cleanup == True:
        five_days_ago = datetime.now() - timedelta(days=5)
        with engine.begin() as conn:
            update_stmt = (
                update(activities_table)
                .where(activities_table.c.date < five_days_ago)
                .values(status='exempt')
            )
            result = conn.execute(update_stmt)
            log_message(f"Updated {result.rowcount} activities to status 'exempt'.")

if __name__ == "__main__":
    classify_and_update(engine)
    print("Activity classification and status update completed.")

