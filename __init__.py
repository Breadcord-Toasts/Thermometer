import time
from datetime import datetime

import discord
from discord import app_commands

import breadcord
from breadcord.module import ModuleCog
from .helpers import GeneralHelper, WhoisHelper, GuildInfoHelper


class Thermometer(ModuleCog, WhoisHelper):
    def __init__(self, module_id: str):
        super().__init__(module_id)
        super(WhoisHelper, self).__init__()

        self.cog_load_time: datetime = datetime.now()

    async def cog_load(self) -> None:
        await self.open_session()

    async def cog_unload(self) -> None:
        await self.close_session()

    @app_commands.command(description="Returns how long the bot has been running.")
    async def uptime(self, interaction: discord.Interaction) -> None:
        # This is technically wrong, as it's the cog uptime, not necessarily the bot uptime, but eh
        uptime = datetime.now() - self.cog_load_time
        started_timestamp = round(time.mktime(self.cog_load_time.timetuple()))

        await interaction.response.send_message(
            f"Bot has been online for {GeneralHelper.readable_timedelta(uptime)}, last started <t:{started_timestamp}>"
        )

    @app_commands.command(description="Gets info about a user.")
    async def whois(self, interaction: discord.Interaction, user: discord.User | None = None) -> None:
        user: discord.User = await self.bot.fetch_user(user.id) if user else interaction.user
        user_info = await self.get_user_info(user)
        banner = GeneralHelper.enhance_asset_image(user.banner).url if user.banner else None
        embeds = []

        if user in interaction.guild.members:
            user: discord.Member = interaction.guild.get_member(user.id)
            user_info |= await self.get_member_info(user)
            embeds.extend(await self.get_member_activity_embeds(user))

        embeds.insert(
            0,
            await GeneralHelper.build_info_embed(
                user_info,
                title="User info",
                colour=user_info["Role colour"] if "Role colour" in user_info else None,
                thumbnail=GeneralHelper.enhance_asset_image(user.display_avatar).url,
                image=banner,
            ),
        )

        await interaction.response.send_message(embeds=embeds[:10])

    guild_info_group = app_commands.Group(name="guild", description="Various guild related info")

    @guild_info_group.command(name="channels", description="Get the guilds channels.")
    async def guild_channels(self, interaction: discord.Interaction) -> None:
        channels = [
            channel.mention
            for channel in interaction.guild.channels
            if not isinstance(channel, discord.CategoryChannel)
        ]
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Guild channels", description=f"**Channel count:** {len(channels)}\n\n" + "\n".join(channels)
            )
        )

    @guild_info_group.command(name="emojis", description="Get the guilds emojis.")
    async def guild_emojis(self, interaction: discord.Interaction) -> None:
        emojis = interaction.guild.emojis
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Guild emojis", description=f"**Emoji count:** {len(emojis)}\n\n" + "".join(map(str, emojis))
            )
        )

    @guild_info_group.command(name="members", description="Get the guilds members.")
    async def guild_members(self, interaction: discord.Interaction) -> None:
        members = sorted(interaction.guild.members, key=lambda x: x.name)
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Guild members",
                description=f"**Member count:** {len(members)}\n\n" + ", ".join([member.mention for member in members]),
            )
        )

    @guild_info_group.command(name="info", description="Gets general info about the guild.")
    async def guild_info(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild

        embed = await GeneralHelper.build_info_embed(
            await GuildInfoHelper.get_guild_info(guild),
            title="Guild info",
            thumbnail=GeneralHelper.enhance_asset_image(guild.icon).url if guild.icon else None,
            image=GeneralHelper.enhance_asset_image(guild.banner).url if guild.banner else None,
            inline_fields=False,
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot: breadcord.Bot):
    await bot.add_cog(Thermometer("thermometer"))
