import discord

from etl import etl_job


@etl_job
def refresh_alliance_of_all_players(ctx):
    from settings.discord_guild_settings import GuildSettings
    from transactions import players
    from goldbot.utils import get_alliance_name

    guild_setting = GuildSettings.get(name='kingdom')
    guild = discord.utils.get(ctx.bot.guilds, id=guild_setting.id)

    for member in guild.get_member():
        player = players.get_player_by_discord_id(member.id)

        if player:
            alliance_name = get_alliance_name(guild, member.id)
            if player.alliance_name != alliance_name:
                await ctx.send(f"{player.gov_id} {player.current_name} | {player.alliance_name} -> {alliance_name}")
        else:
            await ctx.send(f'user `{member.name}` is not linked')
