import logging

import settings
from goldbot.utils import convert_to_dict
from models import Player, Record, RecordingEvent
from transactions.players import update_player
from transactions.records import create_record

logger = logging.getLogger(__name__)


async def execute(message, payload):
    lines = message.content.split('```')[1].strip().split()
    args = convert_to_dict(lines)
    command = args.pop('command', None)
    if command == 'linkme':
        update_player(discord_id=message.mentions[0].id, **args)
    elif command in ('mykill', 'myscore', 'myhonor'):
        player = Player.get(gov_id=args.pop('gov_id'))
        event = RecordingEvent.current_event()
        if command == 'myscore':
            args['stage' + args.pop('stage')] = args.pop('score')
        for k, v in args.items():
            record_type = Record.Type[k.capitalize()]
            create_record(player, record_type, v, event)
    else:
        await message.add_reaction(settings.get("FAILURE_EMOJI"))
        return await message.reply(f'unrecognized {command=}')

    await message.clear_reactions()
    await message.add_reaction(settings.get("SUCCEED_EMOJI"))
    if message.mentions:
        await message.mentions[0].send(f"You submission has been approved by {payload.member.mention}")
