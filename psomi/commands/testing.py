import discord
from discord.ext import commands

class Testing(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.command(name="ping", description="Ping!")
    async def ping_command(self, ctx: commands.Context):
        await ctx.reply(f"Pong! ({round(self.bot.latency, 3)})")

def setup(bot):
    bot.add_cog(Testing(bot))