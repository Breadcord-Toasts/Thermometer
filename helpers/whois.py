import time
from datetime import datetime, timezone

import aiohttp
import discord

from . import info_to_string, readable_timedelta


class WhoisHelper:
    def __init__(self):
        self.session: None | aiohttp.ClientSession = None

    async def open_session(self) -> None:
        self.session = aiohttp.ClientSession()

    async def close_session(self) -> None:
        await self.session.close()

    async def get_user_info(self, user: discord.User, /) -> dict:
        created_at = int(time.mktime(user.created_at.timetuple()))
        user_type = None
        if user.bot:
            user_type = "Bot"
        if user.system:
            user_type = "System"

        return {
            "Username": discord.utils.escape_markdown(user.name), # Escaped due to non-migrated users
            "Global display name": discord.utils.escape_markdown(user.global_name) if user.global_name else None,
            "Discriminator": user.discriminator if user.discriminator != "0" else None,
            "Mention": user.mention,
            "Nickname": discord.utils.escape_markdown(user.display_name) if user.display_name != user.name else None,
            "ID": user.id,
            # We clarify due to the new pronouns field im profiles, that for some reason can't be accessed by bots
            "Pronouns": f"{pronouns} (Fetched from [PronounDB](https://pronoundb.org/))"
            if (pronouns := await self.get_user_pronouns(user)) else None,
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
            description=info_to_string(
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
            description=info_to_string(
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

    @classmethod
    async def create_generic_activity_embed(cls, activity: discord.Activity) -> discord.Embed:
        embed = discord.Embed(
            title=f"Activity: {activity.name}",
            description=activity.details,
            colour=discord.Colour.random(),
        )

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
                # TODO: support custom activities
                #  https://discordpy.readthedocs.io/en/latest/api.html#discord.CustomActivity

        return embeds

    @classmethod
    def pronoun_from_code(cls, pronoun_short_code: str, /) -> str | None:
        pronoun_map = {
            "hh": "he/him",
            "hi": "he/it",
            "hs": "he/she",
            "ht": "he/they",
            "ih": "it/him",
            "ii": "it/its",
            "is": "it/she",
            "it": "it/they",
            "shh": "she/he",
            "sh": "she/her",
            "si": "she/it",
            "st": "she/they",
            "th": "they/he",
            "ti": "they/it",
            "ts": "they/she",
            "tt": "they/them",
            "any": "Any pronouns",
            "other": "Other pronouns",
            "ask": "Ask me my pronouns",
            "avoid": "Avoid pronouns, use my name",
            "unspecified": None,
        }
        return pronoun_map.get(pronoun_short_code)

    async def get_user_pronouns(self, user: discord.User | int, /) -> str | None:
        if not isinstance(user, int):
            user = user.id
        async with self.session.get(f"https://pronoundb.org/api/v1/lookup?platform=discord&id={user}") as response:
            if response.status != 200:
                return
            return self.pronoun_from_code((await response.json())["pronouns"])



