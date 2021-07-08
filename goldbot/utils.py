from functools import wraps

import discord
from discord.ext.commands import errors

import settings


def has_role(guild, role_id, user_id):
    if not guild:
        return False

    member = guild.get_member(user_id)
    if not member:
        return False

    return bool(discord.utils.get(member.roles, id=role_id))


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
        k, v = line.split(':', maxsplit=2)
        args[k.strip()] = v.strip()
    return args
