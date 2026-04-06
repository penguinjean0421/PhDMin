import os
import json
import discord

from discord.ext import commands
from discord import ui


# --- Constants & Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Moves up one level if this file is inside a 'cogs' folder
DATA_FILE = os.path.join(BASE_DIR, "..", "ticket.json")

CATEGORY_NAME = "문의-티켓"
ARCHIVE_CATEGORY_NAME = "종료된-티켓"
SUPPORT_ROLE_NAME = "상담원"


def get_next_ticket_number(guild_id: int, guild_name: str) -> int:
    """
    Increments and returns the ticket count for a specific guild.
    Stored in a JSON file to persist across restarts.
    """
    data = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            data = {}

    guild_key = str(guild_id)

    if guild_key not in data:
        data[guild_key] = {
            "guild_name": guild_name,
            "ticket_count": 0
        }

    data[guild_key]["ticket_count"] += 1
    data[guild_key]["guild_name"] = guild_name

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return data[guild_key]["ticket_count"]


class CloseView(ui.View):
    """View containing the button to close and archive a ticket."""

    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(
        label="티켓 닫기 🔒",
        style=discord.ButtonStyle.danger,
        custom_id="close_ticket"
    )
    async def close_ticket(
        self,
        interaction: discord.Interaction,
        button: ui.Button
    ):
        guild = interaction.guild
        channel = interaction.channel

        archive_category = discord.utils.get(
            guild.categories,
            name=ARCHIVE_CATEGORY_NAME
        )

        if archive_category is None:
            archive_category = await guild.create_category(ARCHIVE_CATEGORY_NAME)

        await channel.edit(
            name=f"closed-{channel.name}",
            category=archive_category,
            sync_permissions=True
        )

        await interaction.response.edit_message(
            content="이 티켓은 종료되었으며, 보관실로 이동되었습니다.",
            view=None
        )


class TicketView(ui.View):
    """View containing the button to open a new ticket."""

    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(
        label="티켓 열기",
        style=discord.ButtonStyle.primary,
        custom_id="open_ticket"
    )
    async def open_ticket(
        self,
        interaction: discord.Interaction,
        button: ui.Button
    ):
        guild = interaction.guild
        user = interaction.user

        # Get incremented ticket number for this server
        ticket_number = get_next_ticket_number(guild.id, guild.name)

        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
        if category is None:
            category = await guild.create_category(CATEGORY_NAME)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            ),
            guild.me: discord.PermissionOverwrite(view_channel=True)
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{ticket_number}",
            overwrites=overwrites,
            category=category
        )

        await interaction.response.send_message(
            f"{channel.mention} 생성 완료!",
            ephemeral=True
        )
        await channel.send(
            f"{user.mention}님, 문의 내용을 남겨주세요.",
            view=CloseView()
        )


class TicketSystem(commands.Cog):
    """Cog for managing the ticket system setup and events."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="setup")
    @commands.has_permissions(administrator=True)
    async def setup_ticket(self, ctx: commands.Context):
        """Sends the initial ticket creation embed."""
        embed = discord.Embed(
            title="📩 문의 지원",
            description="아래 버튼을 눌러 티켓을 생성하세요.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed, view=TicketView())


async def setup(bot: commands.Bot):
    """Standard setup function for loading the cog."""
    # Register persistent views to handle buttons after bot restart
    bot.add_view(TicketView())
    bot.add_view(CloseView())
    await bot.add_cog(TicketSystem(bot))