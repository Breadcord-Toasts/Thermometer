import asyncio
import time

from discord import app_commands
from discord.ext import commands

import breadcord
from breadcord.module import ModuleCog
from .helpers import *

load_time: datetime = datetime.now()

class Thermometer(ModuleCog):
    def __init__(self, module_id: str):
        super().__init__(module_id)
        
        self.ctx_menu = app_commands.ContextMenu(
            name="Who got mentioned",
            callback=self.role_mention_members_ctx_menu,
        )
        self.bot.tree.add_command(self.ctx_menu)

    @commands.hybrid_command(description="Returns how long the bot has been running.")
    async def uptime(self, ctx: commands.Context) -> None:
        # This is technically wrong, as it's the cog uptime, not necessarily the bot uptime, but eh
        global load_time
        uptime = datetime.now() - load_time
        started_timestamp = round(time.mktime(load_time.timetuple()))
        await ctx.reply(f"Bot has been online for {readable_timedelta(uptime)}, last started <t:{started_timestamp}>")

    @commands.hybrid_command(aliases=["pfp"], description="Gets a user's profile picture.")
    async def avatar(
        self,
        ctx: commands.Context,
        user: discord.User | None = None,
        global_avatar: bool = False,
    ) -> None:
        target: discord.User | discord.Member = user or ctx.author
        avatar: discord.Asset
        if global_avatar:
            if not target.avatar:
                await ctx.reply("User has no global avatar.")
                return
            avatar = target.avatar
        else:
            avatar = target.display_avatar
        await ctx.reply(
            embed=discord.Embed(
                title=f"{target.mention}'s avatar" if user else "Your avatar",
                colour=target.colour if isinstance(target, discord.Member) else None,
            ).set_image(url=max_size(avatar).url),
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.hybrid_command(description="Gets info about a user.")
    async def whois(self, ctx: commands.Context, user: discord.User | None = None) -> None:
        target: discord.User | discord.Member = user or ctx.author
        # Ensure we have complete saturated objects
        if ctx.guild and target in ctx.guild.members:
            target = await ctx.guild.fetch_member(target.id)
        else:
            target = await self.bot.fetch_user(target.id)

        user_details: dict[str, Any | None] = await WhoisHelper.get_user_details(target)
        if isinstance(target, discord.Member):
            user_details |= await WhoisHelper.get_member_details(target)

        target_info_embed: discord.Embed = build_info_embed(
            user_details,
            title="User info" if user is not None else "Own user info",
            colour=target.colour,
            thumbnail=max_size(target.avatar if target.avatar else target.default_avatar).url,
            image=max_size(target.banner).url if target.banner else None,
        )
        embeds: list[discord.Embed] = [target_info_embed]
        if isinstance(target, discord.Member):
            embeds.extend(await WhoisHelper.get_member_activity_embeds(target))
            
        response: discord.Message = await ctx.reply(embeds=embeds)
        if target.avatar is None and target.banner is None:
            return
        
        avatar_file, banner_file = await asyncio.gather(
            fetch_asset(target.avatar, "avatar"), 
            fetch_asset(target.banner, "banner"), 
        )
        if avatar_file:
            target_info_embed.set_thumbnail(url=f"attachment://{avatar_file.filename}")
        if banner_file:
            target_info_embed.set_image(url=f"attachment://{banner_file.filename}")
        await response.edit(
            embeds=embeds,
            attachments=[file for file in (avatar_file, banner_file) if file is not None]
        )

    @commands.hybrid_group(name="guild", description="Various guild related info")
    @commands.guild_only()
    async def guild_info_group(self, ctx: commands.Context) -> None:
        # This function is executed when "guild" is run as a message command, it will never run from a slash command.
        await self.guild_info(ctx)

    @guild_info_group.command(name="channels", description="Get the guilds channels.")
    async def guild_channels(self, ctx: commands.Context) -> None:
        if not ctx.guild:
            await ctx.reply("This command can only be used in a guild.")
            return
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
        if not ctx.guild:
            await ctx.reply("This command can only be used in a guild.")
            return
        await ctx.reply(embed=discord.Embed(
            title="Guild emojis",
            description=f"**Emoji count:** {len(ctx.guild.emojis)}\n\n" + "".join(map(str, ctx.guild.emojis))
        ))

    @guild_info_group.command(name="members", description="Get the guilds members.")
    async def guild_members(self, ctx: commands.Context) -> None:
        if not ctx.guild:
            await ctx.reply("This command can only be used in a guild.")
            return
        members = sorted(ctx.guild.members, key=lambda x: x.name)
        await ctx.reply(embed=discord.Embed(
            title="Guild members",
            description=f"**Member count:** {len(members)}\n\n" + ", ".join([member.mention for member in members]),
        ))

    @guild_info_group.command(name="info", description="Gets general info about the guild.")
    async def guild_info(self, ctx: commands.Context) -> None:
        if not ctx.guild:
            await ctx.reply("This command can only be used in a guild.")
            return
        await ctx.reply(embed=build_info_embed(
            await GuildInfoHelper.get_guild_info(ctx.guild),
            title="Guild info",
            thumbnail=max_size(ctx.guild.icon).url if ctx.guild.icon else None,
            image=max_size(ctx.guild.banner).url if ctx.guild.banner else None,
            inline_fields=False,
        ))

    async def role_mention_members_ctx_menu(self, interaction: discord.Interaction, message: discord.Message) -> None:
        if not message.role_mentions:
            await interaction.response.send_message("No role mentions found.", ephemeral=True)
            return
        await interaction.response.send_message(
            f"Only showing 10 of the {len(message.role_mentions)} role mentions."
            if len(message.role_mentions) > 10 else "",
            embeds=[
                discord.Embed(
                    title=f'Members with the role "{role.name}" ' + ("(top 25)" if len(role.members) > 25 else ""),
                    description=", ".join([member.mention for member in role.members[:25]]),
                    colour=role.colour,
                )
                for role in message.role_mentions
                if role.members
            ][:10],
            ephemeral=True,
        )


async def setup(bot: breadcord.Bot, module: breadcord.module.Module) -> None:
    await bot.add_cog(Thermometer(module.id))
