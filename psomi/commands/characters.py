import discord
from discord.ext import commands
from psomi.utils.bot import PsomiBot
from psomi.utils.data import sort_by_page


class Characters(commands.Cog):
    def __init__(self, bot):
        self.bot: PsomiBot = bot
        self.description = "Commands related to modifying or viewing Characters."

    @commands.command(name="list", description="List all of your registered Characters.")
    async def list_command(self, ctx: commands.Context, page: int = 1):
        try:
            user = self.bot.database.get_user(str(ctx.message.author.id))
        except ValueError:
            await ctx.reply("You don't have any registered Characters! Try again after registering some!")
            return

        # create the embed
        characters = sort_by_page([_.characters for _ in user.proxy_groups], page, 20)
        embed = discord.Embed(
            title=f"Registered Characters [{characters["group_num"]}/{len(user.proxy_groups)}]"
                  f"({user.proxy_groups[characters["group_num"]-1].name}):"
        )

        for i, character in enumerate(characters["page"]):
            embed.add_field(
                name=character.name,
                value=f"Prefix: `{character.prefix}`\n"
                      + (f"Avatar: [linkie]({character.avatar})" if character.avatar else "Avatar: None")
            )

        if characters["group_num"] < len(user.proxy_groups):
            embed.set_footer(text="More on next page...")

        # reply to the user
        if ctx.message.reference is not None:
            try:
                # If the message is a reply, edit instead.
                referenced_message = ctx.message.reference.cached_message
                if self.bot.user and referenced_message.author.id != self.bot.user.id:
                    await ctx.channel.send("I didn't send that message!")
                    return

                await referenced_message.edit(embed=embed)
                await ctx.message.delete()
            except AttributeError:
                await ctx.channel.send("Unable to edit. Message was not cached!")
                return
            except discord.errors.NotFound: # The message got deleted from something else, do nothing.
                pass
        else:
            await ctx.reply(embed=embed)

def setup(bot):
    bot.add_cog(Characters(bot))
