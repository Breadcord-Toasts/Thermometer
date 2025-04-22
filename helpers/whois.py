import time
from datetime import datetime, timezone
from typing import Any

import discord

from . import info_to_string, readable_timedelta


class WhoisHelper:
    @staticmethod
    async def get_user_details(user: discord.User | discord.Member, /) -> dict[str, Any | None]:
        created_at = int(time.mktime(user.created_at.timetuple()))
        user_type: str = "Normal"
        if user.bot:
            user_type = "Bot"
        if user.system:
            user_type = "System"

        return {
            "Username": discord.utils.escape_markdown(user.name),  # Escaped due to non-migrated users
            "Global display name": discord.utils.escape_markdown(user.global_name) if user.global_name else None,
            "Discriminator": user.discriminator if user.discriminator != "0" else None,
            "Mention": user.mention,
            "ID": user.id,
            "User type": user_type,
            "Created at": f"<t:{created_at}> (<t:{created_at}:R>)",
        }

    @staticmethod
    async def get_member_details(member: discord.Member, /) -> dict[str, Any | None]:
        colour = member.colour
        joined_at: int | None = int(time.mktime(member.joined_at.timetuple())) if member.joined_at else None
        timeout_timestamp: int | None = None
        if member.is_timed_out() and member.timed_out_until:
            timeout_timestamp = int(time.mktime(member.timed_out_until.timetuple()))

        statuses: list[str] = [s for s in [
            f"Desktop ({member.desktop_status})" if member.desktop_status else None,
            f"Mobile ({member.mobile_status})" if member.mobile_status else None,
            f"Web ({member.web_status})" if member.web_status else None,
        ] if s]
        return {
            "Joined at": f"<t:{joined_at}> (<t:{joined_at}:R>)" if joined_at else None,
            "Status": str(member.status).title(),
            "Presence status": 
            str(member.status) + ((", " + ", ".join(statuses)) if statuses else ""),
            "Timed out until": f"<t:{timeout_timestamp}> (<t:{timeout_timestamp}:R>)" if timeout_timestamp else None,
            # As of writing, this version of discord.py is not on PyPI
            "Has rejoined": member.flags.did_rejoin or None,
            "Name colour": colour if colour != discord.Colour.default() else None,
            "Roles": ", ".join(role.mention for role in reversed(member.roles) if role.name != "@everyone") or None,
        }

    @staticmethod
    async def create_spotify_embed(activity: discord.Spotify) -> discord.Embed:
        return discord.Embed(
            title=f"Listening to: {activity.title}",
            description=info_to_string(
                {"Artist": ", ".join(activity.artists), "Album": activity.album, "Song url": activity.track_url}
            ),
            colour=activity.colour,
        ).set_thumbnail(url=activity.album_cover_url)

    @staticmethod
    async def create_game_embed(activity: discord.Game) -> discord.Embed:
        started_at = int(time.mktime(activity.start.timetuple())) if activity.start else None
        ends_at = int(time.mktime(activity.end.timetuple())) if activity.end else None
        return discord.Embed(
            title=f"Playing: {activity.name}",
            description=info_to_string(
                {
                    "Started at": f"<t:{started_at}> (<t:{started_at}:R>)" if started_at else None,
                    "Ends at": f"<t:{ends_at}> (<t:{ends_at}:R>)" if ends_at else None,
                }
            ),
            colour=discord.Colour.random(seed=activity.name),
        )

    @staticmethod
    async def create_stream_embed(activity: discord.Streaming) -> discord.Embed:
        colour = discord.Colour.random()
        platform = activity.platform
        if platform and platform.lower() == "youtube":
            colour = discord.Colour.from_str("#fe0000")
        elif platform and platform.lower() == "twitch":
            colour = discord.Colour.from_str("#9147ff")

        return discord.Embed(
            title=f"Streaming: {activity.name}",
            description=info_to_string(
                {
                    "Game": activity.game,
                    "Platform": platform,
                    "Twitch name": activity.twitch_name,
                    "URL": activity.url,
                }
            ),
            colour=colour,
        )

    @staticmethod
    async def create_generic_activity_embed(activity: discord.Activity) -> discord.Embed:
        embed = discord.Embed(
            title=f"Activity: {activity.name}",
            description=activity.details,
            colour=discord.Colour.random(seed=activity.name),
        ).set_thumbnail(url=activity.large_image_url)

        started_at = int(time.mktime(activity.start.timetuple())) if activity.start else None
        ends_at = int(time.mktime(activity.end.timetuple())) if activity.end else None
        duration = datetime.now(timezone.utc) - activity.start if activity.start else None
        embed.add_field(
            name=" ",
            value=info_to_string(
                {
                    "State": activity.state or None,
                    "Started at": f"<t:{started_at}> (<t:{started_at}:R>)" if started_at else None,
                    "Ends at": f"<t:{ends_at}> (<t:{ends_at}:R>)" if ends_at else None,
                    "Duration": readable_timedelta(duration) if duration else None,
                    "URL": activity.url,
                }
            ),
        )
        return embed

    @staticmethod
    async def get_member_activity_embeds(member: discord.Member, /) -> list[discord.Embed]:
        embeds: list[discord.Embed] = []
        for activity in member.activities:
            print(activity)
            if isinstance(activity, discord.Spotify):
                embeds.append(await WhoisHelper.create_spotify_embed(activity))
            elif isinstance(activity, discord.Game):
                embeds.append(await WhoisHelper.create_game_embed(activity))
            elif isinstance(activity, discord.Streaming):
                embeds.append(await WhoisHelper.create_stream_embed(activity))
            elif isinstance(activity, discord.Activity):
                embeds.append(await WhoisHelper.create_generic_activity_embed(activity))
            # TODO: support custom activities
            #  https://discordpy.readthedocs.io/en/latest/api.html#discord.CustomActivity

        return embeds
