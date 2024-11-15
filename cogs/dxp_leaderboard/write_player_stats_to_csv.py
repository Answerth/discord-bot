import asyncio
import aiohttp
from aiohttp import ClientSession, ClientTimeout
from asyncio import Semaphore
from urllib.parse import quote
import pandas as pd
import logging
import time
import random
import os
from datetime import datetime
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("member_stats.log"),
        logging.StreamHandler()
    ]
)

# Constants
CONCURRENT_REQUESTS = 10
REQUEST_TIMEOUT = 120  # seconds

SKILLS = [
    "Overall", "Attack", "Defence", "Strength", "Constitution", "Ranged", "Prayer",
    "Magic", "Cooking", "Woodcutting", "Fletching", "Fishing", "Firemaking", "Crafting",
    "Smithing", "Mining", "Herblore", "Agility", "Thieving", "Slayer", "Farming",
    "Runecrafting", "Hunter", "Construction", "Summoning", "Dungeoneering", "Divination",
    "Invention", "Archaeology", "Necromancy"
]

ACTIVITIES = [
    "Bounty Hunter", "B.H. Rogues", "Dominion Tower", "The Crucible", "Castle Wars games",
    "B.A. Attackers", "B.A. Defenders", "B.A. Collectors", "B.A. Healers", "Duel Tournament",
    "Mobilising Armies", "Conquest", "Fist of Guthix", "GG: Athletics", "GG: Resource Race",
    "WE2: Armadyl Lifetime Contrib", "WE2: Bandos Lifetime Contrib",
    "WE2: Armadyl PvP kills", "WE2: Bandos PvP kills", "Heist Guard Level", "Heist Robber Level",
    "CFP: 5 game average", "AF15: Cow Tipping", "AF15: Rat kills post-quest",
    "RuneScore", "Clue Scrolls Easy", "Clue Scrolls Medium", "Clue Scrolls Hard",
    "Clue Scrolls Elite", "Clue Scrolls Master"
]

level_exp_dict = {
    1: 0, 2: 83, 3: 174, 4: 276, 5: 388, 6: 512, 7: 650, 8: 801, 9: 969, 10: 1154,
    11: 1358, 12: 1584, 13: 1833, 14: 2107, 15: 2411, 16: 2746, 17: 3115, 18: 3523, 19: 3973, 20: 4470,
    21: 5018, 22: 5624, 23: 6291, 24: 7028, 25: 7842, 26: 8740, 27: 9730, 28: 10824, 29: 12031, 30: 13363,
    31: 14833, 32: 16456, 33: 18247, 34: 20224, 35: 22406, 36: 24815, 37: 27473, 38: 30408, 39: 33648, 40: 37224,
    41: 41171, 42: 45529, 43: 50339, 44: 55649, 45: 61512, 46: 67983, 47: 75127, 48: 83014, 49: 91721, 50: 101333,
    51: 111945, 52: 123660, 53: 136594, 54: 150872, 55: 166636, 56: 184040, 57: 203254, 58: 224466, 59: 247886, 60: 273742,
    61: 302288, 62: 333804, 63: 368599, 64: 407015, 65: 449428, 66: 496254, 67: 547953, 68: 605032, 69: 668051, 70: 737627,
    71: 814445, 72: 899257, 73: 992895, 74: 1096278, 75: 1210421, 76: 1336443, 77: 1475581, 78: 1629200, 79: 1798808, 80: 1986068,
    81: 2192818, 82: 2421087, 83: 2673114, 84: 2951373, 85: 3258594, 86: 3597792, 87: 3972294, 88: 4385776, 89: 4842295, 90: 5346332,
    91: 5902831, 92: 6517253, 93: 7195629, 94: 7944614, 95: 8771558, 96: 9684577, 97: 10692629, 98: 11805606, 99: 13034431, 100: 14391160,
    101: 15889109, 102: 17542976, 103: 19368992, 104: 21385073, 105: 23611006, 106: 26068632, 107: 28782069, 108: 31777943, 109: 35085654,
    110: 38737661, 111: 42769801, 112: 47221641, 113: 52136869, 114: 57563718, 115: 63555443, 116: 70170840, 117: 77474828, 118: 85539082, 119: 94442737, 120: 104273167
}

elite_skills_exp = {
    1: 0, 2: 830, 3: 1861, 4: 2902, 5: 3980, 6: 5126, 7: 6390, 8: 7787, 9: 9400, 10: 11275,
    11: 13605, 12: 16372, 13: 19656, 14: 23546, 15: 28138, 16: 33520, 17: 39809, 18: 47109, 19: 55535, 20: 64802,
    21: 77190, 22: 90811, 23: 106221, 24: 123573, 25: 143025, 26: 164742, 27: 188893, 28: 215651, 29: 245196, 30: 277713,
    31: 316311, 32: 358547, 33: 404634, 34: 454796, 35: 509259, 36: 568254, 37: 632019, 38: 700797, 39: 774834, 40: 854383,
    41: 946227, 42: 1044569, 43: 1149696, 44: 1261903, 45: 1381488, 46: 1508756, 47: 1644015, 48: 1787581, 49: 1939773, 50: 2100917,
    51: 2283490, 52: 2476369, 53: 2679907, 54: 2894505, 55: 3120508, 56: 3358307, 57: 3608290, 58: 3870846, 59: 4146374, 60: 4435275,
    61: 4758122, 62: 5096111, 63: 5449685, 64: 5819299, 65: 6205407, 66: 6608473, 67: 7028964, 68: 7467354, 69: 7924122, 70: 8399751,
    71: 8925664, 72: 9472665, 73: 10041285, 74: 10632061, 75: 11245538, 76: 11882262, 77: 12542789, 78: 13227679, 79: 13937496, 80: 14672812,
    81: 15478994, 82: 16313404, 83: 17176661, 84: 18069395, 85: 18992239, 86: 19945833, 87: 20930821, 88: 21947856, 89: 22997593, 90: 24080695,
    91: 25259906, 92: 26475754, 93: 27728955, 94: 29020233, 95: 30350318, 96: 31719944, 97: 33129852, 98: 34580790, 99: 36073511, 100: 37608773,
    101: 39270442, 102: 40978509, 103: 42733789, 104: 44537107, 105: 46389292, 106: 48291180, 107: 50243611, 108: 52247435, 109: 54303504, 110: 56412678,
    111: 58575823, 112: 60793812, 113: 63067521, 114: 65397835, 115: 67785643, 116: 70231841, 117: 72737330, 118: 75303019, 119: 77929820, 120: 80618654,
    121: 83370445, 122: 86186124, 123: 89066630, 124: 92012904, 125: 95025896, 126: 98106559, 127: 101255855, 128: 104474750, 129: 107764216, 130: 111125230,
    131: 114558777, 132: 118065845, 133: 121647430, 134: 125304532, 135: 129038159, 136: 132849323, 137: 136739041, 138: 140708338, 139: 144758242, 140: 148889790,
    141: 153104021, 142: 157401983, 143: 161784728, 144: 166253312, 145: 170808801, 146: 175452262, 147: 180184770, 148: 185007406, 149: 189921255, 150: 194927409
}

def remap_levels(experience_value, exp_dict):
    """Map experience to level based on the provided experience dictionary."""
    sorted_levels = sorted(exp_dict.items())
    experience_value_no_commas = experience_value.replace(",", "")
    try:
        experience_value = int(experience_value_no_commas)
    except ValueError:
        logging.error(f"Invalid experience value: {experience_value}")
        return "N/A"

    for i, (lvl, exp) in enumerate(sorted_levels):
        if experience_value < exp:
            return sorted_levels[i - 1][0] if i > 0 else lvl
    return sorted_levels[-1][0]

def fetch_clan_members(clan_name):
    """Fetch clan members from the Runescape clan hiscores."""
    url = f"http://services.runescape.com/m=clan-hiscores/members_lite.ws?clanName={quote(clan_name)}"
    logging.info(f"Fetching clan members from URL: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error occurred while fetching clan members: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error

    data = response.text.strip().split("\n")
    members = []
    for line in data[1:]:  # Skip the header line
        try:
            name, rank, experience, kills = line.split(",")
            name = name.replace("\xa0", " ").strip()
            members.append({
                "name": name,
                "rank": rank.strip(),
                "experience": int(experience.strip()),
                "kills": int(kills.strip())
            })
        except ValueError as ve:
            logging.error(f"Error parsing line: {line}. Error: {ve}")
            continue

    logging.info(f"Fetched {len(members)} clan members.")
    return pd.DataFrame(members)

async def fetch_player_stats_async(session, username, semaphore, retries=3):
    """Asynchronously fetch player stats with retry logic."""
    url = f"https://secure.runescape.com/m=hiscore/index_lite.ws?player={quote(username)}"
    async with semaphore:
        for attempt in range(1, retries + 1):
            try:
                async with session.get(url, timeout=ClientTimeout(total=REQUEST_TIMEOUT)) as response:
                    if response.status == 404:
                        logging.error(f"ERROR - HTTP error occurred for {username}: 404 Client Error: Not found for url: {url}")
                        return None  # Indicate that this member should be skipped
                    elif response.status != 200:
                        logging.warning(f"Failed to fetch stats for {username}. Status Code: {response.status}")
                        return None

                    text = await response.text()
                    data = text.strip().split("\n")

                    if len(data) < len(SKILLS):
                        logging.warning(f"Insufficient data received for {username}. Expected {len(SKILLS)} lines, got {len(data)}.")
                        return None

                    skill_data = [line.split(",") for line in data[:len(SKILLS)]]
                    formatted_skill_data = [
                        ["0" if value == "-1" else value for value in values] for values in skill_data
                    ]

                    processed_data = {
                        "username": username
                    }

                    for skill, values in zip(SKILLS, formatted_skill_data):
                        if len(values) < 3:
                            logging.warning(f"Incomplete data for {skill} of {username}. Data: {values}")
                            processed_data[skill] = {
                                "rank": "N/A",
                                "level": "N/A",
                                "experience": "N/A",
                                "time_retrieved": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            continue

                        rank, level, experience = values
                        try:
                            if skill == 'Invention' and int(level) == 120:
                                level = remap_levels(experience, elite_skills_exp)
                            elif skill != 'Invention' and skill != 'Overall' and int(level) >= 99:
                                level = remap_levels(experience, level_exp_dict)
                            else:
                                level = int(level)
                        except ValueError as ve:
                            logging.error(f"Error processing {skill} for {username}: {ve}")
                            level = "N/A"

                        processed_data[skill] = {
                            "rank": rank,
                            "level": level,
                            "experience": experience,
                            "time_retrieved": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }

                    return processed_data

            except asyncio.TimeoutError:
                logging.error(f"Timeout occurred while fetching stats for {username}. Attempt {attempt} of {retries}.")
            except aiohttp.ClientConnectorError as e:
                logging.error(f"Connection error for {username}: {e}. Attempt {attempt} of {retries}.")
            except Exception as e:
                logging.error(f"Exception occurred while fetching stats for {username}: {e}. Attempt {attempt} of {retries}.")

            if attempt < retries:
                wait_time = 2 ** attempt  # Exponential backoff
                logging.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
        logging.error(f"All retry attempts failed for {username}. Skipping.")
        return None

async def fetch_all_player_stats(members, concurrent_requests=CONCURRENT_REQUESTS):
    """Fetch all player stats concurrently."""
    semaphore = Semaphore(concurrent_requests)
    connector = aiohttp.TCPConnector(limit_per_host=concurrent_requests)
    async with ClientSession(connector=connector) as session:
        tasks = [
            fetch_player_stats_async(session, member, semaphore)
            for member in members
        ]
        # Gather results preserving order
        results = await asyncio.gather(*tasks)

    # Results are in the same order as the tasks list
    ordered_results = []
    skipped_members = []

    for member, result in zip(members, results):
        if result is not None:
            ordered_results.append(result)
        else:
            skipped_members.append(member)

    logging.info(f"Successfully fetched stats for {len(ordered_results)} members.")
    logging.info(f"Skipped {len(skipped_members)} members due to errors.")
    return ordered_results, skipped_members

def save_to_csv(data, filename='formatted_skill_data_cron.csv'):
    """Save the collected data to a CSV file by appending each player-skill as a separate row."""
    records = []
    for entry in data:
        username = entry.get("username", "N/A")
        for skill, stats in entry.items():
            if skill == "username":
                continue
            # Extract or set the retrieval time
            time_retrieved = stats.get("time_retrieved", "N/A")
            record = {
                "username": username,
                "skill": skill,
                "experience": stats.get("experience", "N/A"),
                "level": stats.get("level", "N/A"),
                "rank": stats.get("rank", "N/A"),
                "time_retrieved": time_retrieved
            }
            records.append(record)

    df = pd.DataFrame(records)

    # Check if the file exists
    file_exists = os.path.isfile(filename)

    # Append to the CSV file
    df.to_csv(filename, mode='a', header=not file_exists, index=False)
    if file_exists:
        logging.info(f"Appended data to {filename}.")
    else:
        logging.info(f"Created and saved data to {filename}.")

def main():
    clan_name = "10s" 
    start_time = time.time()

    # Fetch clan members
    members_df = fetch_clan_members(clan_name)
    if members_df.empty:
        logging.error("No clan members fetched. Exiting.")
        return

    member_names = members_df["name"].tolist()
    logging.info(f"Total members to fetch stats for: {len(member_names)}")

    try:
        # Run the asynchronous fetching
        fetched_data, skipped = asyncio.run(fetch_all_player_stats(member_names))
    except RuntimeError as e:
        # Handle the event loop already running error (e.g., in Jupyter)
        logging.error(f"RuntimeError occurred: {e}")
        # If using Jupyter, use nest_asyncio
        # Uncomment the following lines if running in Jupyter
        # import nest_asyncio
        # nest_asyncio.apply()
        # fetched_data, skipped = asyncio.run(fetch_all_player_stats(member_names))
        return

    # Save fetched data to CSV
    if fetched_data:
        save_to_csv(fetched_data, 'formatted_skill_data_cron.csv')
    else:
        logging.warning("No data fetched to save.")

    end_time = time.time()
    elapsed = end_time - start_time
    logging.info(f"Script completed in {elapsed:.2f} seconds.")

    if skipped:
        logging.info(f"Skipped members: {skipped}")

if __name__ == "__main__":
    main()

