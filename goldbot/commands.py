import locale
import logging
import re

import discord
from discord.ext import commands

import settings
from settings.discord_guild_settings import GuildSettings
from transactions.alliances import list_all_alliance_names
from transactions.notes import add_player_note
from transactions.players import (
    search_player,
    get_player_by_id,
    get_player_by_discord_id,
    get_identity_by_gov_id
)
from .utils import has_attachment, enabled_by
from .utils import has_role

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

logger = logging.getLogger(__name__)


class Query(commands.Cog):
    def cog_check(self, ctx):
        channel = ctx.message.channel
        if channel.type == discord.ChannelType.private:
            return True
        if channel.type == discord.ChannelType.text:
            return channel.name in settings.get('LISTENING_CHANNELS')

    @commands.command("whois", help="look up member by name or id.")
    async def whois(self, ctx, *, name_or_id):
        player, names = search_player(name_or_id)
        if not player:
            if len(names) == 0:
                return await ctx.send(f"I don't recognize that name {name_or_id}.")
            if len(names) == 1:
                return await ctx.send(f"Did you mean {names[0]}?")
            if len(names) > 1:
                return await ctx.send(f"{', '.join(map(lambda x: f'`{x}`', names))} Who are you talking about?")
        notes_q = player.get_notes()
        notes = {
            f'note-{i}': f'{n.type.name} on {n.datetime_created.date().isoformat()} - {n.content}'
            for i, n in enumerate(notes_q.limit(5))
        }
        message = _format_message(
            ctx, gov_id=player.gov_id, name=player.current_name, alliance=player.alliance_name,
            **notes,
        )

        await ctx.send(message)
        if notes_q.count() > 5:
            await ctx.send('there are more than 5 notes on this player. Use `!listnote gov-id` to check all.')

    @commands.command('listnote', help="list all the notes of one player")
    async def list_note(self, ctx, name_or_id, type_name='', limit=20):
        player, names = search_player(name_or_id)
        if not player:
            if len(names) == 0:
                return await ctx.send(f"I don't recognize that name: {name_or_id}.")
            if len(names) == 1:
                return await ctx.send(f"Did you mean {names[0]}?")
            if len(names) > 1:
                return await ctx.send(f"{', '.join(map(lambda x: f'`{x}`', names))}. Who are you talking about?")

        notes = {
            f'note-{i}': f'{n.type.name} on {n.datetime_created.date().isoformat()} - {n.content}'
            for i, n in enumerate(player.get_notes(type_name.upper(), limit))
        }
        message = _format_message(ctx, gov_id=player.gov_id, name=player.current_name, **notes)
        await ctx.send(message)


class PMCommand(commands.Cog):
    async def cog_check(self, ctx):
        if await ctx.bot.is_owner(ctx.author):
            return True
        return ctx.guild is None

    @commands.command("linkme", help="link your game account to discord.")
    async def link_me(self, ctx, gov_id: int, *, name: str):
        # discord is not linked
        discord_id = ctx.message.author.id
        player = get_player_by_discord_id(discord_id)
        if player:
            return await ctx.send(f'You are already linked to gov_id: {player.gov_id}')

        # player is not linked
        if get_identity_by_gov_id(gov_id):
            return await ctx.send(f"The gov_id {gov_id} has been linked already")

        has_attachment(ctx)

        alliance_name = _get_alliance_name(ctx, discord_id)
        message = _format_message(ctx, gov_id=gov_id, name=name, alliance=alliance_name, discord_id=discord_id)

        await _reply_for_approval(ctx, message)

    @commands.command("mykill", help="submit the kill data")
    @enabled_by('DM_COMMAND_MY_KILL_ENABLED')
    async def my_kill(self, ctx, t4: int, t5: int, death: int, gov_id: int = None):
        # find player either by linkage or provided gov id
        player = get_player_by_id(gov_id) if gov_id else _get_player_by_ctx(ctx)

        has_attachment(ctx)

        message = _format_message(ctx, gov_id=player.gov_id, name=player.current_name, t4=t4, t5=t5, death=death)

        await _reply_for_approval(ctx, message)

    @commands.command("myhonor", help="submit the honor data")
    @enabled_by('DM_COMMAND_MY_HONOR_ENABLED')
    async def my_honor(self, ctx, honor: int, gov_id: int = None):
        # find player either by linkage or provided gov id
        player = get_player_by_id(gov_id) if gov_id else _get_player_by_ctx(ctx)

        has_attachment(ctx)

        message = _format_message(ctx, gov_id=player.gov_id, name=player.current_name, honor=honor)

        await _reply_for_approval(ctx, message)

    @commands.command("myscore", help="submit the pre-kvk score")
    @enabled_by('DM_COMMAND_MY_SCORE_ENABLED')
    async def my_score(self, ctx, stage: int, score: int, gov_id: int = None):
        # find player either by linkage or provided gov id
        player = get_player_by_id(gov_id) if gov_id else _get_player_by_ctx(ctx)

        # validate stage
        if stage not in (1, 2, 3):
            return await ctx.send(f'stage expected to be 1,2,3')

        has_attachment(ctx)

        message = _format_message(ctx, gov_id=player.gov_id, name=player.current_name, stage=stage, score=score)

        await _reply_for_approval(ctx, message)

    @commands.command("myinfo", help="check your info.")
    async def my_info(self, ctx):
        player = _get_player_by_ctx(ctx)
        message = _format_message(
            ctx, gov_id=player.gov_id, name=player.current_name, alliance=player.alliance.name, tag_author=False)
        records = {r.type: r.value for r in player.get_recent_records()}
        if records:
            message += f"Your previous submission:" + _format_message(ctx, tag_author=False, **records)
        return await ctx.send(message)

    @commands.command("mynewname", help="rename your in-game name.")
    async def my_new_name(self, ctx, *, newname):
        player = _get_player_by_ctx(ctx)
        message = _format_message(ctx, gov_id=player.gov_id, oldname=player.current_name, newname=newname)
        await _reply_for_approval(ctx, message)


class OfficerOnly(commands.Cog):
    async def cog_check(self, ctx):
        if ctx.message.channel.type == discord.ChannelType.text:
            guild_setting = GuildSettings.get(id=ctx.guild.id)
            if discord.utils.get(ctx.author.roles, id=guild_setting.officer_role_id):
                return True
            else:
                await ctx.send("You don't have officer role to use this command.")
                return False
        if ctx.message.channel.type == discord.ChannelType.private:
            await ctx.send("Command can not be used in private channel")
            return False

    @commands.command('add', help="add a new player with id and name")
    async def add(self, ctx, gov_id: int, *, name: str):
        if get_player_by_id(gov_id):
            return await ctx.send(f'{gov_id=} exists already')
        # not tag for add command for non-forwarding message
        message = _format_message(ctx, gov_id=gov_id, name=name, tag_author=False)

        await _reply_for_approval(ctx, message)

    @commands.command("link", help="link player to discord account.")
    async def link(self, ctx, mention, gov_id: int, *, name: str = ''):
        if not re.match("<@!\d+>", mention):
            return await ctx.send(f"please @ the user to link to: `!link @username {gov_id} {name}`")
        else:
            discord_id = int(mention[3:-1])

        name = name or getattr(get_player_by_id(gov_id), 'current_name', None)
        if not name:
            return await ctx.send(f"Please provide in-game name as well: `!link @usename {gov_id} <player_name>`")

        alliance_name = _get_alliance_name(ctx, discord_id)
        # not tag for add command for non-forwarding message
        message = _format_message(
            ctx, gov_id=gov_id, name=name, alliance=alliance_name, discord_id=discord_id, tag_author=False)

        await _reply_for_approval(ctx, message)

        # Hint
        if get_identity_by_gov_id(gov_id):
            await ctx.send(f"**{gov_id=} has been linked already**")

    @commands.command("rename", help="update player in-game name.")
    async def rename(self, ctx, gov_id, *, name):
        player = get_player_by_id(gov_id)
        if not player:
            return await ctx.send(f'{gov_id=} does not exist')
        if player.current_name == name:
            return await ctx.send(f'new name is same as old name.')

        # not tag for add command for non-forwarding message
        message = _format_message(ctx, gov_id=gov_id, oldname=gov_id.current_name, newname=name, tag_author=False)
        await _reply_for_approval(ctx, message)

    @commands.command('note', help='add note to player')
    async def note(self, ctx, gov_id, note_type, *, note):
        player = get_player_by_id(gov_id)
        if not player:
            return await ctx.send(f"Error: {gov_id=} does not exist.")
        add_player_note(gov_id, note_type, note)
        await ctx.message.add_reaction(settings.get('SUCCEED_EMOJI'))


class Admin(commands.Cog):
    async def cog_check(self, ctx):
        return await ctx.bot.is_owner(ctx.author)

    @commands.command("eval", help="eval")
    async def eval(self, ctx, *, arg):
        try:
            await ctx.send(str(eval(arg)))
        except Exception as e:
            await ctx.send(str(e))

    @commands.command("exec", help="exec")
    async def exec(self, ctx, *, arg):
        try:
            exec(arg)
        except Exception as e:
            await ctx.send(str(e))


def _format_message(ctx, tag_author=True, append_attachment=True, **kwargs):
    lines_to_send = []
    if tag_author:
        lines_to_send += [ctx.message.author.mention]

    arguments = [('command', ctx.command.name)]
    arguments += kwargs.items()

    lines_to_send += ['```']
    lines_to_send += [f'{k}: {v}' for k, v in arguments]
    lines_to_send += ['```']

    if append_attachment and ctx.message.attachments:
        lines_to_send.append(ctx.message.attachments[0].url)

    return '\n'.join(lines_to_send)


def _get_alliance_name(ctx, discord_id):
    guild = discord.utils.get(ctx.bot.guilds, id=GuildSettings.get(name='kingdom').id)
    for n in list_all_alliance_names():
        if has_role(guild, n, discord_id):
            return n
    else:
        return 'unknown'


def _get_player_by_ctx(ctx):
    player = get_player_by_discord_id(ctx.message.author.id)
    if player:
        return player

    raise commands.errors.BadArgument(
        "Your game id is not linked to with your discord, Hint: use `!linkme`")


async def _reply_for_approval(ctx, reply_message):
    reply = await ctx.message.reply(reply_message)
    await reply.add_reaction(settings.get("APPROVAL_EMOJI"))
    await reply.add_reaction(settings.get("DECLINED_EMOJI"))
    await ctx.send('Please react on message to approve or cancel your request')
