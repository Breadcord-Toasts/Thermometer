from datetime import timedelta, datetime
from io import BytesIO
from typing import Any, overload

import discord


def info_to_string(info: dict[Any, Any]) -> str:
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


@overload
def max_size(asset: discord.Asset) -> discord.Asset:
    ...
@overload
def max_size(asset: None) -> None:
    ...
def max_size(asset: discord.Asset | None) -> discord.Asset | None:
    if asset is None:
        return None
    return asset.with_size(4096).with_static_format("png")


# noinspection PyShadowingBuiltins
def convert_bytes(bytes: int) -> tuple[float, str]:
    step_size = 1024
    working: int | float = bytes
    for x in ["Bytes", "KB", "MB", "GB"]:
        if working < step_size:
            return working, x
        working /= step_size
    return working, "TB"


def build_info_embed(
    info: dict[str, Any | None],
    /,
    *,
    title: str,
    colour: discord.Colour | discord.Color | None = None,
    thumbnail: str | None = None,
    image: str | None = None,
    inline_fields: bool = True
) -> discord.Embed:
    embed = discord.Embed(title=title, colour=colour, timestamp=datetime.now())
    embed.set_thumbnail(url=thumbnail)
    embed.set_image(url=image)

    embed.description = ""
    for key, value in info.items():
        if isinstance(value, dict):
            embed.add_field(name=key, value=info_to_string(value), inline=inline_fields)
            continue
        embed.description += info_to_string({key: value})
    return embed


async def fetch_asset(asset: discord.Asset | None, filename: str | None) -> discord.File | None:
    """
    More fail-safe reimplementation of discord.Asset.to_file().

    :param asset: Asset to convert to a file
    :param filename: Filename to use for the file. If none is provided it will be set to the asset key.
    :return: discord.File object or None if the asset could not be fetched.
    """
    if asset is None:
        return None
    try:
        data = await asset.read()
    except discord.NotFound:  # There are cases where an asset points to a 404 page
        return None
    else:
        file = discord.File(fp=BytesIO(data), filename=asset.key)
        if filename:
            file.filename = f"{filename}.gif" if asset.is_animated() else f"{filename}.png"
        return file
