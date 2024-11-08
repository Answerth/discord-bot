import os
import signal
import asyncio
import discord
from discord.ext import commands
from sqlalchemy import create_engine, Table, MetaData, select
import json

# Define the lock file path
LOCKFILE = "/tmp/minimal_bot_test.lock"

def is_already_running():
    """Check if another bot instance is running and terminate it."""
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
    """Remove the lock file on exit."""
    if os.path.exists(LOCKFILE):
        os.remove(LOCKFILE)
        print("Cleaned up lock file.")

# Run lockfile check
is_already_running()

class TestMemberMatch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.engine = self.create_db_engine()
        self.testing_channel_id = 1210037185131323402  # Replace with your testing channel ID

    def create_db_engine(self):
        """Create SQLAlchemy engine using dbconfig.json."""
        config_path = os.path.join(os.path.expanduser("~"), 'discordbot10s', 'dbconfig.json')
        if not os.path.exists(config_path):
            raise FileNotFoundError("Database configuration file not found.")
        with open(config_path) as db_config_file:
            db_config = json.load(db_config_file)
        print("Database configuration loaded successfully.")
        return create_engine(
            f"postgresql://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )

    @commands.command(name='test_member_matches')
    async def test_member_matches(self, ctx):
        """Compare database names with Discord member nicknames or usernames, with prioritized custom mappings."""
        print("Command '!test_member_matches' received.")
        if ctx.channel.id != self.testing_channel_id:
            await ctx.send("This command can only be used in the designated testing channel.")
            print(f"Command issued outside the testing channel (ID: {ctx.channel.id}). Aborting.")
            return

        # Step 1: Define Custom Mapping (Keys should be lowercase)
        custom_mapping = {
            "buttbandiit": "Booty Patrol",
            "torvar95": "Torvar98",
            # Add more mappings as needed, ensuring keys are lowercase
        }

        # Step 2: Fetch members from the database
        print("Fetching members from the database.")
        metadata = MetaData()
        members_table = Table('members', metadata, autoload_with=self.engine)
        db_members = []
        db_member_names = set()

        try:
            with self.engine.connect() as conn:
                select_stmt = select(members_table.c.name)
                result = conn.execute(select_stmt)
                db_members_raw = result.fetchall()
                db_members = [(row.name, row.name.lower()) for row in db_members_raw]
                db_member_names = {row.name.lower() for row in db_members_raw}
                print(f"Fetched {len(db_members)} members from the database.")
        except Exception as e:
            print(f"Error fetching data from the database: {e}")
            await ctx.send("An error occurred while accessing the database.")
            return

        # Step 3: Check for missing custom mappings in the database
        missing_custom_members = [name for name in custom_mapping if name.lower() not in db_member_names]
        if missing_custom_members:
            print(f"Warning: Custom mappings not found in the database: {', '.join(missing_custom_members)}")

        # Step 4: Fetch all server members with preserved casing for tagging
        guild = ctx.guild
        print("Fetching all members in the server.")
        discord_members = {}
        for member in guild.members:
            # Use nickname if available, else username
            key = member.display_name.lower() if member.display_name else member.name.lower()
            if key not in discord_members:
                discord_members[key] = member
        print(f"Fetched {len(discord_members)} unique members from the server.")

        # Step 5: Compare and prepare matched/unmatched lists
        matched = []
        unmatched = []

        print("Comparing database members with Discord server members and custom mapping.")
        for original_name, lower_name in db_members:
            # Check custom mapping first (keys are already lowercase)
            custom_nickname = custom_mapping.get(lower_name)
            if custom_nickname:
                # Attempt to find the member with the custom nickname
                discord_member = discord_members.get(custom_nickname.lower())
                if discord_member:
                    matched.append(discord_member.mention)
                    print(f"Custom Matched: Database name '{original_name}' with custom Discord member '{custom_nickname}' (ID: {discord_member.id})")
                else:
                    unmatched.append(f"@{original_name}")  # Custom mapped name not found in Discord
                    print(f"Custom Unmatched: Database name '{original_name}' with custom nickname '{custom_nickname}' not found in Discord.")
            else:
                # Default matching if no custom mapping
                discord_member = discord_members.get(lower_name)
                if discord_member:
                    matched.append(discord_member.mention)  # Tag with preserved casing
                    print(f"Matched: Database name '{original_name}' with Discord member '{discord_member.display_name}' (ID: {discord_member.id})")
                else:
                    unmatched.append(f"@{original_name}")  # Use original name if no match
                    print(f"Unmatched: Database name '{original_name}'")
        # Logging comparison results
        print(f"Total Matched members: {len(matched)}")
        print(f"Total Unmatched members: {len(unmatched)}")

        # Step 6: Send results to Discord
        matched = sorted(matched)
        unmatched = sorted(unmatched)
        if matched:
            matched_message = "Matched members:\n" + "\n".join(matched)
        else:
            matched_message = "No matches found."

        if unmatched:
            unmatched_message = "Unmatched members:\n" + "\n".join(unmatched)
        else:
            unmatched_message = "All members matched."

        print(unmatched_message)
        await ctx.send(f"{unmatched_message}")
        #await ctx.send(f"{matched_message}\n\n{unmatched_message}")
        print("Results sent to the Discord channel.")

    @commands.command(name='listalldiscordmembers')
    async def list_all_discord_members(self, ctx):
        """List all Discord members in plain text."""
        print("Command '!listalldiscordmembers' received.")
        if ctx.channel.id != self.testing_channel_id:
            await ctx.send("This command can only be used in the designated testing channel.")
            print(f"Command issued outside the testing channel (ID: {ctx.channel.id}). Aborting.")
            return

        guild = ctx.guild
        print("Fetching all members in the server.")
        members_list = sorted(
            [member.display_name if member.display_name else member.name for member in guild.members],
            key=lambda name: name.casefold()
            )

        #members_list = sorted([member.display_name if member.display_name else member.name for member in guild.members])
        print(f"Fetched {len(members_list)} members from the server.")

        # Prepare the message
        members_text = "\n".join(members_list)

        # Discord message character limit is 2000
        if len(members_text) > 2000:
            # If too long, send as a text file
            print("Member list exceeds Discord's message character limit. Sending as a text file.")
            file = discord.File(io.StringIO(members_text), filename="discord_members.txt")
            await ctx.send("List of all Discord members:", file=file)
        else:
            # Send as plain text message
            await ctx.send(f"List of all Discord members:\n{members_text}")
            print("Sent member list as a plain text message.")

# Set up bot with minimal commands
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Necessary to fetch guild members

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Testing bot is ready and logged in as {bot.user}')

async def setup_testing_bot():
    await bot.add_cog(TestMemberMatch(bot))
    await bot.start(os.getenv('DISCORD_BOT_TOKEN'))

if __name__ == "__main__":
    # Ensure the bot token is loaded from the environment variable
    BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    if not BOT_TOKEN:
        raise ValueError("Bot token not found. Please set the DISCORD_BOT_TOKEN environment variable.")

    try:
        asyncio.run(setup_testing_bot())
    finally:
        cleanup()

