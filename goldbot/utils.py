import logging
from functools import wraps

import discord
from discord.ext.commands import errors

import settings


def number(s):
    return int(s.replace(',', ''))


def has_role(guild, role, user_id):
    if not guild:
        return False

    member = guild.get_member(int(user_id))
    if not member:
        return False

    if isinstance(role, int):
        return bool(discord.utils.get(member.roles, id=role))
    else:
        return bool(discord.utils.get(member.roles, name=role))


def has_attachment(ctx):
    if not ctx.message.attachments:
        raise errors.BadArgument("Please attach screen shot along with your data.")


def enabled_by(setting_name):
    def decorator(f):
        @wraps(f)
        async def wrapper(self, ctx, *args, **kwargs):
            if not settings.get(setting_name):
                raise errors.BadArgument(f"Command `{ctx.command.name}` is disabled now.")

            return await f(self, ctx, *args, **kwargs)

        return wrapper

    return decorator


def convert_to_dict(lines):
    args = {}
    for line in lines:
        k, v = line.split(':', maxsplit=1)
        args[k.strip()] = v.strip()
    return args


def get_alliance_name(guild, discord_id):
    from transactions.alliances import list_all_alliance_names
    for n in list_all_alliance_names():
        if has_role(guild, n, discord_id):
            return n
    else:
        return 'unknown'


def no_raise(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception:
            logging.exception(f'ignore error for {f.__name__}')

    return wrapper
