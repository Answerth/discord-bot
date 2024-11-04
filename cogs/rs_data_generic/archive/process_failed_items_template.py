import csv
import requests
import json
import time

LOG_DIR = "logs"
FAILED_ITEMS_LOG = os.path.join(LOG_DIR, "failed_items.log")
CATEGORY_LOG_DIR = "category_logs"

def reprocess_failed_items():
    if not os.path.exists(FAILED_ITEMS_LOG):
        print("No failed items to process.")
        return
    
    with open(FAILED_ITEMS_LOG, "r", encoding="utf-8") as failed_log:
        reader = csv.reader(failed_log)
        for row in reader:
            if len(row) >= 3:
                category_id, category_name, item_id = row[:3]
                detail_url = f"https://services.runescape.com/m=itemdb_rs/api/catalogue/detail.json?item={item_id}"
                
                # Make the request
                response = requests.get(detail_url, timeout=10)
                if response.status_code == 200 and response.content:
                    detail_data = response.json()
                    # Append to the category log
                    sanitized_name = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in category_name).strip()
                    log_filename = os.path.join(CATEGORY_LOG_DIR, f"category_{category_id}_{sanitized_name}.log")
                    with open(log_filename, "a", encoding="utf-8") as log_file:
                        log_file.write(json.dumps(detail_data) + "\n")
                    print(f"Successfully reprocessed item ID {item_id}")
                else:
                    print(f"Failed to reprocess item ID {item_id}")
                    # Optionally, log again or handle accordingly
                time.sleep(REQUEST_DELAY)  # Respectful delay

if __name__ == "__main__":
    reprocess_failed_items()
