import locale
import logging

import discord
from discord.ext import commands

import settings
from models import Player, IdentityLinkage, Identity, UsedName, Alliance
from settings.discord_guild_settings import GuildSettings
from transactions.players import create_new_player, update_name
from .utils import fuzzy_match, has_attachment, enabled_by

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
    async def whois(self, ctx, *, name):
        if name.isdigit():
            q = Player.filter(gov_id=name)
        else:
            q = Player.filter(current_name=name)

        if q.count() != 1:
            matched = list(filter(lambda x: name.lower() in x.name.lower(), UsedName.select()))
            if 1 < len(matched) <= 5:
                return await ctx.send(f"{', '.join(map(lambda x: f'`{x.name}`', matched))}. Who are you talking about?")
            if len(matched) > 5 or len(matched) == 0:
                closest_name = fuzzy_match(name, [x.name for x in UsedName.select()])
                if closest_name:
                    return await ctx.send(f"Did you mean {closest_name}?")
                else:
                    return await ctx.send(f"I don't recognize that name {name}.")
            player = matched[0].player
        else:
            player = q.get()
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
    async def list_note(self, ctx, gov_id, type_name='', limit=20):
        player = Player.get_or_none(gov_id=gov_id)
        if not player:
            return await ctx.send(f'{gov_id=} is not recognized.')

        notes = {
            f'note-{i}': f'{n.type.name} on {n.datetime_created.date().isoformat()} - {n.content}'
            for i, n in enumerate(player.get_notes(type_name, limit))
        }
        message = _format_message(ctx, **notes)
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

    @commands.command("mykill", help="submit the kill data | !mykill ID:your-id T4:t4-kill T5:t5-kill death:your-death")
    @enabled_by('DM_COMMAND_MY_KILL_ENABLED')
    async def my_kill(self, ctx, t4, t5, death, gov_id=None):
        gov_id = gov_id or _get_player_by_ctx(ctx, default_to_none=False).gov_id
        has_attachment(ctx)
        message = _format_message(ctx, gov_id=gov_id, t4=t4, t5=t5, death=death)
        reply = await ctx.message.reply(message)
        await reply.add_reaction(settings.get("APPROVAL_EMOJI"))
        await reply.add_reaction(settings.get("DECLINED_EMOJI"))

    @commands.command("myhonor", help="submit the honor data | !myhonor id:your-id honor:your_honor")
    @enabled_by('DM_COMMAND_MY_HONOR_ENABLED')
    async def my_honor(self, ctx, honor, gov_id=None):
        gov_id = gov_id or _get_player_by_ctx(ctx, default_to_none=False).gov_id
        has_attachment(ctx)
        message = _format_message(ctx, gov_id=gov_id, honor=honor)
        reply = await ctx.message.reply(message)
        await reply.add_reaction(settings.get("APPROVAL_EMOJI"))
        await reply.add_reaction(settings.get("DECLINED_EMOJI"))

    @commands.command("myscore", help="submit the pre-kvk score | !myscore stage:1/2/3 score:pre-kvk-score")
    @enabled_by('DM_COMMAND_MY_SCORE_ENABLED')
    async def my_score(self, ctx, *, stage, score, gov_id=None):
        gov_id = gov_id or _get_player_by_ctx(ctx, default_to_none=False).gov_id
        has_attachment(ctx)
        message = _format_message(ctx, gov_id=gov_id, stage=stage, score=score)
        reply = await ctx.message.reply(message)
        await reply.add_reaction(settings.get("APPROVAL_EMOJI"))
        await reply.add_reaction(settings.get("DECLINED_EMOJI"))

    @commands.command("linkme", help="link your game account to discord.")
    async def link_me(self, ctx, gov_id, name, alliance):
        player = _get_player_by_ctx(ctx)
        if player:
            return await ctx.send(f'You are already linked to gov_id: {player.gov_id}')

        player = Player.get_or_none(gov_id=gov_id)
        if player and IdentityLinkage.filter(player=player).exists():
            return await ctx.send(f"The gov_id {gov_id} has been linked already")
        if not Alliance.filter(name=alliance).exists():
            alliances = [a.name for a in Alliance.select()]
            return await ctx.send(f"{alliance} not found. Use one of them {alliances}")

        has_attachment(ctx)
        message = _format_message(ctx, gov_id=gov_id, name=name, alliance=alliance)
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

    @commands.command("introduce", help="add new member info")
    async def introduce(self, ctx, gov_id: int, *, name: str):
        if Player.filter(gov_id=gov_id).exists():
            return await ctx.send(f"Error: {gov_id=} already exists.")
        create_new_player(gov_id, name)

    @commands.command("rename", help="rename member info")
    async def rename(self, ctx, gov_id, *, name):
        player = Player.get_or_none(gov_id=gov_id)
        if not player:
            return await ctx.send(f'{gov_id=} does not exist. `!introduce f{gov_id} f{name}')
        update_name(player, name)


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
            "Your game id is not linked to with your discord, hence you must provide your id.")
