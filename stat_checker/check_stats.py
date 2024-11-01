import requests
from urllib.parse import quote

# Define skill and activity names in the correct order
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
    # Sort levels by experience in ascending order
    sorted_levels = sorted(exp_dict.items())
    
    experience_value_no_commas = experience_value.replace(",", "")
    experience_value = int(experience_value_no_commas)
    # Iterate over each level and experience
    for i, (lvl, exp) in enumerate(sorted_levels):
        # If the current level's experience is more than experience_value, return the previous level
        #experience_value = int(experience_value) 
        if experience_value < exp:
            return sorted_levels[i - 1][0] if i > 0 else lvl
    # If the experience is higher than the highest level in the dictionary, return the max level
    return sorted_levels[-1][0]

def add_commas_back(value):
    value = "{:,}".format(int(value))
    return value

def fetch_player_stats(username):
    url = f"https://secure.runescape.com/m=hiscore/index_lite.ws?player={quote(username)}"
    response = requests.get(url)

    if response.status_code != 200:
        return [f"Could not retrieve stats for {quote(username)}. Please check the username and try again."]

    # Parse data line by line
    data = response.text.strip().split("\n")

    # Extract skill and activity data
    skill_data = [line.split(",") for line in data[:len(SKILLS)]]
    commas_added_to_skills = [
         ["{:,}".format(int(values[0])), values[1], "{:,}".format(int(values[2]))] for values in skill_data
    ]
    formatted_skill_data = [
	["0" if value == "-1" else value for value in values] for values in commas_added_to_skills
	]
    activity_data = [line.split(",") for line in data[len(SKILLS):len(SKILLS) + len(ACTIVITIES)]]
    commas_added = [
	["{:,}".format(int(values[0])), "{:,}".format(int(values[1]))] for values in activity_data
	]
    formatted_activity_data = [
	["0" if value == "-1" else value for value in values] for values in commas_added
	]

    # ANSI color codes for different sections
    header_color = "\x1b[1;36m"  # Cyan for headers
    skill_name_color = "\x1b[1;37m"  # White for skill names
    value_color = "\x1b[6;34m"  # Green for values
    reset_color = "\x1b[0m"  # Reset

    # Build Skills section
    skills_table = [f"{header_color}Stats for {username}{reset_color}\n\n**Skills:**\n"]
    skills_table.append("╔═════════════════════════════════════════════════════╗\n")
    skills_table.append(f"║{header_color} Skill         | Rank       | Level  | Experience    {reset_color}║\n")
    skills_table.append(f"║{header_color}---------------|------------|--------|---------------{reset_color}║\n")
    for skill, values in zip(SKILLS, formatted_skill_data):
       rank, level, experience = values
       if skill == 'Invention' and level == '0':
          skill = 'Invention \U0001F512'
       elif skill == 'Invention' and int(level) == 120:
          level = remap_levels(experience, elite_skills_exp)
          level = add_commas_back(level)
       elif skill != 'Invention' and skill != 'Overall' and int(level) >= 99:
          level = remap_levels(experience, level_exp_dict)
          level = add_commas_back(level)
 

       skills_table.append(
            f"║ {skill_name_color}{skill:<13}{reset_color} | "
            f"{value_color}{rank:<10}{reset_color} | "
            f"{value_color}{level:<6}{reset_color} | "
            f"{value_color}{experience:<13}{reset_color} ║\n"
        )

       #skills_table.append(f"║ {skill:<13} | {rank:<10} | {level:<6} | {experience:<13} ║\n")
    skills_table.append("╚═════════════════════════════════════════════════════╝\n")

    skills_text = ''.join(skills_table)

    # Build Activities section
    activities_table = ["\n**Activities:**\n"]
    activities_table.append("╔══════════════════════════════════════════════════════╗\n")
    activities_table.append(f"║{header_color} Activity                      | Rank    | Score      {reset_color}║\n")
    activities_table.append(f"║{header_color}-------------------------------|---------|------------{reset_color}║\n")
    for activity, values in zip(ACTIVITIES, formatted_activity_data):
        rank, score = values
        #activities_table.append(f"║ {activity:<31} | {rank:<7} | {score:<10} ║\n")
        activities_table.append(
         f"║ {skill_name_color}{activity:<29}{reset_color} | "
         f"{value_color}{rank:<7}{reset_color} | "
         f"{value_color}{score:<10}{reset_color} ║\n"
        )


    activities_table.append("╚══════════════════════════════════════════════════════╝\n")
    activities_text = ''.join(activities_table)

    # Combine sections based on length constraints
    posts = []
    if len(skills_text) > 4000:
        posts.extend(split_into_chunks(skills_text, 4000))
    else:
        posts.append(skills_text)
    
    if len(activities_text) > 4000:
        posts.extend(split_into_chunks(activities_text, 4000))
    else:
        posts.append(activities_text)

    return posts

def split_into_chunks(text, max_length):
    """Splits text into chunks of specified max_length, cleanly splitting on line breaks."""
    lines = text.splitlines(keepends=True)
    chunks = []
    current_chunk = ""

    for line in lines:
        if len(current_chunk) + len(line) > max_length:
            chunks.append(current_chunk)
            current_chunk = ""
        current_chunk += line

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

