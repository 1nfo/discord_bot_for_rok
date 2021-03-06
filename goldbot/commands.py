import locale
import logging

import discord
from discord.ext import commands

import settings
from etl.db_to_sheet import dump_records_to_sheet
from settings.discord_guild_settings import GuildSettings
from transactions import events
from transactions.alliances import update_alliance
from transactions.notes import add_player_note
from transactions.players import (
    search_player,
    get_player_by_id,
    get_player_by_discord_id,
    get_identity_by_gov_id,
    get_linkages_by_discord_id,
)
from .utils import has_attachment, enabled_by, number, get_alliance_name, no_raise, discord_mention

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

logger = logging.getLogger(__name__)


class Query(commands.Cog):
    @commands.command("myinfo", help="check your info.")
    async def my_info(self, ctx, discord_id: discord_mention = None):
        discord_id = discord_id or ctx.message.author.id
        _refresh_alliance(_get_player_by_ctx(ctx, discord_id), ctx, discord_id)
        for linkage in get_linkages_by_discord_id(discord_id):
            records = {r.type: r.value for r in linkage.player.get_recent_records()}
            message = f"Your {linkage.type.name} account:" + _format_message(
                ctx, tag_author=False, show_command=False,
                gov_id=linkage.player.gov_id, name=linkage.player.current_name, alliance=linkage.player.alliance.name,
                **records
            )
            await ctx.send(message)

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

        if identity := get_identity_by_gov_id(player.gov_id):
            _refresh_alliance(player, ctx, identity.discord_id)
            member = _get_discord_member(ctx, identity.discord_id)
            identity = member and member.name

        notes_q = player.get_notes()
        notes = {
            f'note-{i:02}': f'{n.type.name} on {n.datetime_created.date().isoformat()} - {n.content}'
            for i, n in enumerate(notes_q.limit(5))
        }
        message = _format_message(
            ctx, gov_id=player.gov_id, name=player.current_name, alliance=player.alliance_name,
            linked_to=identity,
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
    async def link_me(self, ctx, gov_id: number, *, name: str = ''):
        # discord is not linked
        discord_id = ctx.message.author.id

        if player := get_player_by_discord_id(discord_id):
            return await ctx.send(f'You are already linked to gov_id: {player.gov_id}')

        # player is not linked
        if get_identity_by_gov_id(gov_id):
            return await ctx.send(f"The gov_id {gov_id} has been linked already")

        name = name or _get_player_by_id(gov_id).current_name
        if not name:
            return await ctx.send(f"Please provide in-game name as well: `!link @usename {gov_id} <player_name>`")

        has_attachment(ctx)
        guild = discord.utils.get(ctx.bot.guilds, id=GuildSettings.get(name='kingdom').id)
        alliance_name = get_alliance_name(guild, discord_id)
        message = _format_message(ctx, gov_id=gov_id, name=name, alliance=alliance_name, discord_id=discord_id)

        await _reply_for_approval(ctx, message)

    @commands.command("mykill", help="submit the kill data")
    @enabled_by('DM_COMMAND_MY_KILL_ENABLED')
    async def my_kill(self, ctx, t4: number, t5: number, death: number, gov_id: number = None):
        # find player either by linkage or provided gov id
        player = _get_player_by_id(gov_id) if gov_id else _get_player_by_ctx(ctx)

        has_attachment(ctx)

        message = _format_message(
            ctx, gov_id=player.gov_id, name=player.current_name,
            t4=f'{t4:,}', t5=f'{t5:,}', death=f'{death:,}'
        )

        await _reply_for_approval(ctx, message)

    @commands.command("mydeath", help="submit the death data")
    @enabled_by('DM_COMMAND_MY_DEATH_ENABLED')
    async def my_death(
            self, ctx,
            t5_cav: number, t5_inf: number, t5_archer: number, t5_siege: number,
            t4_cav: number, t4_inf: number, t4_archer: number, t4_siege: number,
            gov_id: number = None
    ):
        # find player either by linkage or provided gov id
        player = _get_player_by_id(gov_id) if gov_id else _get_player_by_ctx(ctx)

        has_attachment(ctx)

        message = _format_message(
            ctx, gov_id=player.gov_id, name=player.current_name,
            t5_cav_death=f'{t5_cav:,}', t5_inf_death=f'{t5_inf:,}',
            t5_archer_death=f'{t5_archer:,}', t5_siege_death=f'{t5_siege:,}',
            t4_cav_death=f'{t4_cav:,}', t4_inf_death=f'{t4_inf:,}',
            t4_archer_death=f'{t4_archer:,}', t4_siege_death=f'{t4_siege:,}',
        )

        await _reply_for_approval(ctx, message)

    @commands.command("myscore", help="submit the pre-kvk score")
    @enabled_by('DM_COMMAND_MY_SCORE_ENABLED')
    async def my_score(self, ctx, stage: int, score: number, gov_id: number = None):
        # find player either by linkage or provided gov id
        player = _get_player_by_id(gov_id) if gov_id else _get_player_by_ctx(ctx)

        # validate stage
        if stage not in (1, 2, 3):
            return await ctx.send(f'stage expected to be 1,2,3')

        has_attachment(ctx)

        message = _format_message(ctx, gov_id=player.gov_id, name=player.current_name, stage=stage, score=f'{score:,}')

        await _reply_for_approval(ctx, message)

    @commands.command("mynewname", help="rename your in-game name.")
    async def my_new_name(self, ctx, *, newname):
        player = _get_player_by_ctx(ctx)
        message = _format_message(ctx, gov_id=player.gov_id, oldname=player.current_name, newname=newname)
        await _reply_for_approval(ctx, message)


class OfficerOnly(commands.Cog):
    async def cog_check(self, ctx):
        if ctx.message.channel.type == discord.ChannelType.text:
            guild_setting = GuildSettings.get(id=ctx.guild.id)
            return discord.utils.get(ctx.author.roles, id=guild_setting.officer_role_id)

    @commands.command('add', help="add a new player with id and name")
    async def add(self, ctx, gov_id: number, *, name: str):
        if get_player_by_id(gov_id):
            return await ctx.send(f'{gov_id=} exists already')
        # not tag for add command for non-forwarding message
        message = _format_message(ctx, gov_id=gov_id, name=name, tag_author=False)

        await _reply_for_approval(ctx, message)

    @commands.command("link", help="link player to discord account.")
    async def link(self, ctx, discord_id: discord_mention, gov_id: number, *, name: str = ''):
        name = name or _get_player_by_id(gov_id).current_name
        if not name:
            return await ctx.send(f"Please provide in-game name as well: `!link @usename {gov_id} <player_name>`")

        guild = discord.utils.get(ctx.bot.guilds, id=GuildSettings.get(name='kingdom').id)
        if get_player_by_discord_id(ctx.message.author.id):
            alliance_name = 'unknown'
        else:
            alliance_name = get_alliance_name(guild, discord_id)
        # not tag for add command for non-forwarding message
        message = _format_message(
            ctx, gov_id=gov_id, name=name, alliance=alliance_name, discord_id=discord_id, tag_author=False)

        await _reply_for_approval(ctx, message)

        # Hint
        if get_identity_by_gov_id(gov_id):
            await ctx.send(f"**{gov_id=} has been linked already**")

    @commands.command("rename", help="update player in-game name.")
    async def rename(self, ctx, gov_id: number, *, name):
        player = get_player_by_id(gov_id)
        if not player:
            return await ctx.send(f'{gov_id=} does not exist')
        if player.current_name == name:
            return await ctx.send(f'new name is same as old name.')

        # not tag for add command for non-forwarding message
        message = _format_message(ctx, gov_id=gov_id, oldname=player.current_name, newname=name, tag_author=False)
        await _reply_for_approval(ctx, message)

    @commands.command('note', help='add note to player')
    async def note(self, ctx, gov_id: number, note_type, *, note):
        player = get_player_by_id(gov_id)
        if not player:
            return await ctx.send(f"Error: {gov_id=} does not exist.")
        add_player_note(gov_id, note_type, note)
        await ctx.message.add_reaction(settings.get('SUCCEED_EMOJI'))

    @commands.command('report', help='report records submitted by player')
    async def report(self, ctx, *, event_name=None):
        try:
            if event_name is None:
                return await ctx.send(f'Please choose one of the options to generate report:\n'
                                      f'{", ".join([f"`{e.name}`" for e in events.get_events()])}')
            sheet_link = dump_records_to_sheet(event_name, settings.get("BOT_REPORT_GOOGLE_SHEET_ID"))
        except Exception as e:
            logger.exception(f'Not able to generate report for {event_name}')
            await ctx.send(f'Error: {e}')
        else:
            await ctx.send(f"Here is the sheet {sheet_link}")


class Admin(commands.Cog):
    async def cog_check(self, ctx):
        return await ctx.bot.is_owner(ctx.author)

    @commands.command("eval", help="eval")
    async def eval(self, ctx, *, arg):
        try:
            await ctx.send(str(eval(arg)))
        except Exception as e:
            await ctx.send(str(e))

    @commands.command("run", help="exec")
    async def run(self, ctx, *, arg=None):
        from etl import JOBS
        if arg is None:
            return await ctx.send(f'{JOBS.keys()}')
        try:
            await ctx.send(f'running {arg}')
            await JOBS[arg](ctx)
        except Exception as e:
            logger.exception(f'not able to run {arg}')
            await ctx.send(repr(e))
        finally:
            await ctx.send(f'finished {arg}')

    @commands.command('event', help='event')
    async def event(self, ctx, command=None, *, arg=None):
        if command is None:
            await ctx.send("\n".join([f"`{t.to_text()}`" for t in events.list_all_events()]))
        elif command == 'add':
            await ctx.send(f'{events.add_new_event(arg).to_text()}')
        elif command == 'rename':
            await ctx.send(f'{events.rename(*arg.split(" ", maxsplit=1))}')
        elif command == 'open':
            await ctx.send(f'{events.open_event(int(arg))}')
        elif command == 'close':
            await ctx.send(f'{events.close_event()}')
        else:
            await ctx.send(f'{command} not recognized')


def _format_message(ctx, tag_author=True, append_attachment=True, show_command=True, **kwargs):
    lines_to_send = []
    if tag_author:
        lines_to_send += [ctx.message.author.mention]

    arguments = []
    if show_command:
        arguments.append(('command', ctx.command.name))
    arguments += kwargs.items()

    lines_to_send += ['```']
    lines_to_send += [f'{k}: {v}' for k, v in arguments]
    lines_to_send += ['```']

    if append_attachment and ctx.message.attachments:
        lines_to_send.append(ctx.message.attachments[0].url)

    return '\n'.join(lines_to_send)


def _get_player_by_ctx(ctx, discord_id=None):
    if discord_id is None:
        discord_id = ctx.message.author.id
    if player := get_player_by_discord_id(discord_id):
        return player

    raise commands.errors.BadArgument(
        "Your game id is not linked to your discord, Hint: use `!linkme`")


async def _reply_for_approval(ctx, reply_message):
    reply = await ctx.message.reply(reply_message)
    await reply.add_reaction(settings.get("APPROVAL_EMOJI"))
    await reply.add_reaction(settings.get("DECLINED_EMOJI"))
    await ctx.send('Please react on message to approve or cancel your request')


def _get_discord_member(ctx, discord_id):
    guild = discord.utils.get(ctx.bot.guilds, id=GuildSettings.get(name='kingdom').id)
    return guild.get_member(discord_id)


@no_raise
def _refresh_alliance(player, ctx, discord_id):
    if player:
        guild = discord.utils.get(ctx.bot.guilds, id=GuildSettings.get(name='kingdom').id)
        alliance_name = get_alliance_name(guild, discord_id)
        update_alliance(player, alliance_name)


def _get_player_by_id(gov_id):
    if player := get_player_by_id(gov_id):
        return player
    else:
        raise commands.errors.BadArgument(f'{gov_id=} does not exist, please add this account first.')
