import datetime
import json
import time
import discord
import aiohttp
from discord import RawReactionActionEvent
from discord.ext import tasks

from psomi.commands import command_groups
from psomi.utils.bot import PsomiBot
from psomi.utils.parsing import parse_message
from psomi.errors import NotFoundError
from psomi.utils.reactions import edit_reaction

intents = discord.Intents.default() #Defining intents
intents.message_content = True # Adding the message_content intent so that the bot can read user messages
bot = PsomiBot(command_prefix="p!", db_path="database.db", wc_path="wccache.db", intents=intents)

@bot.event
async def on_ready():
    print("Performing initial stress-test...")
    result = bot.preform_stress_test()
    print(f"Finished user bulk-test in: {result["user_time"]} seconds ({result["user_count"]} constructed)!")
    print(f"Finished mass bulk-test in: {result["mass_time"]} seconds ({result["mass_count"]} constructed)!")

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"for new horizons... 🚧",
        )
    )

    clear_webhooks.start()

@bot.event
async def on_raw_reaction_add(payload: RawReactionActionEvent):
    if str(payload.emoji) == "📝":
        await edit_reaction(bot, payload)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    try:
        user = bot.database.get_user(str(message.author.id))
    except NotFoundError: # user isn't in the database, we don't need to continue
        await bot.process_commands(message)
        return

    try:
        channel_webhooks = await bot.http.channel_webhooks(message.channel.id)
    except discord.errors.NotFound:
        return
    
    psomi_webhook = None
    for hook in channel_webhooks:
        if hook.get("name", None) == bot.webhook_name:
            psomi_webhook = hook
            break
    if not psomi_webhook:
        psomi_webhook = await bot.http.create_webhook(message.channel.id, name=bot.webhook_name)

    psomi_webhook_id = psomi_webhook.get("id")
    psomi_webhook_token = psomi_webhook.get("token")
    psomi_webhook_url = f"https://discord.com/api/webhooks/{psomi_webhook_id}/{psomi_webhook_token}"

    if not psomi_webhook_token:
        await message.channel.send("Webhook error! Please contact the instance owner!")
        raise AttributeError(f"Failed to retrieve token for webhook under the name '{bot.webhook_name}!'"
                             f" Something is wrong!")

    parsed_message = parse_message(user, message.content)

    # do on_message based character updates
    for character in parsed_message:
        # get the updated Character class...
        updated_character = bot.database.update_character(
            user, character["character"], "proxy_count", character["character"].proxy_count + 1
        )
        # then update it across the entire list.
        for i, _ in enumerate(parsed_message):
            if _["character"].name == updated_character.name:
                parsed_message[i] = {"character": updated_character, "message": _["message"]}


    async with (aiohttp.ClientSession() as session):
        for i, character in enumerate(parsed_message):
            character_webhook = discord.Webhook.from_url(psomi_webhook_url, session=session)
            character_content: str = '\n'.join(character["message"])
            prefix, suffix = character["character"].prefix.split("text")

            if prefix:
                character_content = character_content.removeprefix(prefix)
            if suffix:
                character_content = character_content.removesuffix(suffix)

            # construct reference
            if i == 0 and message.reference:
                try:
                    referenced_message = message.reference.cached_message

                    try:
                        webhook_author = bot.webhook_cache.get_webhook_author_id(str(referenced_message.id))
                    except NotFoundError:
                        webhook_author = None

                    if webhook_author:
                        # use guild.fetch_member to get around stupid caching issues
                        guild = bot.get_guild(message.guild.id)
                        replied_user = await guild.fetch_member(int(webhook_author))
                    else:
                        replied_user = referenced_message.author

                    referenced_content = referenced_message.content
                    referenced_content = referenced_content.split("\n")

                    # Get rid of the last reply to make it look cleaner.
                    for i, _ in enumerate(referenced_content):
                        if _.startswith("> "):
                            referenced_content.remove(_)

                    replied_content = " ".join(referenced_content)
                    replied_content = replied_content.replace(
                        "\n", " "
                    )
                    # print(referenced_message)
                    channel_id = referenced_message.channel.id
                    message_id = referenced_message.id

                    character_content = (
                        f"> {replied_content}\n{replied_user.mention} - [Jump](<https://discord.com/channels/@me/{channel_id}/{message_id}>)\n"
                        + character_content
                    )
                except AttributeError:
                    pass

            proxied_message = await character_webhook.send(
                character_content,
                username=character["character"].name,
                avatar_url=character["character"].avatar if character["character"].avatar else discord.MISSING,
                wait=True
            )

            bot.webhook_cache.add_user_webhook(user, str(proxied_message.id), character_webhook.url)
            # await asyncio.sleep(0.2)

    if parsed_message:
        try:
            await message.delete()
        except discord.errors.NotFound: # message doesn't exist anymore, no need to do anything
            pass

    await bot.process_commands(message)

@tasks.loop(minutes=1)
async def clear_webhooks():
    now = datetime.datetime.now()

    # when to run the purge (in military time)
    run_at = datetime.time(0, 30)
    run_at_day = ["Wednesday", "Sunday"]

    if now.hour != run_at.hour or now.minute != run_at.minute or now.strftime("%A") not in run_at_day:
        return

    print("Running Webhook purge...")
    purge_start = time.time()
    for user_id in bot.database.get_all_user_ids():
        user = bot.database.get_user(user_id)

        bot.webhook_cache.purge_old_records(user, 50)
    purge_end = time.time()-purge_start
    print(f"Finished Webhook purge! (took {round(purge_end, 3)} seconds)")

if __name__ == "__main__":
    print(command_groups)
    for group in command_groups:
        bot.load_extension(group)


    with open("config.json", "r") as f:
        bot.run(json.load(f)["token"])
