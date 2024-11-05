# fetch_and_flatten_data.py
import requests
import pandas as pd
from urllib.parse import quote
from datetime import datetime, timedelta
import os

def fetch_clan_members(clan_name):
    url = f"http://services.runescape.com/m=clan-hiscores/members_lite.ws?clanName={quote(clan_name)}"
    response = requests.get(url)
    data = response.text.strip().split("\n")

    members = []
    for line in data[1:]:
        name, rank, experience, kills = line.split(",")
        name = name.replace("\xa0", " ")
        members.append({
            "name": name,
            "rank": rank,
            "experience": int(experience),
            "kills": int(kills)
        })
    return pd.DataFrame(members)

def get_member_activities(member_name, number_of_activities=20):
    url = f"https://apps.runescape.com/runemetrics/profile/profile?user={quote(member_name)}&activities={number_of_activities}"
    response = requests.get(url)

    data = response.json()
    activities = data.get("activities", [])

    recent_activities = []
    for activity in activities:
        activity_date = datetime.strptime(activity["date"], "%d-%b-%Y %H:%M")
        recent_activities.append({
            "name": data.get("name", member_name),
            "date": activity["date"],
            "details": activity["details"],
            "text": activity["text"]
        })
    return pd.DataFrame(recent_activities)

# Fetch data
members_df = fetch_clan_members("10s")

# Initialize an empty DataFrame to hold all activities
all_activities_df = pd.DataFrame()

# Get activities for each member and concatenate
names = members_df["name"].tolist()
for name in names:
    activities_df = get_member_activities(name)
    print(f"Retrieved {len(activities_df)} activities for {name}")
    all_activities_df = pd.concat([all_activities_df, activities_df], ignore_index=True)

#activities_df = get_member_activities("ButtBandiit")

# Save DataFrames to .pkl files in the same directory
data_dir = os.path.dirname(__file__)

print(members_df)
print(all_activities_df)

members_df.to_pickle(os.path.join(data_dir, "members_data.pkl"))
all_activities_df.to_pickle(os.path.join(data_dir, "activities_data.pkl"))

print("Data saved to members_data.pkl and activities_data.pkl")
