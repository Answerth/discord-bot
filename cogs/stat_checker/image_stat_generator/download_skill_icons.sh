urls=(
'https://www.runescape.com/img/rs3/adventurers-log/skills/herblore.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/necromancy.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/hitpoints.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/archaeology.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/invention.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/farming.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/slayer.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/magic.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/defence.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/dungeoneering.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/ranged.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/summoning.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/strength.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/attack.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/mining.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/fishing.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/smithing.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/woodcutting.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/hunter.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/fletching.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/construction.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/agility.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/divination.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/crafting.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/firemaking.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/prayer.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/runecrafting.png'
'https://www.runescape.com/img/rs3/adventurers-log/skills/cooking.png'
"https://www.runescape.com/img/rs3/adventurers-log/skills/thieving.png"
)


# Directory to store images
save_dir=~/skill_icons

# Download each image
for url in "${urls[@]}"; do
    # Extract the filename from the URL
    filename=$(basename "$url")
    # Download the image and save it in the specified directory
    wget -q -O "$save_dir/$filename" "$url"
    echo "Downloaded $filename to $save_dir"
done
