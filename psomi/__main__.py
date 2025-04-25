import json
import discord
import discord.ext.commands as commands
from psomi.commands import command_groups
from psomi.utils.data import Data

intents = discord.Intents.default() #Defining intents
intents.message_content = True # Adding the message_content intent so that the bot can read user messages
bot = commands.Bot(command_prefix="p!", intents=intents)

if __name__ == "__main__":
    print(command_groups)
    for group in command_groups:
        bot.load_extension(group)


    with open("config.json", "r") as f:
        bot.run(json.load(f)["token"])
