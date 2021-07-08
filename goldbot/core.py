import logging
import sys

from discord import Intents
from discord.ext import commands

import settings

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    pass


class GoldBot(commands.Bot):
    @staticmethod
    async def on_ready():
        logger.info(f'{bot.user} has connected to Discord.')

    async def on_message(self, message):
        logger.debug(f'{message=}')
        return await super(GoldBot, self).on_message(message)

    async def on_error(self, event, *args, **kwargs):
        exc_cls, exc, _ = sys.exc_info()
        if exc_cls is ValidationError:
            message = args[0]
            return await message.author.send("```{}```".format('\n'.join(exc.args)))
        else:
            logger.exception(f'{event} - {exc}')

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f'{error}')
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'{error}')
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f'{error}')
        elif isinstance(error, commands.CheckFailure):
            logger.debug(f'{ctx=}, {error=}')
        else:
            logger.exception(f'{ctx=}, {error=}')
            await ctx.send(f'{error=}')


intents = Intents.default()
intents.members = True
intents.guilds = True
intents.reactions = True

bot = GoldBot(
    command_prefix=settings.get("COMMAND_PREFIX"),
    description="GoldStone's bot",
    intents=intents,
)
