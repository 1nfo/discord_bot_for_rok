import locale
import logging

import discord
from discord.ext import commands

import settings
from models import Player, IdentityLinkage, Identity
from settings.discord_guild_settings import GuildSettings
from transactions.alliances import list_all_alliance_names, get_alliance
from transactions.notes import add_player_note
from transactions.players import create_new_player, update_name, search_player, get_player
from .utils import has_attachment, enabled_by

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

logger = logging.getLogger(__name__)


class Informative(commands.Cog):
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

    @commands.command("myinfo", help="check your info.")
    async def my_info(self, ctx):
        player = _get_player_by_ctx(ctx)
        if not player:
            await ctx.send(
                f'{ctx.message.author.mention} your has no rok account linked to discord. Hint: use `!linkme`')

        message = _format_message(ctx, gov_id=player.gov_id, name=player.current_name, alliance=player.alliance.name)
        return await ctx.send(message)


class Submission(commands.Cog):
    async def cog_check(self, ctx):
        if await ctx.bot.is_owner(ctx.author):
            return True
        return ctx.guild is None

    @commands.command("mynewname", help="rename your in-game name.")
    async def my_new_name(self, ctx, *, newname):
        player = _get_player_by_ctx(ctx, default_to_none=False)
        message = _format_message(ctx, gov_id=player.gov_id, oldname=player.current_name, newname=newname)
        reply = await ctx.message.reply(message)
        await reply.add_reaction(settings.get("APPROVAL_EMOJI"))
        await reply.add_reaction(settings.get("DECLINED_EMOJI"))
        await ctx.send('Please react on message to complete or cancel your rename')

    @commands.command("mykill", help="submit the kill data")
    @enabled_by('DM_COMMAND_MY_KILL_ENABLED')
    async def my_kill(self, ctx, t4, t5, death, gov_id=None):
        player = get_player(gov_id) if gov_id else _get_player_by_ctx(ctx, default_to_none=False)
        has_attachment(ctx)
        message = _format_message(ctx, gov_id=player.gov_id, name=player.current_name, t4=t4, t5=t5, death=death)
        reply = await ctx.message.reply(message)
        await reply.add_reaction(settings.get("APPROVAL_EMOJI"))
        await reply.add_reaction(settings.get("DECLINED_EMOJI"))
        await ctx.send('Please react on message to approve or cancel your request')

    @commands.command("myhonor", help="submit the honor data")
    @enabled_by('DM_COMMAND_MY_HONOR_ENABLED')
    async def my_honor(self, ctx, honor, gov_id=None):
        player = get_player(gov_id) if gov_id else _get_player_by_ctx(ctx, default_to_none=False)
        has_attachment(ctx)
        message = _format_message(ctx, gov_id=player.gov_id, name=player.current_name, honor=honor)
        reply = await ctx.message.reply(message)
        await reply.add_reaction(settings.get("APPROVAL_EMOJI"))
        await reply.add_reaction(settings.get("DECLINED_EMOJI"))
        await ctx.send('Please react on message to approve or cancel your request')

    @commands.command("myscore", help="submit the pre-kvk score")
    @enabled_by('DM_COMMAND_MY_SCORE_ENABLED')
    async def my_score(self, ctx, *, stage, score, gov_id=None):
        player = get_player(gov_id) if gov_id else _get_player_by_ctx(ctx, default_to_none=False)
        has_attachment(ctx)
        message = _format_message(ctx, gov_id=player.gov_id, name=player.name, stage=stage, score=score)
        reply = await ctx.message.reply(message)
        await reply.add_reaction(settings.get("APPROVAL_EMOJI"))
        await reply.add_reaction(settings.get("DECLINED_EMOJI"))
        await ctx.send('Please react on message to approve or cancel your request')

    @commands.command("linkme", help="link your game account to discord.")
    async def link_me(self, ctx, gov_id, name, alliance_name=None):
        player = _get_player_by_ctx(ctx)
        if player:
            return await ctx.send(f'You are already linked to gov_id: {player.gov_id}')

        player = Player.get_or_none(gov_id=gov_id)
        if player and IdentityLinkage.filter(player=player).exists():
            return await ctx.send(f"The gov_id {gov_id} has been linked already")

        if alliance_name is None:
            for n in list_all_alliance_names():
                if discord.utils.get(ctx.author.roles, name=n):
                    alliance_name = n
                    break
            else:
                return await ctx.send(f"alliance_name is a required argument that is missing.")

        if not get_alliance(alliance_name):
            alliance_names = list_all_alliance_names()
            return await ctx.send(f"{alliance=} not found. Use one of them {alliance_names}")

        has_attachment(ctx)
        message = _format_message(ctx, gov_id=gov_id, name=name, alliance=alliance_name)
        reply = await ctx.message.reply(message)
        await reply.add_reaction(settings.get("APPROVAL_EMOJI"))
        await reply.add_reaction(settings.get("DECLINED_EMOJI"))


class OfficerOnly(commands.Cog):
    async def cog_check(self, ctx):
        if await ctx.bot.is_owner(ctx.author):
            return True
        if ctx.channel == discord.ChannelType.text:
            guild_setting = GuildSettings.get(id=ctx.guild.id)
            return discord.utils.get(ctx.author.roles, id=guild_setting.officer_role_id)

    @commands.command("add", help="add new player")
    async def add(self, ctx, gov_id: int, *, name: str):
        player = get_player(gov_id)
        if player:
            return await ctx.send(f"Error: {gov_id=} already exists.")
        create_new_player(gov_id, name)
        await ctx.message.add_reaction(settings.get('SUCCEED_EMOJI'))

    @commands.command('note', help='add note to player')
    async def note(self, ctx, gov_id, note_type, *, note):
        player = get_player(gov_id)
        if not player:
            return await ctx.send(f"Error: {gov_id=} does not exist.")
        add_player_note(gov_id, note_type, note)
        await ctx.message.add_reaction(settings.get('SUCCEED_EMOJI'))

    @commands.command("rename", help="rename in-game name.")
    async def rename(self, ctx, gov_id, *, name):
        player = Player.get_or_none(gov_id=gov_id)
        if not player:
            return await ctx.send(f'{gov_id=} does not exist. `!introduce f{gov_id} f{name}')
        update_name(player, name)
        await ctx.message.add_reaction(settings.get('SUCCEED_EMOJI'))


class Admin(commands.Cog):
    async def cog_check(self, ctx):
        return await ctx.bot.is_owner(ctx.author)

    @commands.command("etl", help="run ETL from google sheet")
    async def etl(self, ctx):
        from etl.sheet_to_db import JOBS
        await ctx.send('starting ETL')
        for j in JOBS:
            await ctx.send(f'running {j.__name__}')
            result = j()
            await ctx.send(f'{result}')
        await ctx.send('finished ETL')

    @commands.command("test", help="test")
    async def test(self, ctx, *, arg):
        try:
            await ctx.send(str(eval(arg)))
        except Exception as e:
            await ctx.send(str(e))


def _format_message(ctx, append_attachment=True, **kwargs):
    lines_to_send = [ctx.message.author.mention]

    arguments = [('command', ctx.command.name)]
    arguments += kwargs.items()

    lines_to_send += ['```']
    lines_to_send += [f'{k}: {v}' for k, v in arguments]
    lines_to_send += ['```']

    if append_attachment and ctx.message.attachments:
        lines_to_send.append(ctx.message.attachments[0].url)

    return '\n'.join(lines_to_send)


def _get_player_by_ctx(ctx, default_to_none=True):
    identity = Identity.get_or_none(external_id=ctx.message.author.id)
    q = IdentityLinkage.filter(identity=identity)
    if identity and q.exists():
        return q.order_by(IdentityLinkage.id.desc()).first().player
    if not default_to_none:
        raise commands.errors.BadArgument(
            "Your game id is not linked to with your discord, Hint: use `!linkme`")
