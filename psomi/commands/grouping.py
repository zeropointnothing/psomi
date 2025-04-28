from asyncio import timeout

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

    @commands.command(name="delete", description="Delete an existing ProxyGroup.")
    async def delete_command(self, ctx: commands.Context, title: str):
        try:
            user = self.bot.database.get_user(str(ctx.message.author.id))
        except NotFoundError:
            await ctx.reply("You do not currently have any created ProxyGroups! Try creating one first!")
            return

        try:
            group = self.bot.database.get_proxygroup(user, title)
        except NotFoundError:
            await ctx.reply(f"You do not have a ProxyGroup with the title '{title}'!")
            return

        await ctx.reply(f"Are you sure you'd like to delete this ProxyGroup? ('{title}')\n"
                        "This action is irreversible! All Characters within this group will become uncategorized!\n"
                        "Reply with 'I am sure!' to proceed, or 'cancel' to abort (or wait 20 seconds).")

        try:
            # destructive action, we should wait for confirmation first.
            result: discord.Message = await self.bot.wait_for(
                "message",
                check=lambda x: x.channel.id == ctx.channel.id
                and x.author.id == ctx.author.id
                and x.content.lower() in ["i am sure!", "cancel"],
                timeout=20.0
            )
        except TimeoutError:
            await ctx.send("Aborting due to lack of accepted response...")
            return

        if result.content.lower() == "i am sure!":
            self.bot.database.delete_proxygroup(user, group)

            await result.reply(f"Successfully deleted the '{title}' ProxyGroup!")
        else:
            await result.reply("Canceled!")

def setup(bot):
    bot.add_cog(Grouping(bot))
