import time

import discord

from .general import GeneralHelper


class GuildInfoHelper:
    @staticmethod
    async def get_guild_info(guild: discord.Guild, /) -> dict:
        created_at = round(time.mktime(guild.created_at.timetuple()))
        nsfw_level = guild.nsfw_level.name.title() if guild.nsfw_level != discord.NSFWLevel.default else None
        filesize_limit, filesize_unit = GeneralHelper.convert_bytes(guild.filesize_limit)
        bot_count = len([member for member in guild.members if member.bot])
        human_count = guild.member_count - bot_count

        # noinspection PyUnresolvedReferences
        return {
            "Name": guild.name,
            "ID": guild.id,
            "Descriptions": guild.description,
            "Created at": f"<t:{created_at}> (<t:{created_at}:R>)",
            "Owner": f"{guild.owner.mention} ({guild.owner_id})" if guild.owner else None,
            "Preferred locale ": guild.preferred_locale.value,
            "Vanity URL": guild.vanity_url,
            "Vanity URL code": guild.vanity_url_code,
            "Splash URL": guild.splash.url if guild.splash else None,
            "Discovery splash URL": guild.discovery_splash.url if guild.splash else None,
            "NSFW level": nsfw_level,
            "Requires MFA": bool(guild.mfa_level.value),
            "Verification level": guild.verification_level.name.title(),
            "Default notifications": guild.default_notifications.name.replace("_", " ").title(),
            "Content filter level": guild.explicit_content_filter.name.replace("_", " ").title(),
            "Features": ", ".join(f"`{feature}`" for feature in sorted(guild.features)),
            "Channels": {
                "Channels": len(guild.channels) - len(guild.categories),
                "Text channels": len(guild.text_channels),
                "Voice channels": len(guild.voice_channels),
                "Stage channels": f"{len(guild.stage_channels)} ({len(guild.stage_instances)} active)",
                "Forum channels": len(guild.forums),
                "Categories": len(guild.categories),
                "Threads": len(guild.threads),
                "Rules channel": guild.rules_channel.mention if guild.rules_channel else None,
                "AFK channel": f"{guild.afk_channel.mention} ({guild.afk_timeout} second timeout)"
                if guild.afk_channel
                else None,
            },
            "Stats": {
                "Members": f"{guild.member_count}/{guild.max_members}",
                "Bots": bot_count,
                "Humans": human_count,
                "Bot/human ratio": f"{round(bot_count/human_count, 3)} bots per human",
                "Roles": len(guild.roles),
                "Emojis": f"{len(guild.emojis)}/{guild.emoji_limit}",
                "Stickers": f"{len(guild.stickers)}/{guild.sticker_limit}",
                "Filesize limit": f"{round(filesize_limit)} {filesize_unit}",
                "Bitrate limit": guild.bitrate_limit,
            },
            "Boosts": {
                "Boost level": f"{guild.premium_tier} ({guild.premium_subscription_count} boosts)",
                "Nitro booster role": guild.premium_subscriber_role.mention if guild.premium_subscriber_role else None,
            },
        }