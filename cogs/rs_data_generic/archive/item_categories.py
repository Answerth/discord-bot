#!/usr/bin/env python3
import os
import json
import time
from math import ceil
from urllib.parse import quote, urlparse
from tqdm import tqdm
import logging
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ============================
# Configuration and Constants
# ============================

# Category Mapping (ID to Name)
CATEGORY_MAPPING = {
    0: "Miscellaneous",
    1: "Ammo",
    2: "Arrows",
    3: "Bolts",
    4: "Construction materials",
    5: "Construction products",
    6: "Cooking ingredients",
    7: "Costumes",
    8: "Crafting materials",
    9: "Familiars",
    10: "Farming produce",
    11: "Fletching materials",
    12: "Food and Drink",
    13: "Herblore materials",
    14: "Hunting equipment",
    15: "Hunting Produce",
    16: "Jewellery",
    17: "Mage armour",
    18: "Mage weapons",
    19: "Melee armour - low level",
    20: "Melee armour - mid level",
    21: "Melee armour - high level",
    22: "Melee weapons - low level",
    23: "Melee weapons - mid level",
    24: "Melee weapons - high level",
    25: "Mining and Smithing",
    26: "Potions",
    27: "Prayer armour",
    28: "Prayer materials",
    29: "Range armour",
    30: "Range weapons",
    31: "Runecrafting",
    32: "Runes, Spells and Teleports",
    33: "Seeds",
    34: "Summoning scrolls",
    35: "Tools and containers",
    36: "Woodcutting product",
    37: "Pocket items",
    38: "Stone spirits",
    39: "Salvage",
    40: "Firemaking products",
    41: "Archaeology materials",
    42: "Wood spirits",
    43: "Necromancy armour"
}

# Base URLs
BASE_CATEGORY_URL = "https://services.runescape.com/m=itemdb_rs/api/catalogue/category.json?category={}"
BASE_ITEMS_URL = "https://services.runescape.com/m=itemdb_rs/api/catalogue/items.json?category={}&alpha={}&page={}"

# Configuration
OUTPUT_DIR = "category_logs"  # Directory to store category-specific logs
LOG_DIR = "logs"              # Directory to store general logs and progress
PROGRESS_FILE = os.path.join(LOG_DIR, "processed_categories.json")  # File to track processed categories
REQUEST_DELAY = 0.5           # Base delay between requests in seconds
MAX_INCREMENTAL_RETRIES = 5  # Maximum number of retries for blank responses

# Ensure output directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,  # Set to INFO for general logs
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "item_categories.log")),
        logging.StreamHandler()  # Logs also printed to console
    ]
)

# Logger for failed items
failed_logger = logging.getLogger("failed_items")
failed_logger.setLevel(logging.ERROR)
failed_handler = logging.FileHandler(os.path.join(LOG_DIR, "failed_items.log"))
failed_handler.setLevel(logging.ERROR)
failed_formatter = logging.Formatter("%(asctime)s - %(message)s")
failed_handler.setFormatter(failed_formatter)
failed_logger.addHandler(failed_handler)

# Database Configuration Path
DB_CONFIG_PATH = os.path.join(os.path.expanduser("~"), 'discordbot10s', 'dbconfig.json')

# ============================
# Helper Functions
# ============================

def load_db_config(config_path):
    """
    Load database configuration from a JSON file.
    The JSON file should have the following structure:
    {
        "username": "your_db_username",
        "password": "your_db_password",
        "host": "your_db_host",
        "port": "your_db_port",
        "database": "your_db_name"
    }
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logging.info("Database configuration loaded successfully.")
        return config
    except Exception as e:
        logging.error(f"Failed to load database configuration: {e}")
        raise

def create_db_engine(config):
    """Create a SQLAlchemy engine."""
    try:
        engine = create_engine(
            f"postgresql://{config['username']}:{config['password']}@"
            f"{config['host']}:{config['port']}/{config['database']}"
        )
        logging.info("Database engine created successfully.")
        return engine
    except Exception as e:
        logging.error(f"Failed to create database engine: {e}")
        raise

def is_valid_url(url):
    """
    Validates the given URL.
    Returns True if the URL has a valid scheme and netloc, False otherwise.
    """
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc, parsed.path])

def create_session():
    """
    Creates a requests Session with retry strategy and custom headers.
    Implements exponential backoff for retries.
    """
    session = requests.Session()
    retry = Retry(
        total=5,  # Total number of retries
        backoff_factor=1,  # Exponential backoff factor (1, 2, 4, 8, 16 seconds)
        status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP status codes
        allowed_methods=["GET"]  # Retry only on GET requests
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    # Set custom headers
    session.headers.update({
        "User-Agent": "RuneScapeItemCategorizer/1.0 (https://yourdomain.com/contact)",
        "Accept": "application/json"
    })

    return session

def fetch_json(url, session, max_incremental_retries=MAX_INCREMENTAL_RETRIES):
    """
    Fetch JSON data from a URL with retry handling.
    Implements incremental backoff for empty responses.
    """
    if not is_valid_url(url):
        logging.error(f"Malformed URL detected: {url}")
        failed_logger.error(f"Invalid URL: {url}")
        return None

    incremental_retries = 0
    wait_time = REQUEST_DELAY  # Start with the base delay

    while incremental_retries <= max_incremental_retries:
        try:
            response = session.get(url, timeout=10)
            logging.debug(f"Fetching URL: {url}")
            print(f"Fetching URL: {url}")

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                logging.warning(f"Rate limited. Retrying after {retry_after} seconds for URL: {url}")
                print(f"Rate limited. Retrying after {retry_after} seconds for URL: {url}")
                time.sleep(retry_after)
                incremental_retries += 1
                continue  # Retry after waiting

            response.raise_for_status()

            if response.content:
                try:
                    data = response.json()
                    logging.info(f"Successfully fetched data from {url}")
                    return data
                except ValueError as json_err:
                    logging.error(f"JSON decoding failed for URL: {url} - {json_err}")
                    print(f"JSON decoding failed for URL: {url} - {json_err}")
                    failed_logger.error(f"JSON Decode Error for URL: {url} - {json_err}")
                    return None
            else:
                # Empty response, likely rate limited or server issue
                if incremental_retries < max_incremental_retries:
                    logging.warning(f"Empty response for URL: {url}. Retrying after {wait_time} seconds...")
                    print(f"Empty response for URL: {url}. Retrying after {wait_time} seconds...")
                    time.sleep(wait_time)
                    wait_time = min(wait_time * 2, 60)  # Exponential backoff up to 60 seconds
                    incremental_retries += 1
                    continue
                else:
                    logging.error(f"Empty response after {max_incremental_retries} retries for URL: {url}")
                    print(f"Empty response after {max_incremental_retries} retries for URL: {url}")
                    failed_logger.error(f"Empty Response for URL: {url} after {max_incremental_retries} retries")
                    return None
        except requests.exceptions.HTTPError as http_err:
            if response.status_code in [500, 502, 503, 504]:
                # Server errors, retry
                if incremental_retries < max_incremental_retries:
                    logging.warning(f"HTTP error {response.status_code} for URL: {url}. Retrying after {wait_time} seconds...")
                    print(f"HTTP error {response.status_code} for URL: {url}. Retrying after {wait_time} seconds...")
                    time.sleep(wait_time)
                    wait_time = min(wait_time * 2, 60)
                    incremental_retries += 1
                    continue
            # For other HTTP errors, do not retry
            logging.error(f"HTTP error occurred for URL: {url} - {http_err}")
            print(f"HTTP error occurred for URL: {url} - {http_err}")
            failed_logger.error(f"HTTP Error for URL: {url} - {http_err}")
            return None
        except requests.exceptions.RequestException as req_err:
            if incremental_retries < max_incremental_retries:
                logging.warning(f"Request exception for URL: {url} - {req_err}. Retrying after {wait_time} seconds...")
                print(f"Request exception for URL: {url} - {req_err}. Retrying after {wait_time} seconds...")
                time.sleep(wait_time)
                wait_time = min(wait_time * 2, 60)
                incremental_retries += 1
                continue
            else:
                logging.error(f"Request exception after {max_incremental_retries} retries for URL: {url} - {req_err}")
                print(f"Request exception after {max_incremental_retries} retries for URL: {url} - {req_err}")
                failed_logger.error(f"Request Exception for URL: {url} after {max_incremental_retries} retries - {req_err}")
                return None
        except ValueError as json_err:
            logging.error(f"JSON decoding failed for URL: {url} - {json_err}")
            print(f"JSON decoding failed for URL: {url} - {json_err}")
            failed_logger.error(f"JSON Decode Error for URL: {url} - {json_err}")
            return None

    # If all retries failed
    logging.error(f"Failed to fetch JSON from URL: {url} after {max_incremental_retries} retries")
    print(f"Failed to fetch JSON from URL: {url} after {max_incremental_retries} retries")
    failed_logger.error(f"Failed to fetch JSON from URL: {url} after {max_incremental_retries} retries")
    return None

def get_total_pages(items_count, items_per_page=12):
    """
    Calculate the total number of pages based on items count.
    """
    return ceil(items_count / items_per_page)

def sanitize_filename(name):
    """
    Sanitize the filename by replacing or removing invalid characters.
    """
    return "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in name).strip()

def load_progress(progress_file):
    """
    Load the progress from a JSON file.
    Returns a set of processed category IDs.
    """
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                processed = set(json.load(f))
            logging.info(f"Loaded progress from {progress_file}. {len(processed)} categories already processed.")
            return processed
        except Exception as e:
            logging.error(f"Failed to load progress file {progress_file}: {e}")
            return set()
    else:
        logging.info(f"No progress file found. Starting fresh.")
        return set()

def save_progress(progress_file, processed_categories):
    """
    Save the processed categories to a JSON file.
    """
    try:
        with open(progress_file, 'w') as f:
            json.dump(list(processed_categories), f, indent=4)
        logging.info(f"Progress saved to {progress_file}. Total processed categories: {len(processed_categories)}.")
    except Exception as e:
        logging.error(f"Failed to save progress to {progress_file}: {e}")

def process_category(category_id, category_name, session, session_db):
    """
    Process a single category: fetch items and update the database.
    """
    logging.info(f"Processing Category {category_id}: {category_name}")
    print(f"\nProcessing Category {category_id}: {category_name}")

    category_url = BASE_CATEGORY_URL.format(category_id)
    logging.debug(f"Category URL: {category_url}")
    print(f"Category URL: {category_url}")

    category_data = fetch_json(category_url, session)

    if not category_data:
        logging.error(f"Failed to retrieve data for category {category_id}")
        print(f"Failed to retrieve data for category {category_id}")
        failed_logger.error(f"{category_id},{category_name},Category Data Fetch Failed")
        return False  # Indicate failure

    alpha_list = category_data.get("alpha", [])
    logging.debug(f"Alpha list for category {category_id}: {alpha_list}")
    print(f"Alpha list: {alpha_list}")

    # Initialize list for this category
    item_ids = []

    for alpha_entry in alpha_list:
        letter = alpha_entry.get("letter")
        items_count = alpha_entry.get("items", 0)

        if items_count == 0:
            logging.info(f"  Letter '{letter}' has no items.")
            print(f"  Letter '{letter}' has no items.")
            continue  # No items for this letter

        # Encode '#' as '%23' if necessary
        encoded_letter = "%23" if letter == "#" else quote(letter.lower())

        # Determine the number of items per page
        items_per_page = 12  # Assuming 12 items per page based on previous logs
        total_pages = get_total_pages(items_count, items_per_page)

        logging.info(f"  Letter '{letter}' has {items_count} items across {total_pages} pages.")
        print(f"  Letter '{letter}' has {items_count} items across {total_pages} pages.")

        # Iterate through pages with progress bar
        for page in tqdm(range(1, total_pages + 1), desc=f"    Fetching pages for '{letter}'", leave=False):
            items_url = BASE_ITEMS_URL.format(category_id, encoded_letter, page)
            items_data = fetch_json(items_url, session)

            if not items_data:
                logging.error(f"    Failed to fetch items for category {category_id}, letter '{letter}', page {page}")
                print(f"    Failed to fetch items for category {category_id}, letter '{letter}', page {page}")
                failed_logger.error(f"{category_id},{category_name},Letter {letter},Page {page},Items Data Fetch Failed")
                continue

            items = items_data.get("items", [])

            if not items:
                logging.info(f"      No items found on page {page} for letter '{letter}'.")
                print(f"      No items found on page {page} for letter '{letter}'.")
                continue

            # Collect item IDs
            for item in items:
                item_id = item.get("id")
                if item_id:
                    item_ids.append(item_id)

            time.sleep(REQUEST_DELAY)  # Respectful delay

    if not item_ids:
        logging.warning(f"No items found for category {category_id}: {category_name}")
        print(f"No items found for category {category_id}: {category_name}")
        return True  # Category processed, even if no items

    # Perform bulk update for this category
    try:
        update_stmt = text("""
            UPDATE items
            SET category_id = :category_id
            WHERE id = ANY(:item_ids)
        """)
        result = session_db.execute(update_stmt, {"category_id": category_id, "item_ids": item_ids})
        session_db.commit()
        logging.info(f"Updated {result.rowcount} items for category ID {category_id}: {category_name}")
        print(f"Updated {result.rowcount} items for category ID {category_id}: {category_name}")
        return True  # Indicate success
    except Exception as e:
        session_db.rollback()
        logging.error(f"Failed to update database for category {category_id}: {e}")
        print(f"Failed to update database for category {category_id}: {e}")
        failed_logger.error(f"{category_id},{category_name},Database Update Failed,{e}")
        return False  # Indicate failure

# ============================
# Main Execution Function
# ============================

def main():
    """Main function to execute the item categorization."""
    try:
        logging.info("Starting item categorization process...")
        print("Starting item categorization process...\n")

        # Load database configuration
        config = load_db_config(DB_CONFIG_PATH)

        # Create database engine
        engine = create_db_engine(config)

        # Create a new database session
        Session = sessionmaker(bind=engine)
        session_db = Session()

        # Create a requests session
        session_http = create_session()

        # Load progress
        processed_categories = load_progress(PROGRESS_FILE)

        # Iterate through categories
        for category_id, category_name in tqdm(CATEGORY_MAPPING.items(), desc="Processing Categories"):
            if category_id in processed_categories:
                logging.info(f"Skipping already processed category {category_id}: {category_name}")
                print(f"Skipping already processed category {category_id}: {category_name}")
                continue  # Skip already processed categories

            success = process_category(category_id, category_name, session_http, session_db)

            if success:
                # Mark category as processed
                processed_categories.add(category_id)
                save_progress(PROGRESS_FILE, processed_categories)
            else:
                logging.error(f"Failed to process category {category_id}: {category_name}. Continuing with next category.")
                print(f"Failed to process category {category_id}: {category_name}. Continuing with next category.")

    except KeyboardInterrupt:
        logging.warning("Script interrupted by user.")
        print("\nScript interrupted by user. Exiting gracefully.")
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
        print(f"An unexpected error occurred: {e}")
    finally:
        # Close the HTTP session
        session_http.close()
        logging.info("HTTP session closed.")
        print("HTTP session closed.")

        # Close the database session
        session_db.close()
        logging.info("Database session closed.")
        print("Database session closed.")

        logging.info("Item categorization process completed.")
        print("Item categorization process completed.")

# ============================
# Progress Tracking Functions
# ============================

def load_progress(progress_file):
    """
    Load the progress from a JSON file.
    Returns a set of processed category IDs.
    """
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                processed = set(json.load(f))
            logging.info(f"Loaded progress from {progress_file}. {len(processed)} categories already processed.")
            return processed
        except Exception as e:
            logging.error(f"Failed to load progress file {progress_file}: {e}")
            return set()
    else:
        logging.info(f"No progress file found. Starting fresh.")
        return set()

def save_progress(progress_file, processed_categories):
    """
    Save the processed categories to a JSON file.
    """
    try:
        with open(progress_file, 'w') as f:
            json.dump(list(processed_categories), f, indent=4)
        logging.info(f"Progress saved to {progress_file}. Total processed categories: {len(processed_categories)}.")
    except Exception as e:
        logging.error(f"Failed to save progress to {progress_file}: {e}")

# ============================
# Entry Point
# ============================

if __name__ == "__main__":
    main()

