import requests
import os
import json
import time
from math import ceil
from urllib.parse import quote, urlparse
from tqdm import tqdm
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Constants
BASE_CATEGORY_URL = "https://services.runescape.com/m=itemdb_rs/api/catalogue/category.json?category={}"
BASE_ITEMS_URL = "https://services.runescape.com/m=itemdb_rs/api/catalogue/items.json?category={}&alpha={}&page={}"
BASE_DETAIL_URL = "https://services.runescape.com/m=itemdb_rs/api/catalogue/detail.json?item={}"

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

# Configuration
OUTPUT_DIR = "category_logs"
LOG_DIR = "logs"
TEST_RUN_CATEGORIES = list(CATEGORY_MAPPING.keys())[26:] # All category IDs for full run
REQUEST_DELAY = 0.5  # Base delay between requests in seconds

# Ensure output directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Logging Configuration
# Configure the main logger
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for detailed logs
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "item_downloader.log")),
        logging.StreamHandler()  # This ensures logs are also printed to the console
    ]
)

# Configure a separate logger for failed items
failed_logger = logging.getLogger("failed_items")
failed_logger.setLevel(logging.ERROR)
failed_handler = logging.FileHandler(os.path.join(LOG_DIR, "failed_items.log"))
failed_handler.setLevel(logging.ERROR)
failed_formatter = logging.Formatter("%(asctime)s - %(message)s")
failed_handler.setFormatter(failed_formatter)
failed_logger.addHandler(failed_handler)

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
    """
    session = requests.Session()
    retry = Retry(
        total=5,  # Total number of retries
        backoff_factor=1,  # Exponential backoff factor (1, 2, 4, 8, 16 seconds)
        status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP status codes
        allowed_methods=["GET"]  # Updated parameter name from method_whitelist
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    # Set custom headers
    session.headers.update({
        "User-Agent": "RuneScapeItemDownloader/1.0 (https://yourdomain.com/contact)",
        "Accept": "application/json"
    })
    
    return session

def fetch_json(url, session, max_incremental_retries=5):
    """
    Fetch JSON data from a URL with retry handling.
    Implements incremental backoff for empty responses.
    """
    # Validate URL
    if not is_valid_url(url):
        logging.error(f"Malformed URL detected: {url}")
        print(f"Malformed URL detected: {url}")
        # Log without context
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
                    logging.debug(f"Received data: {data}")
                    return data
                except ValueError as json_err:
                    logging.error(f"JSON decoding failed for URL: {url} - {json_err}")
                    print(f"JSON decoding failed for URL: {url} - {json_err}")
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
                return None
        except ValueError as json_err:
            logging.error(f"JSON decoding failed for URL: {url} - {json_err}")
            print(f"JSON decoding failed for URL: {url} - {json_err}")
            return None

    # If all retries failed
    logging.error(f"Failed to fetch JSON from URL: {url} after {max_incremental_retries} retries")
    print(f"Failed to fetch JSON from URL: {url} after {max_incremental_retries} retries")
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

def process_category(category_id, category_name, session):
    """
    Process a single category: fetch items and their details, then log them.
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
        return
    
    alpha_list = category_data.get("alpha", [])
    logging.debug(f"Alpha list: {alpha_list}")
    print(f"Alpha list: {alpha_list}")
    
    # Prepare log file
    sanitized_name = sanitize_filename(category_name)
    log_filename = os.path.join(OUTPUT_DIR, f"category_{category_id}_{sanitized_name}.log")
    
    # Load existing item IDs to prevent duplicates
    processed_item_ids = set()
    if os.path.exists(log_filename):
        with open(log_filename, "r", encoding="utf-8") as log_file:
            for line in log_file:
                try:
                    data = json.loads(line)
                    item_id = data.get("item", {}).get("id")
                    if item_id:
                        processed_item_ids.add(item_id)
                except json.JSONDecodeError:
                    continue  # Skip malformed lines
    
    with open(log_filename, "a", encoding="utf-8") as log_file:
        # Iterate through each letter
        for alpha_entry in alpha_list:
            letter = alpha_entry.get("letter")
            items_count = alpha_entry.get("items", 0)
            
            if items_count == 0:
                logging.info(f"  Letter '{letter}' has no items.")
                print(f"  Letter '{letter}' has no items.")
                continue  # No items for this letter
            
            # Encode '#' as '%23' if necessary
            if letter == "#":
                encoded_letter = "%23"
            else:
                encoded_letter = quote(letter.lower())
            
            total_pages = get_total_pages(items_count)
            
            logging.info(f"  Letter '{letter}' has {items_count} items across {total_pages} pages.")
            print(f"  Letter '{letter}' has {items_count} items across {total_pages} pages.")
            
            # Iterate through pages with progress bar
            for page in tqdm(range(1, total_pages + 1), desc="    Fetching pages", leave=False):
                items_url = BASE_ITEMS_URL.format(category_id, encoded_letter, page)
                
                # Validate URL before making the request
                if not is_valid_url(items_url):
                    logging.error(f"Malformed URL detected: {items_url}")
                    print(f"Malformed URL detected: {items_url}")
                    # Log to failed_items.log with additional context
                    failed_logger.error(f"{category_id},{category_name},Invalid URL,{items_url}")
                    continue  # Skip to the next page
                
                items_data = fetch_json(items_url, session)
                
                if not items_data:
                    logging.error(f"    Failed to fetch items for category {category_id}, letter '{letter}', page {page}")
                    print(f"    Failed to fetch items for category {category_id}, letter '{letter}', page {page}")
                    continue
                
                items = items_data.get("items", [])
                
                if not items:
                    logging.info(f"      No items found on page {page} for letter '{letter}'.")
                    print(f"      No items found on page {page} for letter '{letter}'.")
                    continue
                
                # Iterate through items
                for item in items:
                    item_id = item.get("id")
                    if not item_id or item_id in processed_item_ids:
                        continue  # Skip duplicates
                    
                    detail_url = BASE_DETAIL_URL.format(item_id)
                    
                    # Validate detail URL
                    if not is_valid_url(detail_url):
                        logging.error(f"Malformed detail URL detected: {detail_url}")
                        print(f"Malformed detail URL detected: {detail_url}")
                        # Log to failed_items.log with additional context
                        failed_logger.error(f"{category_id},{category_name},{item_id},Invalid Detail URL,{detail_url}")
                        continue  # Skip to the next item
                    
                    detail_data = fetch_json(detail_url, session)
                    
                    if not detail_data:
                        logging.error(f"      Failed to fetch details for item ID {item_id}")
                        print(f"      Failed to fetch details for item ID {item_id}")
                        # Log to failed_items.log
                        failed_logger.error(f"{category_id},{category_name},{item_id}")
                        continue
                    
                    # Write the detail JSON to the log file
                    log_file.write(json.dumps(detail_data) + "\n")
                    logging.debug(f"      Logged details for item ID {item_id}")
                    print(f"      Logged details for item ID {item_id}")
                    
                    # Add to processed IDs to prevent duplicates within the same run
                    processed_item_ids.add(item_id)
                    
                    time.sleep(REQUEST_DELAY)  # Respectful delay

def main():
    """
    Main function to process categories.
    """
    try:
        logging.info("Starting API data retrieval for Runescape items...")
        print("Starting API data retrieval for Runescape items...\n")
        
        session = create_session()
        
        for category_id in TEST_RUN_CATEGORIES:
            category_name = CATEGORY_MAPPING.get(category_id, f"Category_{category_id}")
            logging.debug(f"Processing category ID: {category_id}, Name: {category_name}")
            print(f"Processing category ID: {category_id}, Name: {category_name}")
            process_category(category_id, category_name, session)
    except KeyboardInterrupt:
        logging.warning("Script interrupted by user.")
        print("\nScript interrupted by user. Exiting gracefully.")
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
        print(f"An unexpected error occurred: {e}")
    
    logging.info("Full run completed.")
    print("\nFull run completed. Check the 'category_logs' directory for output files.")

if __name__ == "__main__":
    main()
