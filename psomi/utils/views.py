import discord
from typing import cast
from psomi.errors import OutOfBoundsError
from psomi.utils.data import User, sort_by_page

class CharacterListView(discord.ui.View):
    def __init__(self, page: int, user: User, author: discord.User, *args, **kwargs):
        self.current_page = page
        self.max_page = sort_by_page([_.characters for _ in user.proxy_groups], 1, 20)["page_total"]
        self.user = user
        self.author = author

        super().__init__(*args, **kwargs)

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.author.id

    async def construct_embed(self):
        if self.current_page < 1:
            raise OutOfBoundsError("Cannot have a page number lower than 1!")

        # create the embed
        characters = sort_by_page([_.characters for _ in self.user.proxy_groups], self.current_page, 20)
        if self.current_page > self.max_page:
            raise OutOfBoundsError(f"Cannot have a page number higher than {self.max_page}!")
        elif characters["group_num"] == 0:
            raise OutOfBoundsError("The requested page was out of bounds!")

        embed = discord.Embed(
            title=f"Registered Characters [{self.current_page}/{self.max_page}]"
                  f"({self.user.proxy_groups[characters["group_num"]-1].title}):"
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
        elif self.current_page < characters["page_total"]:
            embed.set_footer(text="More on next page...")

        return embed

    @discord.ui.button(label="⏮️", style=discord.ButtonStyle.green)
    async def first_callback(self, button: discord.Button, interaction: discord.Interaction):
        self.current_page = 1
        embed = await self.construct_embed()
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.primary)
    async def previous_callback(self, button: discord.Button, interaction: discord.Interaction):
        self.current_page -= 1
        # self.current_page %=
        try:
            embed = await self.construct_embed()
        except OutOfBoundsError:
            await interaction.response.send_message("There are no more pages!", ephemeral=True)
            self.current_page += 1
            return        # await self.message.edit(embed=embed)
        await interaction.response.edit_message(embed=embed)


    # @discord.ui.button(label="🔢", style=discord.ButtonStyle.secondary)
    # async def jump_to(self, button: discord.Button, interaction: discord.Interaction):
    #     bot = cast(PsomiBot, interaction.client)
    #
    #     await interaction.channel.send("Reply with the page number you wish to jump to within ten seconds.", ephemeral=True)
    #     await interaction.response.defer()
    #     try:
    #         # destructive action, we should wait for confirmation first.
    #         result: discord.Message = await bot.wait_for(
    #             "message",
    #             check=lambda x: x.channel.id == interaction.channel.id
    #             and x.author.id == self.author.id
    #             and x.content.isdigit(),
    #             timeout=20.0
    #         )
    #     except TimeoutError:
    #         await interaction.channel.send("Aborting due to lack of accepted response...")
    #         return
    #
    #     try:
    #         self.current_page = int(result.content)
    #         embed = await self.construct_embed(bot)
    #     except OutOfBoundsError:
    #         await interaction.channel.send("Invalid page number!", ephemeral=True)
    #         return
    #     # await self.message.edit(embed=embed)
    #     await interaction.followup.edit_message(embed=embed)
    #     # await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.primary)
    async def next_callback(self, button: discord.Button, interaction: discord.Interaction):
        self.current_page += 1
        # self.current_page %=
        try:
            embed = await self.construct_embed()
        except OutOfBoundsError:
            await interaction.response.send_message("There are no more pages!", ephemeral=True)
            self.current_page -= 1
            return
        # await self.message.edit(embed=embed)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="⏭️", style=discord.ButtonStyle.green)
    async def last_callback(self, button: discord.Button, interaction: discord.Interaction):
        self.current_page = self.max_page
        embed = await self.construct_embed()
        await interaction.response.edit_message(embed=embed)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
            # self.remove_item(item)
        try:
            await self.parent.edit(content="This view has timed out.", view=self)
        except discord.errors.NotFound: # message was likely deleted, no need to do anything
            pass

class ProxyGroupListView(discord.ui.View):
    def __init__(self, page: int, user: User, author: discord.User, *args, **kwargs):
        self.current_page = page
        self.user = user
        self.author = author

        super().__init__(*args, **kwargs)

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.author.id

    async def construct_embed(self):
        if self.current_page < 1:
            raise OutOfBoundsError("Cannot have a page number lower than 1!")

        # create the embed
        groups = sort_by_page([self.user.proxy_groups], self.current_page, 20)
        if self.current_page > groups["page_total"]:
            raise OutOfBoundsError(f"Cannot have a page number higher than {groups["page_total"]}!")
        elif groups["group_num"] == 0:
            raise OutOfBoundsError("The requested page was out of bounds!")
            # await ctx.respond(f"That's out of bounds! Please choose a number between 0 and {characters["page_total"]}!")

        embed = discord.Embed(
            title=f"Created ProxyGroups [{self.current_page}/{groups["page_total"]}]"
        )

        for i, proxygroup in enumerate(groups["page"]):
            embed.add_field(
                name=proxygroup.title,
                value=f"Character Count: {len(proxygroup.characters)}"
            )

        if not groups["page"]:
            embed.set_footer(text="Nothing here...")
        elif self.current_page < groups["page_total"]:
            embed.set_footer(text="More on next page...")

        return embed

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.primary)
    async def previous_callback(self, button: discord.Button, interaction: discord.Interaction):
        self.current_page -= 1
        # self.current_page %=
        try:
            embed = await self.construct_embed()
        except OutOfBoundsError:
            await interaction.response.send_message("There are no more pages!", ephemeral=True)
            self.current_page += 1
            return        # await self.message.edit(embed=embed)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.primary)
    async def next_callback(self, button: discord.Button, interaction: discord.Interaction):
        self.current_page += 1
        # self.current_page %=
        try:
            embed = await self.construct_embed()
        except OutOfBoundsError:
            await interaction.response.send_message("There are no more pages!", ephemeral=True)
            self.current_page -= 1
            return
        # await self.message.edit(embed=embed)
        await interaction.response.edit_message(embed=embed)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
            # self.remove_item(item)
        try:
            await self.parent.edit(content="This view has timed out.", view=self)
        except discord.errors.NotFound: # message was likely deleted, no need to do anything
            pass
