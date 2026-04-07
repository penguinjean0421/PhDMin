import os
import json
import random
import datetime

import discord
from discord.ext import commands, tasks


class Roulette(commands.Cog):
    """A Cog for managing scheduled Russian Roulette events across multiple servers."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Define path to config file (assumes cog is in a subfolder)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.normpath(
            os.path.join(current_dir, "..", "roulette.json")
        )
        self.last_sent_hour = None
        self.check_schedule.start()

    def cog_unload(self):
        """Cancel the background task when the cog is unloaded."""
        self.check_schedule.cancel()

    # --- JSON Management ---

    def load_full_config(self) -> dict:
        """Loads the entire configuration file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config: {e}")
        return {}

    def save_guild_config(
        self,
        guild_id: int,
        channel_id: int,
        guild_name: str,
        owner_name: str
    ):
        """Saves or updates configuration for a specific guild."""
        config = self.load_full_config()
        config[str(guild_id)] = {
            "guild_name": guild_name,
            "owner_name": str(owner_name),
            "roulette_channel_id": channel_id,
        }
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving config: {e}")

    # --- Commands ---

    @commands.group(name="set", invoke_without_command=True)
    @commands.has_permissions(manage_channels=True)
    async def set_group(self, ctx: commands.Context):
        """Base command group for server settings."""
        embed = discord.Embed(
            title="⚙️ 서버 설정 도움말",
            description="`!set roulette`: 현재 채널을 이 서버의 룰렛 채널로 지정합니다.",
            color=0x3498db
        )
        await ctx.send(embed=embed)

    @set_group.command(name="roulette")
    @commands.has_permissions(manage_channels=True)
    async def set_roulette(self, ctx: commands.Context):
        """Sets the current channel as the roulette target."""
        self.save_guild_config(
            ctx.guild.id,
            ctx.channel.id,
            ctx.guild.name,
            ctx.guild.owner
        )
        embed = discord.Embed(
            description=(
                f"✅ **{ctx.guild.name}** 서버의 룰렛 채널이 "
                f"{ctx.channel.mention}으로 설정되었습니다."
            ),
            color=0x2ecc71
        )
        await ctx.send(embed=embed)

    # --- Scheduled Tasks ---

    @tasks.loop(minutes=5)
    async def check_schedule(self):
        """Checks the current time against the schedule and runs events."""
        tz_korea = datetime.timezone(datetime.timedelta(hours=9))
        now = datetime.datetime.now(tz_korea)
        day, hour, minute = now.weekday(), now.hour, now.minute

        # Schedule Logic (Mon 14-17, Tue 10-13/14-17, Wed 14-17)
        is_scheduled = (
            (day == 0 and 14 <= hour <= 17) or
            (day == 1 and (10 <= hour <= 13 or 14 <= hour <= 17)) or
            (day == 2 and 14 <= hour <= 17)
        )

        current_time_slot = f"{now.date()}-{hour}"
        if is_scheduled and self.last_sent_hour != current_time_slot:
            config = self.load_full_config()

async def setup(bot):
    await bot.add_cog(Roulette(bot))