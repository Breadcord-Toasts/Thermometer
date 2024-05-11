from datetime import timedelta, datetime

import discord


def info_to_string(info: dict) -> str:
    return "".join(f"**{key}:** {value}\n" for key, value in info.items() if value is not None)


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


def enhance_asset_image(asset: discord.Asset) -> discord.Asset:
    return asset.with_size(4096).with_static_format("png")


# noinspection PyShadowingBuiltins
def convert_bytes(bytes: int) -> tuple[float, str]:
    step_size = 1000
    for x in ["Bytes", "KB", "MB", "GB"]:
        if bytes < step_size:
            return bytes, x
        bytes /= step_size


def build_info_embed(
    info: dict,
    /,
    *,
    title: str,
    colour: discord.Colour | discord.Color | None = None,
    thumbnail: str | None = None,
    image: str | None = None,
    inline_fields: bool = True
) -> discord.Embed:
    embed = discord.Embed(title=title, description="", colour=colour, timestamp=datetime.now())
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    if image:
        embed.set_image(url=image)

    for key, value in info.items():
        if isinstance(value, dict):
            embed.add_field(name=key, value=info_to_string(value), inline=inline_fields)
            continue
        embed.description += info_to_string({key: value})
    return embed

