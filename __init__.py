import time
from datetime import datetime

import discord
from discord import app_commands

import breadcord
from breadcord.module import ModuleCog
from .helpers import GeneralHelper, WhoisHelper


class Thermometer(ModuleCog):
    def __init__(self, module_id: str):
        super().__init__(module_id)
        self.cog_load_time: datetime = datetime.now()

    @app_commands.command(description="Returns how long the bot has been running.")
    async def uptime(self, interaction: discord.Interaction) -> None:
        # This is technically wrong, as it's the cog uptime, not necessarily the bot uptime, but eh
        uptime = datetime.now() - self.cog_load_time
        started_timestamp = round(time.mktime(self.cog_load_time.timetuple()))

        await interaction.response.send_message(
            f"Bot has been online for {GeneralHelper.readable_timedelta(uptime)}, last started <t:{started_timestamp}>"
        )

    @app_commands.command(description="Gets info about a user.")
    async def whois(self, interaction: discord.Interaction, user: discord.User = None) -> None:
        user: discord.User = await self.bot.fetch_user(user.id) if user else interaction.user
        user_info = await WhoisHelper.get_user_info(user)
        banner = GeneralHelper.enhance_asset_image(user.banner).url if user.banner else None
        embeds = []

        if user in interaction.guild.members:
            user: discord.Member = interaction.guild.get_member(user.id)
            user_info |= await WhoisHelper.get_member_info(user)
            embeds.extend(await WhoisHelper.get_member_activity_embeds(user))

        embeds.insert(
            0,
            await WhoisHelper.build_info_embed(
                user_info,
                colour=user_info["Role colour"] if "Role colour" in user_info else None,
                thumbnail=GeneralHelper.enhance_asset_image(user.display_avatar).url,
                image=banner,
            ),
        )

        await interaction.response.send_message(embeds=embeds[:10])


async def setup(bot: breadcord.Bot):
    await bot.add_cog(Thermometer("thermometer"))
