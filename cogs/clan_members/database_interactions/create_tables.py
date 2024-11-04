import os
import json
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime

# Load database configuration from dbconfig.json in the parent directory
#config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dbconfig.json')
config_path = os.path.join(os.path.expanduser("~"), 'discordbot10s', 'dbconfig.json')

with open(config_path) as config_file:
    config = json.load(config_file)

# Create the SQLAlchemy engine using the loaded configuration
engine = create_engine(f"postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}")

def create_db_tables(engine):
    metadata = MetaData()

    # Define the members table
    members = Table(
        'members', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('name', String, unique=True, nullable=False),
        Column('rank', String, nullable=True),
        Column('experience', Integer, nullable=True),
        Column('kills', Integer, nullable=True)
    )

    # Define the activities table
    activities = Table(
        'activities', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('member_name', String, nullable=False),  # Links to 'name' in members
        Column('date', DateTime, nullable=False),  # Date of activity
        Column('details', String, nullable=True),  # Full activity details
        Column('text', String, nullable=True)  # Additional text field from activities
    )

    metadata.create_all(engine)

# Execute table creation
create_db_tables(engine)
