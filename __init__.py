import time
from datetime import datetime, timezone, timedelta
from typing import List

import discord
from discord import app_commands
from discord.utils import escape_markdown

import breadcord
from breadcord.module import ModuleCog


class Helpers:

    @staticmethod
    def readable_timedelta(duration: timedelta) -> str:
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        string = ""
        if duration.days:
            string += f"{round(duration.days)} days "
        if hours:
            string += f"{round(hours)} hours "
        if minutes:
            string += f"{round(minutes)} minutes "
        string += f"{round(seconds)} seconds"
        return string

    @staticmethod
    def enhance_asset_image(asset: discord.Asset) -> discord.Asset:
        return asset.with_size(4096).with_static_format("png")

    @staticmethod
    async def info_to_string(info: dict) -> str:
        return "".join(f"**{key}:** {value}\n" for key, value in info.items() if value is not None)

    async def build_info_embed(
        self,
        info: dict,
        /,
        *,
        colour: discord.Colour | discord.Color | None = None,
        thumbnail: str | None = None,
        image: str | None = None,
    ) -> discord.Embed:
        embed = discord.Embed(title="User info", description="", colour=colour, timestamp=datetime.now())
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        if image:
            embed.set_image(url=image)

        for key, value in info.items():
            if isinstance(value, dict):
                embed.add_field(name=key, value=await self.info_to_string(value))
                continue
            embed.description += await self.info_to_string({key: value})
        return embed

    @staticmethod
    async def get_user_info(user: discord.User, /) -> dict:
        created_at = int(time.mktime(user.created_at.timetuple()))
        user_type = None
        if user.bot:
            user_type = "Bot"
        if user.system:
            user_type = "System"

        return {
            "Username": escape_markdown(user.name),
            "Discriminator": user.discriminator,
            "Mention": user.mention,
            "Nickname": escape_markdown(user.display_name) if user.display_name != user.name else None,
            "ID": user.id,
            "User type": user_type,
            "Created at": f"<t:{created_at}> (<t:{created_at}:R>)",
        }

    @staticmethod
    async def get_member_info(member: discord.Member, /) -> dict:
        colour = member.colour
        joined_at = int(time.mktime(member.joined_at.timetuple()))
        is_timed_out = member.is_timed_out()
        timeout_timestamp = int(time.mktime(member.timed_out_until.timetuple())) if is_timed_out else None
        return {
            "Joined at": f"<t:{joined_at}> (<t:{joined_at}:R>)",
            "Status": str(member.status).title(),
            "On mobile": member.is_on_mobile() or None,
            "Timed out until": f"<t:{timeout_timestamp}> (<t:{timeout_timestamp}:R>)"  if is_timed_out else None,
            # As of writing, this version of discord.py is not on PyPI
            "Has rejoined": (
                discord.version_info.major >= 2 and discord.version_info.minor >= 2 and member.flags.did_rejoin
            )
            or None,
            "Is bot": member.bot or None,
            "Name colour": colour if colour != discord.Colour.default() else None,
            "Roles": ", ".join(role.mention for role in reversed(member.roles) if role.name != "@everyone"),
        }

    async def create_spotify_embed(self, activity: discord.Spotify) -> discord.Embed:
        embed = discord.Embed(
            title=f"Listening to: {activity.title}",
            description=await self.info_to_string(
                {"Artist": ", ".join(activity.artists), "Album": activity.album, "Song url": activity.track_url}
            ),
            colour=activity.colour,
        )
        embed.set_thumbnail(url=activity.album_cover_url)
        return embed

    async def create_game_embed(self, activity: discord.Game) -> discord.Embed:
        started_at = int(time.mktime(activity.start.timetuple())) if activity.start else None
        ends_at = int(time.mktime(activity.end.timetuple())) if activity.end else None
        return discord.Embed(
            title=f"Playing: {activity.name}",
            description=await self.info_to_string(
                {
                    "Started at": f"<t:{started_at}> (<t:{started_at}:R>)" if started_at else None,
                    "Ends at": f"<t:{ends_at}> (<t:{ends_at}:R>)" if ends_at else None,
                }
            ),
            colour=discord.Colour.random(),
        )

    async def create_stream_embed(self, activity: discord.Streaming) -> discord.Embed:
        colour = (discord.Colour.random(),)
        platform = activity.platform

        if platform.lower() == "youtube":
            colour = discord.Colour.from_str("#fe0000")
        elif platform.lower() == "twitch":
            colour = discord.Colour.from_str("#9147ff")

        return discord.Embed(
            title=f"Streaming: {activity.name}",
            description=await self.info_to_string(
                {
                    "Game": activity.game,
                    "Platform": platform,
                    "Twitch name": activity.twitch_name,
                    "URL": activity.url,
                }
            ),
            colour=colour,
        )

    async def create_generic_activity_embed(self, activity: discord.Activity) -> discord.Embed:
        embed = discord.Embed(
            title=f"Activity: {activity.name}",
            description=activity.details,
        )

        started_at = int(time.mktime(activity.start.timetuple())) if activity.start else None
        ends_at = int(time.mktime(activity.end.timetuple())) if activity.end else None
        duration = datetime.now(timezone.utc) - activity.start if activity.start else None
        embed.add_field(
            name=" ",
            value=await self.info_to_string(
                {
                    "State": activity.state or None,
                    "Started at": f"<t:{started_at}> (<t:{started_at}:R>)" if started_at else None,
                    "Ends at": f"<t:{ends_at}> (<t:{ends_at}:R>)" if ends_at else None,
                    "Duration": self.readable_timedelta(duration) if duration else None,
                    "URL": activity.url,
                }
            ),
        )
        embed.set_thumbnail(url=activity.large_image_url)
        return embed

    async def get_member_activity_embeds(self, member: discord.Member, /) -> List[discord.Embed]:
        embeds: List[discord.Embed] = []
        for activity in member.activities:
            match type(activity):
                case discord.Spotify:
                    embeds.append(await self.create_spotify_embed(activity))
                case discord.Activity:
                    embeds.append(await self.create_generic_activity_embed(activity))
                case discord.Game:
                    embeds.append(await self.create_game_embed(activity))
                case discord.Streaming:
                    embeds.append(await self.create_stream_embed(activity))

        return embeds



class Thermometer(ModuleCog):
    def __init__(self, module_id: str):
        super().__init__(module_id)
        self.cog_load_time: datetime = datetime.now()
        self.helper = Helpers()

    @app_commands.command(description="Returns how long the bot has been running.")
    async def uptime(self, interaction: discord.Interaction) -> None:
        # This is technically wrong, as it's the cog uptime, not necessarily the bot uptime, but eh
        uptime = datetime.now() - self.cog_load_time
        started_timestamp = round(time.mktime(self.cog_load_time.timetuple()))

        await interaction.response.send_message(
            f"Bot has been online for {self.helper.readable_timedelta(uptime)}, last started <t:{started_timestamp}>"
        )

    @app_commands.command(description="Gets info about a user.")
    async def whois(self, interaction: discord.Interaction, user: discord.User = None) -> None:
        user: discord.User = await self.bot.fetch_user(user.id) if user else interaction.user
        user_info = await self.helper.get_user_info(user)
        banner = self.helper.enhance_asset_image(user.banner).url if user.banner else None
        embeds = []

        if user in interaction.guild.members:
            user: discord.Member = interaction.guild.get_member(user.id)
            user_info |= await self.helper.get_member_info(user)
            embeds.extend(await self.helper.get_member_activity_embeds(user))

        embeds.insert(
            0,
            await self.helper.build_info_embed(
                user_info,
                colour=user_info["Role colour"] if "Role colour" in user_info else None,
                thumbnail=self.helper.enhance_asset_image(user.display_avatar).url,
                image=banner,
            ),
        )

        await interaction.response.send_message(embeds=embeds[:10])


async def setup(bot: breadcord.Bot):
    await bot.add_cog(Thermometer("thermometer"))
