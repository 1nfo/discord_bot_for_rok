import settings


async def execute(message, payload):
    await message.add_reaction(settings.get("FAILURE_EMOJI"))
    if message.mentions:
        await message.mentions[0].send(
            f"There is an issue in your submission, please check with officer {payload.member.mention}")
