import re
from typing import cast

import discord
from discord import Option
from discord.ext import commands
from psomi.utils.bot import PsomiBot
from psomi.utils.data import sort_by_page, User
from psomi.errors import NotFoundError, DuplicateError, OutOfBoundsError
from psomi.utils.views import CharacterListView


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

    characters = discord.SlashCommandGroup(
        name="characters",
        description="Commands related to modifying or viewing Characters."
    )

    @characters.command(name="register", description="Create and register a Character with PSOMI.")
    async def register_command(
            self,
            ctx: discord.ApplicationContext,
            name: Option(str, "The Character's name.", required=True),
            brackets: Option(str, "The Character's brackets.", required=True),
            avatar_file: Option(discord.Attachment, "Upload a file as the avatar.", required=False),
            avatar_url: Option(str, "Use a URL as the avatar.", required=False)
    ):
        if not re.match(".*text.*", brackets):
            await ctx.respond("Invalid brackets supplied. Please ensure your brackets follow the `<pfx>:text:<sfx>` format!")
            return

        if avatar_file:
            avatar = avatar_file.url
        elif avatar_url:
            avatar = avatar_url
        else:
            avatar = None

        if avatar:
            # thanks:
            # https://stackoverflow.com/questions/7160737/how-to-validate-a-url-in-python-malformed-or-not
            if re.match(self.url_check_regex, avatar) is None: # validate url
                await ctx.respond("Malformed avatar url! Please ensure your arguments are supplied correctly.")
                return

        try:
            user = self.bot.database.get_user(str(ctx.author.id))
        except NotFoundError: # we should add the user if they are not present
            user = self.bot.database.add_user(str(ctx.author.id))
        try:
            self.bot.database.create_character(user, name, brackets, avatar)
        except DuplicateError:
            await ctx.respond("Unable to register Character, as one or more values are already present.\n"
                            "Make sure both the name and brackets of your Character is unique!")
            return

        await ctx.respond(f"Successfully registered '{name}'!"
                        f" To use them, type in `{brackets.replace("text", "<your message>")}`!")

    @characters.command(name="unregister", description="Unregister (or delete) a Character.")
    async def unregister_command(
            self,
            ctx: discord.ApplicationContext,
            name: Option(str, "The name of the Character to unregister.", required=True)):
        try:
            user = self.bot.database.get_user(str(ctx.author.id))
        except NotFoundError:
            await ctx.respond("You don't have any registered Characters! Try again after registering some!")
            return
        try:
            character = self.bot.database.get_character(user, name)
        except NotFoundError:
            await ctx.respond(f"You don't have a Character under the name '{name}'!")
            return

        self.bot.database.delete_character(user, character)

        await ctx.respond(f"Successfully deleted '{character.name}'!")

    @characters.command(name="avatar", description="View or update a Character's avatar.")
    async def avatar_command(
            self,
            ctx: discord.ApplicationContext,
            name: Option(str, "The name of the Character you wish to update or view.", required=True),
            avatar_file: Option(discord.Attachment, "Upload a file as the new avatar.", required=False),
            avatar_url: Option(str, "Use a URL as the new avatar.", required=False)
    ):
        try:
            user = self.bot.database.get_user(str(ctx.author.id))
        except NotFoundError:
            await ctx.respond("You don't have any registered Characters! Try again after registering some!")
            return
        try:
            character = self.bot.database.get_character(user, name)
        except NotFoundError:
            await ctx.respond(f"You don't have a Character under the name '{name}'!")
            return

        if avatar_file:
            url = avatar_file.url
        elif avatar_url:
            url = avatar_url
        else:
            url = None
        if url:
            if re.match(self.url_check_regex, url) is None: # validate url
                await ctx.respond("Malformed avatar url!")
                return

            self.bot.database.update_character(user, character, "avatar", url)

            await ctx.respond(
                f"Successfully updated the avatar of '{name}'!\n"
                "(Note, avatars are subject to [Link Rot](https://en.wikipedia.org/wiki/Link_rot), as Discord routinely"
                " gets rid of unused images! Always keep a copy on one or more devices in case your avatar breaks!)"
            )
        else:
            if character.avatar:
                await ctx.respond(f"[avatar linkie]({character.avatar})")
            else:
                await ctx.respond(f"'{name}' does not currently have an avatar!")

    @characters.command(name="brackets", description="Update a Character's Prefix/Suffix.")
    async def brackets_command(
            self,
            ctx: discord.ApplicationContext,
            name: Option(str, "The name of the Character you wish to update.", required=True),
            brackets: Option(str, "The Character's new brackets.", required=True)
    ):
        if not re.match(".*text.*", brackets):
            await ctx.respond(f"The supplied brackets ({brackets}) were invalid. "
                              f"Please ensure they follow the format `<your_prefix>:text:<your_suffix>`!")
            return
        
        try:
            user = self.bot.database.get_user(str(ctx.author.id))
        except NotFoundError:
            await ctx.respond("You don't have any registered Characters! Try again after registering some!")
            return
        try:
            character = self.bot.database.get_character(user, name)
        except NotFoundError:
            await ctx.respond(f"You don't have a Character under the name '{name}'!")
            return

        try:
            self.bot.database.update_character(user, character, "prefix", brackets)
        except DuplicateError:
            in_use_by = [
                character for group in user.proxy_groups
                for character in group.characters if character.prefix == brackets
            ][0]
            await ctx.respond(f"The brackets you supplied ('{brackets}') are already in use by another character"
                              f" ('{in_use_by.name}')!")
            return

        await ctx.respond(f"Successfully updated the brackets of '{name}' to '{brackets}'!")

    @characters.command(name="rename", description="Rename a Character.")
    async def rename_command(
            self,
            ctx: discord.ApplicationContext,
            old_name: Option(str, "The Character's old name (the one you want to change).", required=True),
            new_name: Option(str, "The Character's new name (what you want to change it to)", required=True)
    ):
        try:
            user = self.bot.database.get_user(str(ctx.author.id))
        except NotFoundError:
            await ctx.respond("You don't have any registered Characters! Try again after registering some!")
            return
        try:
            character = self.bot.database.get_character(user, old_name)
        except NotFoundError:
            await ctx.respond(f"You don't have a Character under the name '{old_name}'!")
            return

        try:
            self.bot.database.update_character(user, character, "name", new_name)
        except DuplicateError:
            await ctx.respond(f"The name you supplied ('{new_name}') is already in use!")
            return
        
        await ctx.respond(f"Successfully updated the name of '{old_name}' to '{new_name}'!")

    @characters.command(name="list", description="List all of your registered Characters.")
    async def list_command(
            self,
            ctx: discord.ApplicationContext,
            page: Option(int, description="What page to show.", default=1)
    ):
        try:
            user = self.bot.database.get_user(str(ctx.author.id))
        except NotFoundError:
            await ctx.respond("You don't have any registered Characters! Try again after registering some!")
            return

        # create the embed
        characters = sort_by_page([_.characters for _ in user.proxy_groups], page, 20)
        if characters["group_num"] == 0:
            await ctx.respond(f"That's out of bounds! Please choose a number between 0 and {characters["page_total"]}!")
            return

        embed = discord.Embed(
            title=f"Registered Characters [{page}/{characters["page_total"]}]"
                  f"({user.proxy_groups[characters["group_num"]-1].title}):"
        )

        for i, character in enumerate(characters["page"]):
            embed.add_field(
                name=character.name,
                value=f"Brackets: `{character.prefix}`\n"
                      f"Message Count: {character.proxy_count}\n"
                      + (f"Avatar: [linkie]({character.avatar})" if character.avatar else "Avatar: None")
            )

        if not characters["page"]:
            embed.set_footer(text="Nothing here...")
        elif page < characters["page_total"]:
            embed.set_footer(text="More on next page...")

        await ctx.respond(
            embed=embed,
            view=CharacterListView(
                page=page,
                user=user,
                author=ctx.author,
                timeout=120
            )
        )

    @characters.command(name="find", description="Find a Character via Fuzzy Searching.")
    async def find_command(
            self,
            ctx: discord.ApplicationContext,
            query: Option(str, "The character(s) to search for.", required=True)
    ):
        try:
            user = self.bot.database.get_user(str(ctx.author.id))
        except NotFoundError:
            await ctx.respond("You don't have any registered Characters! Try again after registering some!")
            return

        embed = discord.Embed(title=f"Search Results for '{query}':")
        embed.set_footer(text="PSOMI uses Fuzzy searching to find characters. Try to make your searches specific. "
                              "Otherwise, it may get confused!")

        for i, result in enumerate(user.get_character_by_search(query, limit=10)):
            embed.add_field(
                name=result[0].name,
                value=f"Faith: {round(result[1], 2)}\n"
                      f"Message Count: {result[0].proxy_count}\n"
                      f"ProxyGroup: {result[0].proxygroup_name}\n"
                      f"Brackets: {result[0].prefix}\n" +
                      (f"Avatar: [linkie]({result[0].avatar})" if result[0].avatar else "Avatar: None")
            )

        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Characters(bot))
