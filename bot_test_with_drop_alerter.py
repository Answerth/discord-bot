# bot_test_with_drop_alerter.py

import os
import signal
import discord
from discord.ext import commands
from discord import app_commands, Embed
from cogs.clan_members.get_clan_members import fetch_clan_members, get_member_activities
import io
import re  # For potential future use with as_file functionality
import asyncio
import logging

# Define the lock file path
LOCKFILE = "/tmp/minimal_bot_test.lock"

def is_already_running():
    """Check if the bot is already running using a lock file."""
    if os.path.exists(LOCKFILE):
        with open(LOCKFILE, "r") as f:
            try:
                old_pid = int(f.read().strip())
                os.kill(old_pid, signal.SIGTERM)
                print(f"Terminated old instance with PID {old_pid}")
            except ProcessLookupError:
                print("No active process found for old PID; starting a new instance.")
            except Exception as e:
                print(f"Unexpected error: {e}")
    # Write the current process ID to the lock file
    with open(LOCKFILE, "w") as f:
        f.write(str(os.getpid()))
    print(f"Started new instance with PID {os.getpid()}")

def cleanup():
    """Ensure lock file is removed on exit."""
    if os.path.exists(LOCKFILE):
        os.remove(LOCKFILE)
        print("Cleaned up lock file.")

def strip_ansi_codes(text):
    """
    Removes ANSI escape codes from the given text.

    :param text: The input string containing ANSI codes.
    :return: The cleaned string without ANSI codes.
    """
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)

async def send_activities(send_func, activities_chunks, username, include_activities):
    """
    Helper function to send activities as embedded messages based on the include_activities flag.

    :param send_func: The function to use for sending messages (e.g., ctx.send or interaction.followup.send)
    :param activities_chunks: List of activity text chunks
    :param username: The username to include in the filename if sending as a file
    :param include_activities: Boolean flag indicating whether to include activities
    """
    if include_activities:
        # Send Activities as embedded messages
        for chunk in activities_chunks:
            embed = Embed(description=f"```ansi\n{chunk}\n```")
            await send_func(embed=embed)
    else:
        # Append a message indicating activities have been excluded
        # This function should not handle sending this message to avoid multiple posts
        pass

# Run the lockfile check at the beginning
is_already_running()

# Set up Discord bot with '!' as the prefix
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    """Event handler when the bot is ready."""
    await bot.tree.sync()
    print(f'Logged in as {bot.user}')

@bot.command(name="ping")
async def ping(ctx):
    """Responds with 'Pong!' when a user sends !ping."""
    await ctx.send("Pong!")

@bot.tree.command(name="ping")
async def ping_slash(interaction: discord.Interaction):
    """Slash command that responds with 'Pong!'."""
    await interaction.response.send_message("Pong!")

@bot.tree.command(name="activity")
@app_commands.describe(username="The RuneScape username to fetch activities for")
async def activity(interaction: discord.Interaction, username: str, qty_max_10_atm: int = 5):
    await interaction.response.defer()  # Prevents timeout while processing

    # Fetch recent activities for the specified user
    member_data = get_member_activities(username, qty_max_10_atm)

    # Format activities as an embed for Discord
    embed = Embed(title=f"Recent Activities for {username}", color=discord.Color.blue())

    if member_data.empty:
        embed.description = "No recent activities found within the last 30 days."
    else:
        activity_text = "\n".join(
            f"- **{activity['date']}**: {activity['details']}"
            for _, activity in member_data.iterrows()
        )
        embed.add_field(name="Activities", value=activity_text, inline=False)

    await interaction.followup.send(embed=embed)

@bot.command(name="checkstats")
async def check_stats(ctx, *, args: str):
    """
    Traditional command to check player stats.

    Usage:
    !checkstats Username
    !checkstats Username include_activities=False
    """
    # Inform the user to use the slash command instead
    await ctx.send("I no longer use '!' commands. Please use `/checkstats` instead.")

@bot.tree.command(name="checkstats")
@app_commands.describe(
    username="The username to check stats for",
    include_activities="Whether to include activities in the stats report"
)
async def check_stats_slash(interaction: discord.Interaction, username: str, include_activities: bool = False):
    """
    Slash command to check player stats.

    Usage:
    /checkstats username: Username include_activities: true
    """
    # Acknowledge the command to prevent timeout
    await interaction.response.defer()

    stats_chunks = fetch_player_stats(username)

    if not stats_chunks:
        await interaction.followup.send(
            f"Could not retrieve stats for {username}. Please check the username and try again.",
            ephemeral=True
        )
        return

    skills_chunks = []
    activities_chunks = []

    if len(stats_chunks) >= 1:
        skills_chunks.append(stats_chunks[0])
    if len(stats_chunks) >= 2:
        activities_chunks.append(stats_chunks[1])

    # Create an embed for Skills
    skills_embed = Embed(title=f"{username}'s Skills", color=0x00ff00)
    skills_description = "\n".join([f"```ansi\n{chunk}\n```" for chunk in skills_chunks])
    skills_embed.description = skills_description

    # If include_activities is False, append the exclusion message
    if not include_activities:
        skills_embed.add_field(name="Note", value="Activities have been excluded from this stats report.", inline=False)

    # Send Skills embed
    await interaction.followup.send(embed=skills_embed)

    # Handle Activities based on the flag using the helper function
    if include_activities and activities_chunks:
        await send_activities(interaction.followup.send, activities_chunks, username, include_activities)

@bot.tree.command(
    name="embed_video",
    description="Embed videos from supported platforms: Instagram, Reddit, and Twitter/X"
)
async def embed_video(interaction: discord.Interaction, link: str):
    await interaction.response.defer()

    # Domain replacements for embedding
    if "instagram.com" in link:
        new_link = link.replace("instagram.com", "instagramez.com")
    elif "reddit.com" in link:
        new_link = link.replace("reddit.com", "rxddit.com")
    elif "x.com" in link:
        new_link = link.replace("x.com", "fxtwitter.com")
    elif "twitter.com" in link:
        new_link = link.replace("twitter.com", "fxtwitter.com")
    else:
        await interaction.followup.send("Unsupported URL. Please provide a link from Instagram, Reddit, or Twitter.")
        return

    # Send the modified link in response
    await interaction.followup.send(new_link)



import random

whatsup_responses = [
    "Vibin', u?", 
    "Skibidi bop bop 💀", 
    "Livin' the dream 😎", 
    "Chillin' like a villain", 
    "Big W vibes rn", 
    "Just rizzin' up 🌊", 
    "On that grind, fr", 
    "Catchin' the vibe", 
    "Y'know, just vibin'", 
    "Stayin' unbothered", 
    "Out here chillaxin'", 
    "Feelin' the drip 😤", 
    "Same vibe, diff day", 
    "Skrrt skrrt, u?", 
    "In my feels, lowkey", 
    "Ridin' the wave 🌊", 
    "Upgraded my rizz 💯", 
    "Keepin' it lowkey", 
    "Mad vibez only", 
    "Catchin' dubs today"
]

# Define the command
#@bot.tree.command(
#    name="whatsup",
#    description="Responds with a random Gen Z reply to 'what's up?'"
#)
#async def whats_up(interaction: discord.Interaction):
#    #await interaction.response.defer()
#    # Choose a random response
#    response = random.choice(whatsup_responses)
#    # Send the chosen response
#    await interaction.response.send_message(response)
@bot.command(name="whatsup")
async def whats_up_prefix(ctx):
    """Responds with a random Gen Z reply to '!whatsup'."""
    response = random.choice(whatsup_responses)
    await ctx.send(response)


# Load the alert_drops cog
initial_extensions = [
    'cogs.clan_members.alert_drops',  # Add the new cog here
]


async def load_extensions():
    for extension in initial_extensions:
        try:
            await bot.load_extension(extension)
            print(f"Loaded extension '{extension}'")
        except Exception as e:
            print(f"Failed to load extension {extension}. {e}")

async def main():
    await load_extensions()
    await bot.start(os.getenv('DISCORD_BOT_TOKEN'))

if __name__ == "__main__":
    # Ensure that the bot token is loaded from the environment variable
    BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    if not BOT_TOKEN:
        raise ValueError("Bot token not found. Please set the DISCORD_BOT_TOKEN environment variable.")

    try:
        asyncio.run(main())
    finally:
        cleanup()

