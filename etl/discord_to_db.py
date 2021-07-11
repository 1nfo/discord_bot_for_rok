import time
from collections import defaultdict

import discord

from etl import etl_job
from functools import partial

stats = None


@etl_job
async def refresh_alliance_name_and_check_unlinked_identity(ctx):
    from settings.discord_guild_settings import GuildSettings
    from transactions import players
    from goldbot.utils import get_alliance_name

    guild_setting = GuildSettings.get(name='kingdom')
    guild = discord.utils.get(ctx.bot.guilds, id=guild_setting.id)

    members = guild.members
    message = await ctx.send(f'progress: 0/{len(members)}')
    global stats
    stats = defaultdict(partial(defaultdict, list))
    count = defaultdict(int)
    t = time.time()
    for i, member in enumerate(members):
        player = players.get_player_by_discord_id(member.id)
        alliance_name = get_alliance_name(guild, member.id)
        if player:
            if player.alliance_name != alliance_name:
                stats['alliance_updated'][alliance_name].append(f'`{member.name}`')
                count['alliance_updated'] += 1
            count['linked'] += 1
        else:
            stats['not_linked'][alliance_name].append(f'`{member.name}`')
            count['not_linked'] += 1

        if time.time() - t > 1 or i + 1 == len(members):
            t = time.time()
            await message.edit(content=f'progress: {i + 1}/{len(members)}')
    await ctx.send(f'{count}')


@etl_job
async def report_last_run(ctx):
    global stats
    if stats is None:
        return await ctx.send('No previous result.')
    for category, m in stats.items():
        for alliance, names in m.items():
            for i in range(0, len(names), 100):
                await ctx.send(f'{category}-{alliance}: {names[i: i + 20]}')
