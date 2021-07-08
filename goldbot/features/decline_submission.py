import settings


async def execute(message, payload):
    await message.add_reaction(settings.get("FAILURE_EMOJI"))
    await message.remove_reaction(settings.get("APPROVAL_EMOJI"), message.author)
    await message.remove_reaction(settings.get("DECLINED_EMOJI"), message.author)
    if message.mentions:
        await message.mentions[0].send(
            f"There is an issue in your submission, please check with officer {payload.member.mention}")
