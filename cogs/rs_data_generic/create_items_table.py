import os
import json
from sqlalchemy import create_engine, MetaData, Table, Column, BigInteger, String, Boolean

# Load database configuration from dbconfig.json
config_path = os.path.join(os.path.expanduser("~"), 'discordbot10s', 'dbconfig.json')

with open(config_path) as config_file:
    config = json.load(config_file)

# Create the SQLAlchemy engine using the loaded configuration
engine = create_engine(f"postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}")

def create_items_table(engine):
    metadata = MetaData()

    # Define the items table with BigInteger for large numeric fields
    items = Table(
        'items', metadata,
        Column('id', BigInteger, primary_key=True, unique=True, nullable=False),
        Column('limit', BigInteger, nullable=True),
        Column('highalch', BigInteger, nullable=True),
        Column('name', String, nullable=False),
        Column('examine', String, nullable=True),
        Column('value', BigInteger, nullable=True),
        Column('members', Boolean, nullable=True),
        Column('lowalch', BigInteger, nullable=True),
        Column('name_pt', String, nullable=True),
        Column('price', BigInteger, nullable=True),
        Column('last', BigInteger, nullable=True),
        Column('volume', BigInteger, nullable=True),
        Column('icon', String, nullable=True)  # Added 'icon' field based on JSON
    )

    metadata.create_all(engine)
    print("Items table created successfully.")

# Execute table creation
if __name__ == "__main__":
    create_items_table(engine)
