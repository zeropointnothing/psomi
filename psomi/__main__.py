import json
import discord
import discord.ext.commands as commands
import aiohttp, asyncio
from psomi.commands import command_groups
from psomi.utils.bot import PsomiBot
from psomi.utils.parsing import parse_message

intents = discord.Intents.default() #Defining intents
intents.message_content = True # Adding the message_content intent so that the bot can read user messages
bot = PsomiBot(command_prefix="p!", db_path="database.db", intents=intents)

@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"for new horizons... 🚧",
        )
    )

@bot.event
async def on_message(message: discord.message.Message):
    if message.author.bot:
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
    user = bot.database.get_user(str(message.author.id))
    
    parsed_message = parse_message(user, message.content)
    async with aiohttp.ClientSession() as session:
        for character in parsed_message:
            character_webhook = discord.Webhook.from_url(psomi_webhook_url, session=session)
            character_content: str = '\n'.join(character["message"])
            prefix, suffix = character["character"].prefix.split("text")

            if prefix:
                character_content = character_content.removeprefix(prefix)
            if suffix:
                character_content = character_content.removesuffix(suffix)

            await character_webhook.send(
                character_content,
                username=character["character"].name,
                avatar_url=character["character"].avatar if character["character"].avatar else discord.MISSING
            )
            await asyncio.sleep(0.06)

    if parsed_message:
        try:
            await message.delete()
        except discord.errors.NotFound: # message doesn't exist anymore, no need to do anything
            pass

    await bot.process_commands(message)

if __name__ == "__main__":
    print(command_groups)
    for group in command_groups:
        bot.load_extension(group)


    with open("config.json", "r") as f:
        bot.run(json.load(f)["token"])
