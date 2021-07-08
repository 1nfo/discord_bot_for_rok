import discord

import settings
from goldbot.utils import convert_to_dict
from settings.discord_guild_settings import GuildSettings
from transactions.players import update_name


async def execute(message, reaction_name, guilds):
    if reaction_name == settings.get("DECLINED_EMOJI"):
        return await message.add_reaction(settings.get("FAILURE_EMOJI"))

    if reaction_name == settings.get("APPROVAL_EMOJI"):
        lines = message.content.split('```')[1].strip().split('\n')
        args = convert_to_dict(lines)
        command = args.pop('command', None)
        if command in ('mynewname',):
            await _self_service(message, command, args)
        else:
            await _forward(message, guilds, command)

        return await message.add_reaction(settings.get("SUCCEED_EMOJI"))


async def _forward(message, guilds, command):
    guild_settings = GuildSettings.get(name='kingdom')
    guild = discord.utils.get(guilds, id=guild_settings.id)
    channel = discord.utils.get(guild.channels, id=guild_settings.channels[command])

    forwarded = await channel.send(message.content)
    await forwarded.add_reaction(settings.get('APPROVAL_EMOJI'))
    await forwarded.add_reaction(settings.get('DECLINED_EMOJI'))
    if message.mentions:
        await message.mentions[0].send(f"Sent your screen shot {channel.name}, please wait for officer to verify.")


async def _self_service(message, command, args):
    if command == 'mynewname':
        update_name(gov_id=args['gov_id'], name=args['newname'])
        if message.mentions:
            await message.mentions[0].send("Your name has change. type `!myinfo` to confirm")
