# fetch_and_flatten_test_concurrent.py
import argparse
import requests
import pandas as pd
from urllib.parse import quote
from datetime import datetime, timedelta
import os
import pickle
import asyncio
import aiohttp
import logging
from aiohttp import ClientSession, ClientTimeout
from asyncio import Semaphore

print("--concurrent flag to get all names concurrently")

# Configure logging to output to both console and file
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# File handler
log_dir = os.path.join(os.path.dirname(__file__), '../../logs')
os.makedirs(log_dir, exist_ok=True)
file_handler = logging.FileHandler(os.path.join(log_dir, 'fetch_and_flatten_test_concurrent.log'))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Constants
DEFAULT_CLAN_NAME = "10s"
ACTIVITIES_PICKLE = "activities_data.pkl"
MEMBERS_PICKLE = "members_data.pkl"
OUTPUT_DIR = "fetch_and_flatten_data_files"
CONCURRENT_REQUESTS = 10  # Limit for concurrent requests to prevent overloading


def fetch_clan_members(clan_name):
    """Fetch clan members from the Runescape clan hiscores."""
    url = f"http://services.runescape.com/m=clan-hiscores/members_lite.ws?clanName={quote(clan_name)}"
    logger.info(f"Fetching clan members from URL: {url}")
    response = requests.get(url)
    response.raise_for_status()  # Raise exception for HTTP errors
    data = response.text.strip().split("\n")

    members = []
    for line in data[1:]:  # Skip the header line
        name, rank, experience, kills = line.split(",")
        name = name.replace("\xa0", " ").strip()
        members.append({
            "name": name,
            "rank": rank.strip(),
            "experience": int(experience.strip()),
            "kills": int(kills.strip())
        })
    logger.info(f"Fetched {len(members)} clan members.")
    return pd.DataFrame(members)


def get_member_activities(member_name, number_of_activities=20):
    """Fetch activities for a single member (Serial Version)."""
    url = f"https://apps.runescape.com/runemetrics/profile/profile?user={quote(member_name)}&activities={number_of_activities}"
    logger.debug(f"Fetching activities for member: {member_name}")
    response = requests.get(url)
    if response.status_code != 200:
        logger.warning(f"Failed to fetch activities for {member_name}. Status Code: {response.status_code}")
        return pd.DataFrame()  # Return empty DataFrame on failure

    data = response.json()
    activities = data.get("activities", [])

    recent_activities = []
    for activity in activities:
        try:
            activity_date = datetime.strptime(activity["date"], "%d-%b-%Y %H:%M")
            recent_activities.append({
                "name": data.get("name", member_name),
                "date": activity["date"],
                "details": activity["details"],
                "text": activity["text"]
                #"activity_type": activity[None]
                #"status": activity[None]
            })
        except Exception as e:
            logger.error(f"Error parsing activity for {member_name}: {e}")
            continue
    logger.debug(f"Retrieved {len(recent_activities)} activities for {member_name}")
    return pd.DataFrame(recent_activities)


async def fetch_member_activities_async(session, member_name, number_of_activities=20, semaphore=None):
    """Fetch activities for a single member asynchronously."""
    url = f"https://apps.runescape.com/runemetrics/profile/profile?user={quote(member_name)}&activities={number_of_activities}"
    if semaphore:
        async with semaphore:
            return await _fetch_activity(session, member_name, url)
    else:
        return await _fetch_activity(session, member_name, url)


async def _fetch_activity(session, member_name, url):
    """Helper function to perform the actual HTTP request."""
    try:
        async with session.get(url) as response:
            if response.status != 200:
                logger.warning(f"Failed to fetch activities for {member_name}. Status Code: {response.status}")
                return pd.DataFrame()
            data = await response.json()
            activities = data.get("activities", [])

            recent_activities = []
            for activity in activities:
                try:
                    activity_date = datetime.strptime(activity["date"], "%d-%b-%Y %H:%M")
                    recent_activities.append({
                        "name": data.get("name", member_name),
                        "date": activity["date"],
                        "details": activity["details"],
                        "text": activity["text"]
                        #"activity_type": activity[None]
                        #"status": activity[None]
                    })
                except Exception as e:
                    logger.error(f"Error parsing activity for {member_name}: {e}")
                    continue
            logger.info(f"Retrieved {len(recent_activities)} activities for {member_name}")
            return pd.DataFrame(recent_activities)
    except Exception as e:
        logger.error(f"Exception occurred while fetching activities for {member_name}: {e}")
        return pd.DataFrame()


async def fetch_all_activities_concurrently(members, number_of_activities=20):
    """Fetch activities for all members concurrently."""
    logger.info("Starting concurrent fetching of member activities.")
    timeout = ClientTimeout(total=60)  # Adjust as needed
    semaphore = Semaphore(CONCURRENT_REQUESTS)
    async with ClientSession(timeout=timeout) as session:
        tasks = [
            fetch_member_activities_async(session, member, number_of_activities, semaphore)
            for member in members
        ]
        results = await asyncio.gather(*tasks)
    logger.info("Completed concurrent fetching of member activities.")
    return pd.concat(results, ignore_index=True)


def load_recent_members(data_dir, days=7):
    """Load recently active members based on activities data."""
    activities_path = os.path.join(data_dir, OUTPUT_DIR, ACTIVITIES_PICKLE)
    if not os.path.exists(activities_path):
        logger.info("Activities data not found. Fetching all members.")
        return None  # Indicate that all members should be fetched

    activities_df = pd.read_pickle(activities_path)
    activities_df['date'] = pd.to_datetime(activities_df['date'], format="%d-%b-%Y %H:%M")
    recent_threshold = datetime.now() - timedelta(days=days)
    recent_members = activities_df[activities_df['date'] >= recent_threshold]['name'].unique().tolist()
    logger.info(f"Identified {len(recent_members)} recently active members.")
    return recent_members


async def main_async(clan_name, active_only, concurrent):
    """Main asynchronous function to orchestrate data fetching and saving."""
    data_dir = os.path.dirname(__file__)
    output_dir = os.path.join(data_dir, OUTPUT_DIR)

    # Fetch clan members
    members_df = fetch_clan_members(clan_name)

    if active_only:
        recent_members = load_recent_members(data_dir)
        if recent_members is not None:
            members_df = members_df[members_df['name'].isin(recent_members)]
            logger.info(f"Fetching activities for {len(members_df)} recently active members.")
        else:
            logger.info("Fetching activities for all members.")
    else:
        logger.info("Fetching activities for all members.")

    # Get list of member names
    names = members_df["name"].tolist()
    logger.info(f"Total members to fetch activities for: {len(names)}")

    if concurrent:
        # Run the asynchronous concurrent fetching
        activities_df = await fetch_all_activities_concurrently(names, number_of_activities=20)
    else:
        # Run the serial fetching
        logger.info("Starting serial fetching of member activities.")
        activities_df = pd.DataFrame()
        for name in names:
            activities = get_member_activities(name, number_of_activities=20)
            logger.info(f"Retrieved {len(activities)} activities for {name}")
            activities_df = pd.concat([activities_df, activities], ignore_index=True)
        logger.info("Completed serial fetching of member activities.")

    # Save DataFrames
    save_dataframes(members_df, activities_df, output_dir)
    logger.info("Data insertion process completed.")


def save_dataframes(members_df, activities_df, output_dir):
    """Save DataFrames to pickle files."""
    os.makedirs(output_dir, exist_ok=True)
    members_path = os.path.join(output_dir, MEMBERS_PICKLE)
    activities_path = os.path.join(output_dir, ACTIVITIES_PICKLE)
    activities_df['activity_type'] = None
    activities_df['status'] = None
    members_df.to_pickle(members_path)
    activities_df.to_pickle(activities_path)
    logger.info(f"Data saved to {members_path} and {activities_path}")


def load_recent_members(data_dir, days=7):
    """Load recently active members based on activities data."""
    activities_path = os.path.join(data_dir, OUTPUT_DIR, ACTIVITIES_PICKLE)
    if not os.path.exists(activities_path):
        logger.info("Activities data not found. Fetching all members.")
        return None  # Indicate that all members should be fetched

    activities_df = pd.read_pickle(activities_path)
    activities_df['date'] = pd.to_datetime(activities_df['date'], format="%d-%b-%Y %H:%M")
    #activities_df['activity_type'] = None
    #activities_df['status'] = None
    recent_threshold = datetime.now() - timedelta(days=days)
    recent_members = activities_df[activities_df['date'] >= recent_threshold]['name'].unique().tolist()
    logger.info(f"Identified {len(recent_members)} recently active members.")
    return recent_members


def main(clan_name, active_only, concurrent):
    """Entry point for the script."""
    try:
        asyncio.run(main_async(clan_name, active_only, concurrent))
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch and flatten clan member data.")
    parser.add_argument('--active', action='store_true', help='Fetch activities for recently active members only.')
    parser.add_argument('--concurrent', action='store_true', help='Enable concurrent fetching of member activities.')
    parser.add_argument('--clan', type=str, default=DEFAULT_CLAN_NAME, help='Name of the clan to fetch data for.')
    args = parser.parse_args()

    main(clan_name=args.clan, active_only=args.active, concurrent=args.concurrent)

