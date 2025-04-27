import discord
from discord.ext import commands
from psomi.utils.bot import PsomiBot
from psomi.errors import NotFoundError, DuplicateError


class Grouping(commands.Cog):
    def __init__(self, bot):
        self.bot: PsomiBot = bot
        self.description = "Commands related to modifying or viewing ProxyGroups."

    @commands.command(name="create", description="Create a new ProxyGroup")
    async def create_command(self, ctx: commands.Context, name: str):
        try:
            user = self.bot.database.get_user(str(ctx.message.author.id))
        except NotFoundError: # we should add the user if they are not present
            user = self.bot.database.add_user(str(ctx.message.author.id))
        
        try:
            self.bot.database.create_proxygroup(user, name)
        except DuplicateError:
            await ctx.reply("Unable to create ProxyGroup, as one with that name already exists.")
            return
        
        await ctx.reply(f"Successfully created the '{name}' ProxyGroup!")

def setup(bot):
    bot.add_cog(Grouping(bot))
