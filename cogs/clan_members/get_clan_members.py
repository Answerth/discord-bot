import requests
from urllib.parse import quote
from datetime import datetime, timedelta

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
    print(members)
    return members

def get_member_activities(member_name, number_of_activities = 5):
    thirty_days_ago = datetime.now() - timedelta(days=30)
    if number_of_activities > 10:
        number_of_activities = 10
    url = f"https://apps.runescape.com/runemetrics/profile/profile?user={quote(member_name)}&activities={number_of_activities}"
    response = requests.get(url)

    # Parse JSON response
    data = response.json()

    # Extract 'name' and 'activities', handle missing 'activities' gracefully
    name = data.get("name", member_name)
    activities = data.get("activities", [])

    # Filter activities to include only those within the last 30 days
    recent_activities = []
    for activity in activities:
        activity_date = datetime.strptime(activity["date"], "%d-%b-%Y %H:%M")

        if activity_date >= thirty_days_ago:
            recent_activities.append(activity)

        #if len(recent_activities) >= 10:
        #    break

    return {
        "name": name,
        "activities": recent_activities
    }


#fetch_clan_members("10s")
#member_activity = get_member_activities("ButtBandiit")
#print(member_activity) 

