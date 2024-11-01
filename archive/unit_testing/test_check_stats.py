import asyncio
from minimal_bot_test import check_stats_command  # Updated import
from check_stats import HiscoreFetcher, format_stats_to_text, generate_stats_image

class MockContext:
    """A mock class to simulate Discord's Context (ctx) object."""
    async def send(self, content=None, *, embed=None, file=None):
        if embed:
            print("Embed Title:", embed.title)
            if embed.description:
                print("Embed Description:", embed.description)
            if embed.image:
                print("Embed Image URL:", embed.image.url)
        if file:
            print("Sent file:", file.filename)
        if content:
            print("Message:", content)

async def test_check_stats(username: str):
    """Function to test the check_stats command with a mock context."""
    ctx = MockContext()
    try:
        await check_stats_command(ctx, username=username)
    except Exception as e:
        print(f"An error occurred during testing: {e}")

if __name__ == "__main__":
    username = input("Enter a RuneScape username to test: ")
    asyncio.run(test_check_stats(username))

