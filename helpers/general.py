from datetime import timedelta

import discord


class GeneralHelper:
    @classmethod
    async def info_to_string(cls, info: dict) -> str:
        return "".join(f"**{key}:** {value}\n" for key, value in info.items() if value is not None)

    @classmethod
    def readable_timedelta(cls, duration: timedelta) -> str:
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

    @classmethod
    def enhance_asset_image(cls, asset: discord.Asset) -> discord.Asset:
        return asset.with_size(4096).with_static_format("png")
