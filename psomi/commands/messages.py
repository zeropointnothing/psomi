import aiohttp
import discord
from discord import Option
from discord.ext import commands

from psomi.errors import NotFoundError
from psomi.utils.bot import PsomiBot

class Messages(commands.Cog):
    def __init__(self, bot):
        self.bot: PsomiBot = bot
        self.description = "Commands related to messages."

    messages = discord.SlashCommandGroup(
        name="messages", description="Commands related to messages."
    )

    @messages.command(name="edit", description="Edit a proxied message.")
    async def edit_command(
            self,
            ctx: discord.ApplicationContext,
            message_id: Option(str, "The ID of the message you want to edit.", required=True),
            new_content: Option(str, "The new content of the message.", required=True)
    ):
        try:
            user = self.bot.database.get_user(str(ctx.author.id))
        except NotFoundError:
            await ctx.respond("You don't have any registered Characters! Try again after registering some!")
            return
        try:
            channel_webhooks = await self.bot.http.channel_webhooks(ctx.channel.id)
        except discord.errors.NotFound:
            return

        psomi_webhook = None
        for hook in channel_webhooks:
            if hook.get("name", None) == self.bot.webhook_name:
                psomi_webhook = hook
                break
        if not psomi_webhook:
            psomi_webhook = await self.bot.http.create_webhook(ctx.channel.id, name=self.bot.webhook_name)

        psomi_webhook_id = psomi_webhook.get("id")
        psomi_webhook_token = psomi_webhook.get("token")
        psomi_webhook_url = f"https://discord.com/api/webhooks/{psomi_webhook_id}/{psomi_webhook_token}"
        proxied_messages = self.bot.webhook_cache.get_user_webhooks(user)

        if not proxied_messages:
            await ctx.respond("You either haven't sent any messages, or none are present in the cache!", ephemeral=True)
            return

        try:
            proxied_message = [
                _ for _ in proxied_messages if _["message_id"] == message_id
            ][0]
        except IndexError:
            await ctx.respond("That message either wasn't cached, or wasn't proxied!", ephemeral=True)
            return

        # likely won't happen, but just in case!
        if proxied_message["author_id"] != user.tid:
            await ctx.respond("You did not send this message!", ephemeral=True)
            return

        async with aiohttp.ClientSession() as session:
            proxy_webhook = discord.Webhook.from_url(psomi_webhook_url, session=session)

            await proxy_webhook.edit_message(
                message_id=proxied_message["message_id"],
                content=new_content
            )

        await ctx.respond("Successfully edited the message!", ephemeral=True)

def setup(bot):
    bot.add_cog(Messages(bot))
