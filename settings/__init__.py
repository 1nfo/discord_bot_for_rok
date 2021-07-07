_UNDEFINED = object()


def get(name, default=_UNDEFINED):
    import os
    if name in globals():
        return globals()[name]

    env_name = 'BOT_' + name
    if env_name in os.environ:
        return os.environ[env_name]

    if default is not _UNDEFINED:
        return default

    raise ValueError(f"Unknown setting {name}")


from .constants import *  # noqa
from .discord_guild_settings import GuildSettings as GUILD_SETTINGS  # noqa
