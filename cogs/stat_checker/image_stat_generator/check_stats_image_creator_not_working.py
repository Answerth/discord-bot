import requests
from urllib.parse import quote
from typing import List, Dict, Tuple
from PIL import Image, ImageDraw, ImageFont
import os

# Constants
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


LEVEL_EXP_DICT = {
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

ELITE_SKILLS_EXP = {
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


class HiscoreFetcher:
    BASE_URL = "https://secure.runescape.com/m=hiscore/index_lite.ws?player={username}"

    def __init__(self, username: str):
        self.username = username
        self.skill_data = []
        self.activity_data = []

    def fetch_data(self) -> bool:
        url = self.BASE_URL.format(username=quote(self.username))
        response = requests.get(url)
        if response.status_code != 200:
            return False

        data = response.text.strip().split("\n")
        self.skill_data = [line.split(",") for line in data[:len(SKILLS)]]
        self.activity_data = [line.split(",") for line in data[len(SKILLS):len(SKILLS) + len(ACTIVITIES)]]
        return True

    @staticmethod
    def remap_levels(experience_value: str, exp_dict: Dict[int, int]) -> int:
        experience = int(experience_value.replace(",", ""))
        sorted_levels = sorted(exp_dict.items())

        for i, (lvl, exp) in enumerate(sorted_levels):
            if experience < exp:
                return sorted_levels[i - 1][0] if i > 0 else lvl
        return sorted_levels[-1][0]

    @staticmethod
    def add_commas(value: int) -> str:
        return "{:,}".format(value)

    def process_skill_data(self) -> List[List[str]]:
        processed = []
        for values in self.skill_data:
            rank, level, experience = values
            rank = "0" if rank == "-1" else self.add_commas(int(rank))
            level = "0" if level == "-1" else level
            experience = "0" if experience == "-1" else self.add_commas(int(experience))
            processed.append([rank, level, experience])
        return processed

    def process_activity_data(self) -> List[List[str]]:
        processed = []
        for values in self.activity_data:
            rank, score = values
            rank = "0" if rank == "-1" else self.add_commas(int(rank))
            score = "0" if score == "-1" else self.add_commas(int(score))
            processed.append([rank, score])
        return processed

def split_into_chunks(text: str, max_length: int = 4000) -> List[str]:
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

def format_stats_to_text(username: str, skills: List[List[str]], activities: List[List[str]]) -> List[str]:
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
    for skill, values in zip(SKILLS, skills):
        rank, level, experience = values
        if skill == 'Invention' and level == '0':
            skill_display = 'Invention \U0001F512'
        elif skill == 'Invention' and int(level) >= 120:  # Updated condition
            level = HiscoreFetcher.remap_levels(experience, ELITE_SKILLS_EXP)
            level = HiscoreFetcher.add_commas(int(level))
            skill_display = skill
        elif skill != 'Invention' and skill != 'Overall' and int(level) >= 99:
            level = HiscoreFetcher.remap_levels(experience, LEVEL_EXP_DICT)
            level = HiscoreFetcher.add_commas(int(level))
            skill_display = skill
        else:
            skill_display = skill

        skills_table.append(
            f"║ {skill_name_color}{skill_display:<13}{reset_color} | "
            f"{value_color}{rank:<10}{reset_color} | "
            f"{value_color}{level:<6}{reset_color} | "
            f"{value_color}{experience:<13}{reset_color} ║\n"
        )
    skills_table.append("╚═════════════════════════════════════════════════════╝\n")

    # Build Activities section
    activities_table = ["\n**Activities:**\n"]
    activities_table.append("╔══════════════════════════════════════════════════════╗\n")
    activities_table.append(f"║{header_color} Activity                      | Rank    | Score      {reset_color}║\n")
    activities_table.append(f"║{header_color}-------------------------------|---------|------------{reset_color}║\n")
    for activity, values in zip(ACTIVITIES, activities):
        rank, score = values
        activities_table.append(
            f"║ {skill_name_color}{activity:<29}{reset_color} | "
            f"{value_color}{rank:<7}{reset_color} | "
            f"{value_color}{score:<10}{reset_color} ║\n"
        )
    activities_table.append("╚══════════════════════════════════════════════════════╝\n")

    # Combine sections
    full_text = ''.join(skills_table) + ''.join(activities_table)
    return split_into_chunks(full_text)

def generate_stats_image(username: str, skills: List[List[str]], output_path: str = "skills_summary.png"):
    # Configuration
    icon_size = (30, 30)
    padding = 10
    y_offset = padding
    font_size = 22

    # Use default font
    font = ImageFont.load_default()

    # Calculate image size
    # Header height
    header_text = f"Stats for {username}"
    img_dummy = Image.new("RGB", (1, 1))
    draw_dummy = ImageDraw.Draw(img_dummy)
    header_bbox = draw_dummy.textbbox((0, 0), header_text, font=font)
    header_height = header_bbox[3] - header_bbox[1]

    # Total height: padding + header + padding + (icon + padding) * number of skills + padding
    image_width = 600
    image_height = padding + header_height + padding + (icon_size[1] + padding) * len(SKILLS) + padding

    # Create image
    img = Image.new("RGB", (image_width, image_height), color=(30, 30, 30))  # Dark background
    draw = ImageDraw.Draw(img)

    # Draw header
    draw.text((padding, y_offset), header_text, fill="white", font=font)
    y_offset += header_height + padding

    # Define skill_icons directory
    SKILL_ICONS_DIR = os.path.join(os.path.dirname(__file__), "skill_icons")
    skill_icons = {
        "agility": os.path.join(SKILL_ICONS_DIR, "agility.png"),
        "archaeology": os.path.join(SKILL_ICONS_DIR, "archaeology.png"),
        "attack": os.path.join(SKILL_ICONS_DIR, "attack.png"),
        "construction": os.path.join(SKILL_ICONS_DIR, "construction.png"),
        "cooking": os.path.join(SKILL_ICONS_DIR, "cooking.png"),
        "crafting": os.path.join(SKILL_ICONS_DIR, "crafting.png"),
        "defence": os.path.join(SKILL_ICONS_DIR, "defence.png"),
        "divination": os.path.join(SKILL_ICONS_DIR, "divination.png"),
        "dungeoneering": os.path.join(SKILL_ICONS_DIR, "dungeoneering.png"),
        "farming": os.path.join(SKILL_ICONS_DIR, "farming.png"),
        "firemaking": os.path.join(SKILL_ICONS_DIR, "firemaking.png"),
        "fishing": os.path.join(SKILL_ICONS_DIR, "fishing.png"),
        "fletching": os.path.join(SKILL_ICONS_DIR, "fletching.png"),
        "herblore": os.path.join(SKILL_ICONS_DIR, "herblore.png"),
        "hitpoints": os.path.join(SKILL_ICONS_DIR, "hitpoints.png"),
        "hunter": os.path.join(SKILL_ICONS_DIR, "hunter.png"),
        "invention": os.path.join(SKILL_ICONS_DIR, "invention.png"),
        "magic": os.path.join(SKILL_ICONS_DIR, "magic.png"),
        "mining": os.path.join(SKILL_ICONS_DIR, "mining.png"),
        "necromancy": os.path.join(SKILL_ICONS_DIR, "necromancy.png"),
        "prayer": os.path.join(SKILL_ICONS_DIR, "prayer.png"),
        "ranged": os.path.join(SKILL_ICONS_DIR, "ranged.png"),
        "runecrafting": os.path.join(SKILL_ICONS_DIR, "runecrafting.png"),
        "slayer": os.path.join(SKILL_ICONS_DIR, "slayer.png"),
        "smithing": os.path.join(SKILL_ICONS_DIR, "smithing.png"),
        "strength": os.path.join(SKILL_ICONS_DIR, "strength.png"),
        "summoning": os.path.join(SKILL_ICONS_DIR, "summoning.png"),
        "thieving": os.path.join(SKILL_ICONS_DIR, "thieving.png"),
        "woodcutting": os.path.join(SKILL_ICONS_DIR, "woodcutting.png")
    }

    # Use the new Resampling filter
    resample_filter = Image.Resampling.LANCZOS

    # Draw each skill
    for skill, values in zip(SKILLS, skills):
        rank, level, experience = values

        # Load and paste icon
        icon_path = skill_icons.get(skill.lower())
        if icon_path and os.path.exists(icon_path):
            try:
                icon = Image.open(icon_path).resize(icon_size, resample_filter)
                # If the icon has an alpha channel, use it as mask
                if icon.mode in ('RGBA', 'LA'):
                    img.paste(icon, (padding, y_offset), icon)
                else:
                    img.paste(icon, (padding, y_offset))
            except Exception as e:
                print(f"Error loading icon for {skill}: {e}")
                # Draw a placeholder rectangle if icon fails
                draw.rectangle([padding, y_offset, padding + icon_size[0], y_offset + icon_size[1]], fill=(100, 100, 100))
        else:
            # Placeholder if icon not found
            draw.rectangle([padding, y_offset, padding + icon_size[0], y_offset + icon_size[1]], fill=(100, 100, 100))

        # Prepare text
        text_x = padding + icon_size[0] + padding
        text_y = y_offset + (icon_size[1] - font_size) // 2

        text = f"{skill}: Level {level} | Exp {experience}"

        # Calculate text size using textbbox (optional, not used here)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        draw.text((text_x, text_y), text, fill="white", font=font)

        y_offset += icon_size[1] + padding

    # Save image
    img.save(output_path)
    return output_path
