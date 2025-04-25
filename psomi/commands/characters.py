import re
import discord
from discord.ext import commands
from psomi.utils.bot import PsomiBot
from psomi.utils.data import sort_by_page


class Characters(commands.Cog):
    def __init__(self, bot):
        self.bot: PsomiBot = bot
        self.description = "Commands related to modifying or viewing Characters."
        self.url_check_regex = re.compile(
                r'^(?:http|ftp)s?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)


    @commands.command(name="register", desciption="Create and register a Character with PSOMI.")
    async def register_command(self, ctx: commands.Context, name: str, prefix: str, avatar: str | None = None):
        if not re.match(".*text.*", prefix):
            await ctx.reply("Invalid prefix supplied. Please ensure your prefix follows the `<pfx>:text:<sfx>` format!")
            return

        if len(ctx.message.attachments) > 0:
            avatar = ctx.message.attachments[0].url

        if avatar:
            # thanks:
            # https://stackoverflow.com/questions/7160737/how-to-validate-a-url-in-python-malformed-or-not
            if re.match(self.url_check_regex, avatar) is None: # validate url
                await ctx.reply("Malformed avatar url! Please ensure your arguments are supplied correctly.")
                return

        try:
            user = self.bot.database.get_user(str(ctx.message.author.id))
        except IndexError: # we should add the user if they are not present
            user = self.bot.database.add_user(str(ctx.message.author.id))
        try:
            self.bot.database.create_character(user, name, prefix, avatar)
        except ValueError:
            await ctx.reply("Unable to register Character, as one or more values are already present.\n"
                            "Make sure both the name and prefix of your Character is unique!")
            return

        await ctx.reply(f"Successfully registered '{name}'!"
                        f" To use them, type in `{prefix.replace("text", "<your message>")}`!")

    @commands.command(name="delete", description="Delete a Character.")
    async def delete_command(self, ctx: commands.Context, name: str):
        try:
            user = self.bot.database.get_user(str(ctx.message.author.id))
        except ValueError:
            await ctx.reply("You don't have any registered Characters! Try again after registering some!")
            return
        try:
            character = self.bot.database.get_character(user, name)
        except ValueError:
            await ctx.reply(f"You don't have a Character under the name '{name}'!")
            return

        self.bot.database.delete_character(user, character)

        await ctx.reply(f"Successfully deleted '{character.name}'!")

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
