from functools import wraps

import discord
from discord.ext import commands
from discord.ext.commands import errors
from fuzzywuzzy import process

import settings
from settings.discord_guild_settings import GuildSettings


def fuzzy_match(name, chooses):
    result = process.extractOne(name, chooses, score_cutoff=60)
    return result and result[0]


def has_role(guild, role_id, user_id):
    if not guild:
        return False

    member = guild.get_member(user_id)
    if not member:
        return False

    return bool(discord.utils.get(member.roles, id=role_id))


def any_channels(channel_names, dm_allowed=True):
    def predicate(ctx):
        channel = ctx.message.channel
        if channel.type == discord.ChannelType.private:
            return dm_allowed
        if channel.type == discord.ChannelType.text:
            return channel.name in channel_names

    return predicate


@commands.check
def limit_command_to_pm_or_bot_channel(ctx):
    channel = ctx.message.channel
    if channel.type == discord.ChannelType.private:
        return True
    if channel.type == discord.ChannelType.text:
        return channel.name in settings.get('LISTENING_CHANNELS')


@commands.check
def officer_only(ctx):
    if isinstance(ctx.channel, discord.abc.GuildChannel):
        guild_setting = GuildSettings.get(id=ctx.guild.id)
        if not discord.utils.get(ctx.author.roles, id=guild_setting.officer_role_id):
            return False
    return True


def has_attachment(ctx):
    if not ctx.message.attachments:
        raise errors.BadArgument("Please attach screen shot along with your data.")


def enabled_by(setting_name):
    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            if not settings.get(setting_name):
                raise errors.BadArgument(f"Command `{f.__name__}` is disabled now.")

            return await f(*args, **kwargs)

        return wrapper

    return decorator


def convert_to_dict(lines):
    args = {}
    for line in lines:
        k, v = line.split(':', maxsplit=2)
        args[k.strip()] = v.strip()
    return args


def parse_to_dict(*keys):
    keys = set(keys)

    def wrapper(string):
        try:
            ret = convert_to_dict(string.split())
        except Exception as e:
            raise errors.BadArgument(*e.args)

        for k in keys:
            if k not in ret:
                raise errors.BadArgument(f"Missing arguments: {k}")
            if not ret[k]:
                raise errors.BadArgument(f"Empty arguments: {k}")

        return ret

    return wrapper
