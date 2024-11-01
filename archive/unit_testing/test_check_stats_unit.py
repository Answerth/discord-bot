import unittest
from unittest.mock import AsyncMock, MagicMock
from minimal_bot_test import check_stats
from check_stats import HiscoreFetcher, format_stats_to_text, generate_stats_image

class TestCheckStats(unittest.IsolatedAsyncioTestCase):
    async def test_check_stats_success(self):
        # Mock Context
        class MockContext:
            async def send(self, content=None, *, embed=None, file=None):
                self.content = content
                self.embed = embed
                self.file = file

        ctx = MockContext()
        
        # Mock HiscoreFetcher
        fetcher = HiscoreFetcher("sampleuser")
        fetcher.fetch_data = AsyncMock(return_value=True)
        fetcher.process_skill_data = MagicMock(return_value=[["1", "99", "13034431"] for _ in range(len(SKILLS))])
        fetcher.process_activity_data = MagicMock(return_value=[["1", "1000000"] for _ in range(len(ACTIVITIES))])
        
        # Replace HiscoreFetcher with mock
        with unittest.mock.patch('check_stats.HiscoreFetcher', return_value=fetcher):
            await check_stats(ctx, username="sampleuser")
            # Assertions
            self.assertTrue(hasattr(ctx, 'embed'))
            self.assertTrue(hasattr(ctx, 'file'))
            self.assertIn("Stats for sampleuser", ctx.embed.description)
            self.assertEqual(ctx.file.filename, "sampleuser_stats.png")

    async def test_check_stats_failure(self):
        # Mock Context
        class MockContext:
            async def send(self, content=None, *, embed=None, file=None):
                self.content = content
                self.embed = embed
                self.file = file

        ctx = MockContext()
        
        # Mock HiscoreFetcher
        fetcher = HiscoreFetcher("invaliduser")
        fetcher.fetch_data = AsyncMock(return_value=False)
        
        # Replace HiscoreFetcher with mock
        with unittest.mock.patch('check_stats.HiscoreFetcher', return_value=fetcher):
            await check_stats(ctx, username="invaliduser")
            # Assertions
            self.assertIn("❌ Could not retrieve stats for `invaliduser`", ctx.content)

if __name__ == '__main__':
    unittest.main()
