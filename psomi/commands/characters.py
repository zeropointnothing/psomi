import re
import discord
from discord.ext import commands
from psomi.utils.bot import PsomiBot
from psomi.utils.data import sort_by_page
from psomi.errors import NotFoundError, DuplicateError


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


    @commands.command(name="register", description="Create and register a Character with PSOMI.")
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
        except NotFoundError: # we should add the user if they are not present
            user = self.bot.database.add_user(str(ctx.message.author.id))
        try:
            self.bot.database.create_character(user, name, prefix, avatar)
        except DuplicateError:
            await ctx.reply("Unable to register Character, as one or more values are already present.\n"
                            "Make sure both the name and prefix of your Character is unique!")
            return

        await ctx.reply(f"Successfully registered '{name}'!"
                        f" To use them, type in `{prefix.replace("text", "<your message>")}`!")

    @commands.command(name="unregister", description="Unregister (or delete) a Character.")
    async def unregister_command(self, ctx: commands.Context, name: str):
        try:
            user = self.bot.database.get_user(str(ctx.message.author.id))
        except NotFoundError:
            await ctx.reply("You don't have any registered Characters! Try again after registering some!")
            return
        try:
            character = self.bot.database.get_character(user, name)
        except NotFoundError:
            await ctx.reply(f"You don't have a Character under the name '{name}'!")
            return

        self.bot.database.delete_character(user, character)

        await ctx.reply(f"Successfully deleted '{character.name}'!")

    @commands.command(name="avatar", description="View or update a Character's avatar.")
    async def avatar_command(self, ctx: commands.Context, name: str, url: str | None = None):
        try:
            user = self.bot.database.get_user(str(ctx.message.author.id))
        except NotFoundError:
            await ctx.reply("You don't have any registered Characters! Try again after registering some!")
            return
        try:
            character = self.bot.database.get_character(user, name)
        except NotFoundError:
            await ctx.reply(f"You don't have a Character under the name '{name}'!")
            return

        if len(ctx.message.attachments) > 0:
            url = ctx.message.attachments[0].url
        if url:
            if re.match(self.url_check_regex, url) is None: # validate url
                await ctx.reply("Malformed avatar url!")
                return

            self.bot.database.update_character(user, character, "avatar", url)

            await ctx.reply(
                f"Successfully updated the avatar of '{name}'!\n"
                "(Note, avatars are subject to [Link Rot](https://en.wikipedia.org/wiki/Link_rot), as Discord routinely"
                " gets rid of unused images! Always keep a copy on one or more devices in case your avatar breaks!)"
            )
        else:
            if character.avatar:
                await ctx.reply(f"[avatar linkie]({character.avatar})")
            else:
                await ctx.reply(f"'{name}' does not currently have an avatar!")

    @commands.command(name="brackets", description="Update a Character's Prefix/Suffix.")
    async def brackets_command(self, ctx: commands.Context, name: str, brackets: str):
        if not re.match(".*text.*", brackets):
            await ctx.reply(f"The supplied brackets ({brackets}) were invalid. Please ensure they follow the format `<your_prefix>:text:<your_suffix>`!")
            return
        
        try:
            user = self.bot.database.get_user(str(ctx.message.author.id))
        except NotFoundError:
            await ctx.reply("You don't have any registered Characters! Try again after registering some!")
            return
        try:
            character = self.bot.database.get_character(user, name)
        except NotFoundError:
            await ctx.reply(f"You don't have a Character under the name '{name}'!")
            return

        try:
            self.bot.database.update_character(user, character, "prefix", brackets)
        except DuplicateError:
            in_use_by = [character for group in user.proxy_groups for character in group.characters if character.prefix == brackets][0]
            await ctx.reply(f"The brackets you supplied ('{brackets}') are already in use by another character ('{in_use_by.name}')!")
            return

        await ctx.reply(f"Successfully updated the brackets of '{name}' to '{brackets}'!")

    @commands.command(name="rename", description="Rename a Character.")
    async def rename_command(self, ctx: commands.Context, old_name: str, new_name: str):
        try:
            user = self.bot.database.get_user(str(ctx.message.author.id))
        except NotFoundError:
            await ctx.reply("You don't have any registered Characters! Try again after registering some!")
            return
        try:
            character = self.bot.database.get_character(user, old_name)
        except NotFoundError:
            await ctx.reply(f"You don't have a Character under the name '{old_name}'!")
            return

        try:
            self.bot.database.update_character(user, character, "name", new_name)
        except DuplicateError:
            await ctx.reply(f"The name you supplied ('{new_name}') is already in use!")
            return
        
        await ctx.reply(f"Successfully updated the name of '{old_name}' to '{new_name}'!")

    @commands.command(name="list", description="List all of your registered Characters.")
    async def list_command(self, ctx: commands.Context, page: int = 1):
        try:
            user = self.bot.database.get_user(str(ctx.message.author.id))
        except NotFoundError:
            await ctx.reply("You don't have any registered Characters! Try again after registering some!")
            return

        # create the embed
        characters = sort_by_page([_.characters for _ in user.proxy_groups], page, 2)
        if characters["group_num"] == 0:
            await ctx.reply(f"That's out of bounds! Please choose a number between 0 and {characters["page_total"]}!")
            return

        embed = discord.Embed(
            title=f"Registered Characters [{page}/{characters["page_total"]}]"
                  f"({user.proxy_groups[characters["group_num"]-1].title}):"
        )

        for i, character in enumerate(characters["page"]):
            embed.add_field(
                name=character.name,
                value=f"Prefix: `{character.prefix}`\n"
                      + (f"Avatar: [linkie]({character.avatar})" if character.avatar else "Avatar: None")
            )

        if not characters["page"]:
            embed.set_footer(text="Nothing here...")
        elif page < characters["page_total"]:
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
