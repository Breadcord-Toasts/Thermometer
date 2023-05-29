import time
from datetime import datetime

import discord
from discord.ext import commands

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

    @commands.hybrid_command(description="Returns how long the bot has been running.")
    async def uptime(self, ctx: commands.Context) -> None:
        # This is technically wrong, as it's the cog uptime, not necessarily the bot uptime, but eh
        uptime = datetime.now() - self.cog_load_time
        started_timestamp = round(time.mktime(self.cog_load_time.timetuple()))

        await ctx.reply(
            f"Bot has been online for {GeneralHelper.readable_timedelta(uptime)}, last started <t:{started_timestamp}>"
        )

    @commands.hybrid_command(description="Gets info about a user.")
    async def whois(self, ctx: commands.Context, user: discord.User | None = None) -> None:
        user: discord.User = await self.bot.fetch_user(user.id) if user else ctx.author
        user_info = await self.get_user_info(user)
        banner = GeneralHelper.enhance_asset_image(user.banner).url if user.banner else None
        embeds = []

        if user in ctx.guild.members:
            user: discord.Member = ctx.guild.get_member(user.id)
            user_info |= await self.get_member_info(user)
            embeds.extend(await self.get_member_activity_embeds(user))

        embeds.insert(0, GeneralHelper.build_info_embed(
            user_info,
            title="User info",
            colour=user_info["Role colour"] if "Role colour" in user_info else None,
            thumbnail=GeneralHelper.enhance_asset_image(user.display_avatar).url,
            image=banner,
        ))

        await ctx.reply(embeds=embeds[:10])

    @commands.hybrid_group(name="guild", description="Various guild related info")
    async def guild_info_group(self, ctx: commands.Context) -> None:
        # This function is executed when "guild" is run as a message command, it will never run from a slash command.
        await self.guild_info(ctx)

    @guild_info_group.command(name="channels", description="Get the guilds channels.")
    async def guild_channels(self, ctx: commands.Context) -> None:
        channels = [
            channel.mention
            for channel in ctx.guild.channels
            if not isinstance(channel, discord.CategoryChannel)
        ]
        await ctx.reply(embed=discord.Embed(
            title="Guild channels",
            description=f"**Channel count:** {len(channels)}\n\n" + "\n".join(channels)
        ))

    @guild_info_group.command(name="emojis", description="Get the guilds emojis.")
    async def guild_emojis(self, ctx: commands.Context) -> None:
        emojis = ctx.guild.emojis
        await ctx.reply(embed=discord.Embed(
            title="Guild emojis",
            description=f"**Emoji count:** {len(emojis)}\n\n" + "".join(map(str, emojis))
        ))

    @guild_info_group.command(name="members", description="Get the guilds members.")
    async def guild_members(self, ctx: commands.Context) -> None:
        members = sorted(ctx.guild.members, key=lambda x: x.name)
        await ctx.reply(embed=discord.Embed(
            title="Guild members",
            description=f"**Member count:** {len(members)}\n\n" + ", ".join([member.mention for member in members]),
        ))

    @guild_info_group.command(name="info", description="Gets general info about the guild.")
    async def guild_info(self, ctx: commands.Context) -> None:
        await ctx.reply(embed=GeneralHelper.build_info_embed(
            await GuildInfoHelper.get_guild_info(ctx.guild),
            title="Guild info",
            thumbnail=GeneralHelper.enhance_asset_image(ctx.guild.icon).url if ctx.guild.icon else None,
            image=GeneralHelper.enhance_asset_image(ctx.guild.banner).url if ctx.guild.banner else None,
            inline_fields=False,
        ))


async def setup(bot: breadcord.Bot):
    await bot.add_cog(Thermometer("thermometer"))
