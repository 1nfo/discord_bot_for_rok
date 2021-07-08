import locale
import logging

import discord

import settings
from goldbot.features import forward_submission
from settings.discord_guild_settings import GuildSettings
from .core import bot
from .features import approve_submission, decline_submission
from .utils import has_role

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

logger = logging.getLogger(__name__)


@bot.event
async def on_raw_reaction_add(payload):
    # ignore recursive reaction
    if payload.user_id == bot.user.id:
        return

    # ignore reaction on non bot's message
    channel = await bot.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    if message.author != bot.user:
        return

    # ignore reacted message already
    if discord.utils.get(message.reactions, emoji=settings.get("SUCCEED_EMOJI")):
        return
    if discord.utils.get(message.reactions, emoji=settings.get("FAILURE_EMOJI")):
        return

    # forward submission
    if channel.type == discord.ChannelType.private:
        return await forward_submission.execute(message, payload.emoji.name, bot.guilds)

    if payload.guild_id:
        guild_settings = GuildSettings.get(id=payload.guild_id)
        if not guild_settings:
            return

        guild = discord.utils.get(bot.guilds, id=payload.guild_id)
        if not has_role(guild, guild_settings.approver_role_id, payload.member.id):
            return

        if payload.emoji.name == settings.get("APPROVAL_EMOJI"):
            return await approve_submission.execute(message, payload)
        if payload.emoji.name == settings.get("DECLINED_EMOJI"):
            return await decline_submission.execute(message, payload)
