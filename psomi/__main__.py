import json
import discord
import discord.ext.commands as commands
from psomi.commands import command_groups
from psomi.utils.data import Data

intents = discord.Intents.default() #Defining intents
intents.message_content = True # Adding the message_content intent so that the bot can read user messages
test = commands.Bot(command_prefix="p!", intents=intents)

if __name__ == "__main__":
    print(command_groups)
    for group in command_groups:
        test.load_extension(group)

    dt = Data("database.db")

    with open("token.json", "r") as f:
        test.run(json.load(f)["token"])
