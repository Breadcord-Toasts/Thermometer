import asyncio
import contextlib
import io
import time

from discord import app_commands
from discord.ext import commands

import breadcord
from breadcord.module import ModuleCog
from .helpers import *


class Thermometer(ModuleCog, WhoisHelper):
    def __init__(self, module_id: str):
        super().__init__(module_id)
        super(WhoisHelper, self).__init__()

        self.cog_load_time: datetime = datetime.now()

        self.ctx_menu = app_commands.ContextMenu(
            name="Who got mentioned",
            callback=self.role_mention_members_ctx_menu,
        )
        self.bot.tree.add_command(self.ctx_menu)

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
            f"Bot has been online for {readable_timedelta(uptime)}, last started <t:{started_timestamp}>"
        )

    @commands.hybrid_command(aliases=["pfp"], description="Gets a user's profile picture.")
    async def avatar(self, ctx: commands.Context, user: discord.User | None = None) -> None:
        user = user or ctx.author

        await ctx.reply(
            embed=discord.Embed(
                title=(
                    f"{user.name}'s avatar"
                    if user.display_name.endswith("s")
                    else f"{user.display_name}'s avatar"
                )
            ).set_image(
                url=enhance_asset_image(user.avatar).url,
            )
        )

    @commands.hybrid_command(description="Gets info about a user.")
    async def whois(self, ctx: commands.Context, user: discord.User | None = None) -> None:
        user: discord.User = await self.bot.fetch_user(user.id) if user else ctx.author
        user_info = await self.get_user_info(user)
        embeds = []

        async def fetch_avatar() -> discord.File | None:
            with contextlib.suppress(discord.NotFound):
                return discord.File(
                    fp=io.BytesIO(await enhance_asset_image(user.avatar).read()),
                    filename="avatar.gif" if user.avatar.is_animated() else "avatar.png",
                )

        async def fetch_banner() -> discord.File | None:
            if user.banner is None:
                return None
            with contextlib.suppress(discord.NotFound):
                return discord.File(
                    fp=io.BytesIO(await enhance_asset_image(user.banner).read()),
                    filename="banner.gif" if user.banner.is_animated() else "banner.png",
                )

        if user in ctx.guild.members:
            user: discord.Member = ctx.guild.get_member(user.id)
            user_info |= await self.get_member_info(user)
            embeds.extend(await self.get_member_activity_embeds(user))

        avatar_task = asyncio.create_task(fetch_avatar())
        banner_task = asyncio.create_task(fetch_banner())
        done, pending = await asyncio.wait(
            [avatar_task, banner_task],
            return_when=asyncio.ALL_COMPLETED,
            timeout=1,
        )

        embeds.insert(0, build_info_embed(
            user_info,
            title="User info",
            colour=user.colour,
            thumbnail=enhance_asset_image(user.avatar).url,
            image=enhance_asset_image(user.banner).url if user.banner else None,
        ))

        avatar_file, banner_file = None, None
        if avatar_task in done:
            avatar_file = avatar_task.result()
            if avatar_file:
                embeds[0].set_thumbnail(url=f"attachment://{avatar_file.filename}")

        if banner_task in done:
            banner_file = banner_task.result()
            if banner_file:
                embeds[0].set_image(url=f"attachment://{banner_file.filename}")

        response = await ctx.reply(
            embeds=embeds,
            files=tuple(filter(bool, (avatar_file, banner_file))),
        )

        if pending:
            if avatar_task in pending:
                avatar_file = await avatar_task
                if avatar_file:
                    embeds[0].set_thumbnail(url=f"attachment://{avatar_file.filename}")
            if banner_task in pending:
                banner_file = await banner_task
                if banner_file:
                    embeds[0].set_image(url=f"attachment://{banner_file.filename}")

            if not (avatar_file or banner_file):
                return
            if isinstance(avatar_file, discord.File):
                avatar_file.fp.seek(0)
            if isinstance(banner_file, discord.File):
                banner_file.fp.seek(0)
            await response.edit(
                embeds=embeds,
                attachments=tuple(filter(bool, (avatar_file, banner_file))),
            )

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
        await ctx.reply(embed=build_info_embed(
            await GuildInfoHelper.get_guild_info(ctx.guild),
            title="Guild info",
            thumbnail=enhance_asset_image(ctx.guild.icon).url if ctx.guild.icon else None,
            image=enhance_asset_image(ctx.guild.banner).url if ctx.guild.banner else None,
            inline_fields=False,
        ))

    async def role_mention_members_ctx_menu(self, interaction: discord.Interaction, message: discord.Message) -> None:
        if not message.role_mentions:
            await interaction.response.send_message("No role mentions found.", ephemeral=True)
            return

        embeds_to_be_sent = [
            discord.Embed(
                title=f'Members with the role "{role.name}" ' + ("(top 25)" if len(role.members) > 25 else ""),
                description=", ".join([member.mention for member in role.members[:25]]),
                colour=role.colour,
            )
            for role in message.role_mentions
            if role.members
        ][:10]
        await interaction.response.send_message(
            f"Only showing 10 of the {len(message.role_mentions)} role mentions."
            if len(message.role_mentions) > 10 else "",
            embeds=embeds_to_be_sent,
            ephemeral=True,
        )


async def setup(bot: breadcord.Bot):
    await bot.add_cog(Thermometer("thermometer"))
