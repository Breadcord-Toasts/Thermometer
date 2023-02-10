import time
from datetime import datetime, timezone

import discord

from . import GeneralHelper


class WhoisHelper:
    @classmethod
    async def build_info_embed(
        cls,
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
                embed.add_field(name=key, value=await GeneralHelper.info_to_string(value))
                continue
            embed.description += await GeneralHelper.info_to_string({key: value})
        return embed

    @classmethod
    async def get_user_info(cls, user: discord.User, /) -> dict:
        created_at = int(time.mktime(user.created_at.timetuple()))
        user_type = None
        if user.bot:
            user_type = "Bot"
        if user.system:
            user_type = "System"

        return {
            "Username": discord.utils.escape_markdown(user.name),
            "Discriminator": user.discriminator,
            "Mention": user.mention,
            "Nickname": discord.utils.escape_markdown(user.display_name) if user.display_name != user.name else None,
            "ID": user.id,
            "User type": user_type,
            "Created at": f"<t:{created_at}> (<t:{created_at}:R>)",
        }

    @classmethod
    async def get_member_info(cls, member: discord.Member, /) -> dict:
        colour = member.colour
        joined_at = int(time.mktime(member.joined_at.timetuple()))
        is_timed_out = member.is_timed_out()
        timeout_timestamp = int(time.mktime(member.timed_out_until.timetuple())) if is_timed_out else None
        return {
            "Joined at": f"<t:{joined_at}> (<t:{joined_at}:R>)",
            "Status": str(member.status).title(),
            "On mobile": member.is_on_mobile() or None,
            "Timed out until": f"<t:{timeout_timestamp}> (<t:{timeout_timestamp}:R>)" if is_timed_out else None,
            # As of writing, this version of discord.py is not on PyPI
            "Has rejoined": (
                discord.version_info.major >= 2 and discord.version_info.minor >= 2 and member.flags.did_rejoin
            )
            or None,
            "Is bot": member.bot or None,
            "Name colour": colour if colour != discord.Colour.default() else None,
            "Roles": ", ".join(role.mention for role in reversed(member.roles) if role.name != "@everyone"),
        }

    @classmethod
    async def create_spotify_embed(cls, activity: discord.Spotify) -> discord.Embed:
        embed = discord.Embed(
            title=f"Listening to: {activity.title}",
            description=await GeneralHelper.info_to_string(
                {"Artist": ", ".join(activity.artists), "Album": activity.album, "Song url": activity.track_url}
            ),
            colour=activity.colour,
        )
        embed.set_thumbnail(url=activity.album_cover_url)
        return embed

    @classmethod
    async def create_game_embed(cls, activity: discord.Game) -> discord.Embed:
        started_at = int(time.mktime(activity.start.timetuple())) if activity.start else None
        ends_at = int(time.mktime(activity.end.timetuple())) if activity.end else None
        return discord.Embed(
            title=f"Playing: {activity.name}",
            description=await GeneralHelper.info_to_string(
                {
                    "Started at": f"<t:{started_at}> (<t:{started_at}:R>)" if started_at else None,
                    "Ends at": f"<t:{ends_at}> (<t:{ends_at}:R>)" if ends_at else None,
                }
            ),
            colour=discord.Colour.random(),
        )

    @classmethod
    async def create_stream_embed(cls, activity: discord.Streaming) -> discord.Embed:
        colour = (discord.Colour.random(),)
        platform = activity.platform

        if platform.lower() == "youtube":
            colour = discord.Colour.from_str("#fe0000")
        elif platform.lower() == "twitch":
            colour = discord.Colour.from_str("#9147ff")

        return discord.Embed(
            title=f"Streaming: {activity.name}",
            description=await GeneralHelper.info_to_string(
                {
                    "Game": activity.game,
                    "Platform": platform,
                    "Twitch name": activity.twitch_name,
                    "URL": activity.url,
                }
            ),
            colour=colour,
        )

    @classmethod
    async def create_generic_activity_embed(cls, activity: discord.Activity) -> discord.Embed:
        embed = discord.Embed(
            title=f"Activity: {activity.name}",
            description=activity.details,
        )

        started_at = int(time.mktime(activity.start.timetuple())) if activity.start else None
        ends_at = int(time.mktime(activity.end.timetuple())) if activity.end else None
        duration = datetime.now(timezone.utc) - activity.start if activity.start else None
        embed.add_field(
            name=" ",
            value=await GeneralHelper.info_to_string(
                {
                    "State": activity.state or None,
                    "Started at": f"<t:{started_at}> (<t:{started_at}:R>)" if started_at else None,
                    "Ends at": f"<t:{ends_at}> (<t:{ends_at}:R>)" if ends_at else None,
                    "Duration": GeneralHelper.readable_timedelta(duration) if duration else None,
                    "URL": activity.url,
                }
            ),
        )
        embed.set_thumbnail(url=activity.large_image_url)
        return embed

    @classmethod
    async def get_member_activity_embeds(cls, member: discord.Member, /) -> list[discord.Embed]:
        embeds: list[discord.Embed] = []
        for activity in member.activities:
            match type(activity):
                case discord.Spotify:
                    embeds.append(await cls.create_spotify_embed(activity))
                case discord.Activity:
                    embeds.append(await cls.create_generic_activity_embed(activity))
                case discord.Game:
                    embeds.append(await cls.create_game_embed(activity))
                case discord.Streaming:
                    embeds.append(await cls.create_stream_embed(activity))

        return embeds
