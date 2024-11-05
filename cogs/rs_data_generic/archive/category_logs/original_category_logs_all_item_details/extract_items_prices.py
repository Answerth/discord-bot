import json
import os
import csv

# Configuration
LOG_FILE = "./category_0_Miscellaneous.log"  # Path to your log file
OUTPUT_CSV = "category_0_Miscellaneous_prices.csv"        # Output CSV file

def extract_items_and_prices(log_file_path, output_csv_path):
    """
    Extracts item names and their current prices from the log file and writes them to a CSV.
    """
    if not os.path.exists(log_file_path):
        print(f"Log file not found: {log_file_path}")
        return

    with open(log_file_path, "r", encoding="utf-8") as log_file, \
         open(output_csv_path, "w", encoding="utf-8", newline='') as csv_file:
        
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["Item ID", "Item Name", "Current Price"])  # Header

        for line_number, line in enumerate(log_file, start=1):
            try:
                data = json.loads(line)
                item = data.get("item", {})
                item_id = item.get("id", "N/A")
                item_name = item.get("name", "N/A")
                current = item.get("current", {})
                price = current.get("price", "N/A")
                
                # Ensure price is a string for consistency
                if isinstance(price, (int, float)):
                    price = str(price)
                
                csv_writer.writerow([item_id, item_name, price])
            except json.JSONDecodeError as e:
                print(f"JSON decode error at line {line_number}: {e}")
                continue  # Skip malformed lines

    print(f"Extraction complete. Data saved to '{output_csv_path}'.")

if __name__ == "__main__":
    extract_items_and_prices(LOG_FILE, OUTPUT_CSV)
