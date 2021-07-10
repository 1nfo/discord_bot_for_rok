import logging

import settings
from goldbot.utils import convert_to_dict
from transactions.players import upsert_player, update_name
from transactions.records import create_records

logger = logging.getLogger(__name__)


async def execute(message, payload):
    lines = message.content.split('```')[1].strip().split('\n')
    args = convert_to_dict(lines)
    command = args.pop('command', None)
    if command in ('linkme', 'link', 'add'):
        upsert_player(**args)
    elif command in ('mykill', 'myscore', 'myhonor'):
        args.pop('name', None)
        if command == 'myscore':
            args['stage' + args.pop('stage')] = args.pop('score')
        create_records(**args)
    elif command in ('rename',):
        update_name(gov_id=args['gov_id'], name=args['newname'])
    else:
        await message.add_reaction(settings.get("FAILURE_EMOJI"))
        return await message.reply(f'unrecognized {command=}')

    await message.add_reaction(settings.get("SUCCEED_EMOJI"))
    await message.remove_reaction(settings.get("APPROVAL_EMOJI"), message.author)
    await message.remove_reaction(settings.get("DECLINED_EMOJI"), message.author)
    if message.mentions:
        await message.mentions[0].send(f"You submission has been approved by {payload.member.mention}")
