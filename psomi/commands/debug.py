import time
import discord
from discord.ext import commands
from psomi.utils.bot import PsomiBot

class Debug(commands.Cog):
    def __init__(self, bot):
        self.bot: PsomiBot = bot
        self.description = "Debugging/status commands."

    debug = discord.SlashCommandGroup(
        name="debug", description="Debugging/status commands."
    )

    @debug.command(name="ping", description="Get this instance's current response metrics.")
    async def ping_command(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        result = self.bot.preform_stress_test()
        embed = discord.Embed(title="Pong!", description="PSOMI.v2 Latency Tests!")
        embed.add_field(name="Discord API", value=f"{round(self.bot.latency, 5)} seconds")
        embed.add_field(
            name=f"Internal Database (last tested: {round(time.time()-result["last_test"], 2)} seconds ago)",
            value=f"User bulk-test: {result["user_time"]} seconds ({result["user_count"]} constructed)\n"
                  f"Mass bulk-test: {result["mass_time"]} seconds ({result["mass_count"]} constructed)"
        )

        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Debug(bot))
