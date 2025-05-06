import discord
from typing import cast
from psomi.utils.bot import PsomiBot

def chr_name_autocomplete(ctx: discord.AutocompleteContext):
    bot = cast(PsomiBot, ctx.bot)

    if str(ctx.interaction.user.id) in bot.user_cache:
        print("cache hit! (character name)")
        user = bot.user_cache[str(ctx.interaction.user.id)]
    else:
        print("cache miss! (character name)")
        user = bot.database.get_user(str(ctx.interaction.user.id))
        bot.user_cache[user.uid] = user
    return [_[0].name for _ in user.get_character_by_search(ctx.value)]

def pgp_name_autocomplete(ctx: discord.AutocompleteContext):
    bot = cast(PsomiBot, ctx.bot)

    if str(ctx.interaction.user.id) in bot.user_cache:
        print("cache hit! (proxygroup name)")
        user = bot.user_cache[str(ctx.interaction.user.id)]
    else:
        print("cache miss! (proxygroup name)")
        user = bot.database.get_user(str(ctx.interaction.user.id))
        bot.user_cache[user.uid] = user
    return [_[0].title for _ in user.get_proxygroup_by_search(ctx.value)]

def bracket_autocomplete(ctx: discord.AutocompleteContext):
    if not ctx.value:
        return []
    elif "text" not in ctx.value:
        return [ctx.value+":text"]
    else:
        return [ctx.value]