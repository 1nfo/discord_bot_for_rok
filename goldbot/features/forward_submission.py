import discord

import settings
from settings.discord_guild_settings import GuildSettings


async def execute(message, payload, guilds, reaction_channel):
    if payload.emoji.name == settings.get("DECLINED_EMOJI"):
        return await message.add_reaction(settings.get("FAILURE_EMOJI"))

    if payload.emoji.name == settings.get("APPROVAL_EMOJI"):
        guild_settings = GuildSettings.get(name='test')
        guild = discord.utils.get(guilds, id=guild_settings.id)
        channel_id = guild_settings.kill_channel_id
        channel = discord.utils.get(guild.channels, id=channel_id)
        forwarded = await channel.send(message.content)
        await forwarded.add_reaction(settings.get('APPROVAL_EMOJI'))
        await forwarded.add_reaction(settings.get('DECLINED_EMOJI'))
        await message.add_reaction(settings.get("SUCCEED_EMOJI"))
        await reaction_channel.send(f"Sent your screen shot {channel.name}, please wait for officer to verify.")
        return
