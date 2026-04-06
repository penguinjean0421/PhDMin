import os
from pathlib import Path
from typing import List

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

class PhDMin(commands.Bot):
    """Main Bot class for managing extensions and connectivity."""

    def __init__(self):
        raw_prefixes = os.getenv("BOT_PREFIXES", "!")
        prefixes: List[str] = [p.strip() for p in raw_prefixes.split(",")]
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(
            command_prefix=prefixes,
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        """Initializes the bot by loading all Python files in the cogs directory."""
        cogs_path = Path(__file__).parent / "cogs"
        if not cogs_path.exists():
            cogs_path.mkdir()
            print("📂 'cogs' 폴더가 없어 새로 생성했습니다.")
        for filepath in cogs_path.glob("*.py"):
            # Skip private/special files like __init__.py
            if filepath.stem.startswith("__"):
                continue
            cog_name = f"cogs.{filepath.stem}"
            try:
                await self.load_extension(cog_name)
                print(f"✅ {cog_name} 로드 성공")
            except Exception as e:
                print(f"❌ {cog_name} 로드 실패 -> {e}")

    async def on_ready(self):
        """Triggered when the bot is connected and ready."""
        print("-" * 30)
        print(f"🟢 {self.user.name} 온라인!")
        print(f"🆔 ID: {self.user.id}")
        print(f"🔢 접두사: {', '.join(self.command_prefix)}")
        print("-" * 30)
        await self.change_presence()

if __name__ == "__main__":
    if not TOKEN:
        print("❌ 오류: BOT_TOKEN이 설정되지 않았습니다.")
    else:
        bot = PhDMin()
        bot.run(TOKEN)