import logging
import os
import sys

import settings
from goldbot.commands import Informative, OfficerOnly, Admin, Submission
from goldbot.core import bot

file_handler = logging.FileHandler(filename=f'{os.getenv("HOME")}/app.log')
stdout_handler = logging.StreamHandler(sys.stdout)

logging.basicConfig(
    level=settings.get('LOG_LEVEL'),
    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    handlers=[file_handler, stdout_handler]
)

bot.add_cog(Admin())
bot.add_cog(Informative())
bot.add_cog(OfficerOnly())
bot.add_cog(Submission())

if __name__ == "__main__":
    bot.run(settings.get("DISCORD_TOKEN"))
