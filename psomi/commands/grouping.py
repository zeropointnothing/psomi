from asyncio import timeout

import discord
from discord import Option
from discord.ext import commands
from psomi.utils.bot import PsomiBot
from psomi.utils.data import sort_by_page
from psomi.utils.views import ProxyGroupListView
from psomi.errors import NotFoundError, DuplicateError


class Grouping(commands.Cog):
    def __init__(self, bot):
        self.bot: PsomiBot = bot
        self.description = "Commands related to modifying or viewing ProxyGroups."

    grouping = discord.SlashCommandGroup(
        name="grouping", description="Commands related to modifying or viewing ProxyGroups."
    )

    @grouping.command(name="create", description="Create a new ProxyGroup")
    async def create_command(
            self,
            ctx: discord.ApplicationContext,
            title: Option(str, description="The ProxyGroup's title.", required=True)
    ):
        try:
            user = self.bot.database.get_user(str(ctx.author.id))
        except NotFoundError: # we should add the user if they are not present
            user = self.bot.database.add_user(str(ctx.author.id))
        
        try:
            self.bot.database.create_proxygroup(user, title)
        except DuplicateError:
            await ctx.respond("Unable to create ProxyGroup, as one with that name already exists.")
            return
        
        await ctx.respond(f"Successfully created the '{title}' ProxyGroup!")

    @grouping.command(name="delete", description="Delete an existing ProxyGroup.")
    async def delete_command(
            self,
            ctx: discord.ApplicationContext,
            title: Option(str, "The title of the ProxyGroup you wish to delete.", required=True)
    ):
        try:
            user = self.bot.database.get_user(str(ctx.author.id))
        except NotFoundError:
            await ctx.respond("You do not currently have any created ProxyGroups! Try creating one first!")
            return

        try:
            group = self.bot.database.get_proxygroup(user, title)
        except NotFoundError:
            await ctx.respond(f"You do not have a ProxyGroup with the title '{title}'!")
            return

        await ctx.respond(f"Are you sure you'd like to delete this ProxyGroup? ('{title}')\n"
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

    @grouping.command(name="rename", description="Update a ProxyGroup's title.")
    async def rename_command(
            self,
            ctx: discord.ApplicationContext,
            old_title: Option(str, "The title of the ProxyGroup you wish to update.", required=True),
            new_title: Option(str, "The title you wish to update it to.", required=True)
    ):
        try:
            user = self.bot.database.get_user(str(ctx.author.id))
        except NotFoundError:
            await ctx.respond("You do not currently have any created ProxyGroups! Try creating one first!")
            return

        try:
            group = self.bot.database.get_proxygroup(user, old_title)
        except NotFoundError:
            await ctx.respond(f"You do not have a ProxyGroup with the title '{old_title}'!")
            return

        try:
            self.bot.database.retitle_proxygroup(user, group, new_title)
        except DuplicateError:
            await ctx.respond(f"The title you supplied ('{new_title}') is already in use!")
            return

        await ctx.respond(f"Successfully renamed the '{old_title}' ProxyGroup to '{new_title}'!")

    @grouping.command(name="add", description="Add a Character to a ProxyGroup.")
    async def add_command(
            self,
            ctx: discord.ApplicationContext,
            group_name: Option(str, "The name of the ProxyGroup you wish to add to.", required=True),
            character_name: Option(str, "The name of the Character you wish to add.", required=True)
    ):
        try:
            user = self.bot.database.get_user(str(ctx.author.id))
        except NotFoundError:
            await ctx.respond("You need to have Characters first!")
            return
        try:
            group = self.bot.database.get_proxygroup(user, group_name)
        except NotFoundError:
            await ctx.respond(f"You do not have a ProxyGroup with the title '{group_name}'!")
            return
        try:
            character = self.bot.database.get_character(user, character_name)
        except NotFoundError:
            await ctx.respond(f"You don't have a Character under the name '{character_name}'!")
            return

        if character.proxygroup_name == group_name:
            await ctx.respond(f"'{character_name}' is already present in this group!")
            return

        self.bot.database.group_character(user, character, group)

        await ctx.respond(f"Successfully placed '{character_name}' into the '{group_name}' ProxyGroup!")

    @grouping.command(name="remove", description="Remove a Character from their current ProxyGroup.")
    async def remove_command(
            self,
            ctx: discord.ApplicationContext,
            character_name: Option(str, "The name of the Character you wish to remove.", required=True)
    ):
        try:
            user = self.bot.database.get_user(str(ctx.author.id))
        except NotFoundError:
            await ctx.respond("You need to have Characters first!")
            return
        try:
            character = self.bot.database.get_character(user, character_name)
        except NotFoundError:
            await ctx.respond(f"You don't have a Character under the name '{character_name}'!")
            return

        if character.proxygroup_name is None:
            await ctx.respond(f"'{character_name}' isn't in any ProxyGroups!")
            return

        self.bot.database.ungroup_character(user, character)

        await ctx.respond(f"Successfully removed '{character_name}' from their current ProxyGroup "
                          f"('{character.proxygroup_name}')!")

    @grouping.command(name="list", description="List all of your created ProxyGroups.")
    async def list_command(
            self,
            ctx: discord.ApplicationContext,
            page: Option(int, description="What page to show.", default=1)
    ):
        try:
            user = self.bot.database.get_user(str(ctx.author.id))
        except NotFoundError:
            await ctx.respond("You don't have any created ProxyGroups! Try again after creating some!")
            return

        # create the embed
        groups = sort_by_page([user.proxy_groups], page, 20)
        if groups["group_num"] == 0:
            await ctx.respond(f"That's out of bounds! Please choose a number between 0 and {groups["page_total"]}!")
            return

        embed = discord.Embed(
            title=f"Created ProxyGroups [{page}/{groups["page_total"]}]"
        )

        for i, proxygroup in enumerate(groups["page"]):
            embed.add_field(
                name=proxygroup.title,
                value=f"Character Count: {len(proxygroup.characters)}"
            )

        if not groups["page"]:
            embed.set_footer(text="Nothing here...")
        elif page < groups["page_total"]:
            embed.set_footer(text="More on next page...")

        await ctx.respond(
            embed=embed,
            view=ProxyGroupListView(
                page=page,
                user=user,
                author=ctx.author,
                timeout=120
            )
        )

def setup(bot):
    bot.add_cog(Grouping(bot))
