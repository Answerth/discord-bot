import requests
import json

# Define the URL of the item database
url = "https://chisel.weirdgloop.org/gazproj/gazbot/rs_dump.json"
output_file = "rs_item_database.json"

# Download the JSON file
response = requests.get(url)
if response.status_code == 200:
    with open(output_file, 'w') as f:
        json.dump(response.json(), f, indent=4)
    print(f"Database successfully downloaded and saved as {output_file}")
else:
    print(f"Failed to download data. Status code: {response.status_code}")
