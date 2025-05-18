import aiohttp
import discord
from discord import RawReactionActionEvent

from psomi.errors import NotFoundError
from psomi.utils.bot import PsomiBot
from psomi.utils.checking import enforce_annotations


@enforce_annotations
async def edit_reaction(bot: PsomiBot, payload: RawReactionActionEvent) -> None:
    """
    Attempt to edit the message attached to the payload.

    :param bot: The PsomiBot instance.
    :param payload: The reaction payload.
    :return:
    """
    try:
        user = bot.database.get_user(str(payload.member.id))
    except (NotFoundError, AttributeError):
        return
    try:
        channel_webhooks = await bot.http.channel_webhooks(payload.channel_id)
    except discord.errors.NotFound:
        return

    psomi_webhook = None
    for hook in channel_webhooks:
        if hook.get("name", None) == bot.webhook_name:
            psomi_webhook = hook
            break
    if not psomi_webhook:
        psomi_webhook = await bot.http.create_webhook(payload.channel_id, name=bot.webhook_name)

    psomi_webhook_id = psomi_webhook.get("id")
    psomi_webhook_token = psomi_webhook.get("token")
    psomi_webhook_url = f"https://discord.com/api/webhooks/{psomi_webhook_id}/{psomi_webhook_token}"
    proxied_messages = bot.webhook_cache.get_user_webhooks(user)

    if not proxied_messages:
        return

    try:
        proxied_message = [
            _ for _ in proxied_messages if _["message_id"] == str(payload.message_id)
        ][0]
    except IndexError:
        return

    # likely won't happen, but just in case!
    if proxied_message["author_id"] != user.uid:
        return

    original_message = bot.get_channel(payload.channel_id)
    original_message = await original_message.fetch_message(payload.message_id)
    await payload.member.send("Editing the following message:\n"
                              f"```{original_message.content}```\n"
                              "Please respond with the new content:")

    try:
        result: discord.Message = await bot.wait_for(
            "message",
            check=lambda x: x.author.id == payload.member.id and isinstance(x.channel, discord.DMChannel),
            timeout=120.0
        )
    except TimeoutError:
        await payload.member.send("Aborting due to lack of accepted response...")
        return
    finally:
        await original_message.remove_reaction("📝", payload.member)

    async with aiohttp.ClientSession() as session:
        proxy_webhook = discord.Webhook.from_url(psomi_webhook_url, session=session)

        await proxy_webhook.edit_message(
            message_id=proxied_message["message_id"],
            content=result.content
        )

    await payload.member.send(f"Successfully edited the message!\n\n{original_message.jump_url}")
