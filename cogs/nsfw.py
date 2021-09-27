from cogs._decorators import guild_whitelist
from cogs._functions import split_add
from discord.ext import commands
from discord import Embed, TextChannel
from pixivapi import Client
import json
import pathlib
import random
import requests
import xmltodict
import asyncio


cwd = pathlib.Path().absolute()

with open(cwd/"cogs/config/nsfw_config.json") as json_file:
    config = json.load(json_file)

with open(cwd/"cogs/config/whitelist.json") as json_file:
    whitelist = json.load(json_file)


def rule34_search(search, pid=0):
    search = split_add(search, "+")
    r = requests.get(
        f"https://rule34.xxx//index.php?page=dapi&s=post&q=index&tags={search}&pid={pid}")
    r = r.text
    obj = xmltodict.parse(r)
    post_data = json.dumps(obj)
    post_data = json.loads(post_data)
    return post_data


class NSFW(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pixiv_client = Client()
        try:
            self.pixiv_client.authenticate(config["pixiv"]["refresh_token"])
        except:
            print("[DEBUG] Couldn't authenticate pixiv")

    @commands.command()
    @commands.is_nsfw()
    async def rule34(self, ctx, *, search):
        post_data = rule34_search(search)
        # Check if there are any results
        try:
            post_data = post_data["posts"]["post"]
        except:
            embed = Embed(title=search)
            embed.add_field(
                name="No posts found", value="try another search term (see rule34.xxx for tags)")
            await ctx.send(embed=embed)
            return
        post = random.choice(post_data)
        post_tags = post["@tags"].replace("_", "\_")
        embed = Embed(title=search, description=post_tags)
        embed.set_image(url=post["@file_url"])
        embed.set_footer(text="ID {}".format(post["@id"]))
        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_nsfw()
    @commands.cooldown(rate="1", per="5")
    async def pixiv(self, ctx):
        await ctx.send("pixiv api is currently down, waiting on a fix")

    @commands.command()
    @commands.is_nsfw()
    @guild_whitelist(whitelist["guilds"]["nsfw._sort"])
    async def sort(self, ctx, target_channel: TextChannel = None, page_id=None, *, search=None):
        if not target_channel or not page_id or not search:
            await ctx.send("command syntax: `<prefix> sort <target_channel> <rule34_page> <rule34_search>`")
            return
        if not target_channel.is_nsfw():
            await ctx.send("Target and origin channel need to be NSFW.")
            return
        post_data = rule34_search(search, page_id)
        # Check if there are any results
        try:
            post_data = post_data["posts"]["post"]
        except:
            embed = Embed(title=search)
            embed.add_field(
                name="No posts found", value="try another search term (see rule34.xxx for tags)")
            await ctx.send(embed=embed)
            return
        embed = Embed(
            title=f"Are you sure you want to start sorting by term: `{search}` in channel `#{target_channel}`?")
        embed.add_field(
            name=f"{len(post_data)} results found", value=":white_check_mark: to add | :x: to skip | :no_entry: to stop")
        confirm_message = await ctx.send(embed=embed)
        # Reaction add & check

        valid_reactions = ["✅", "❌", "⛔"]
        for add in valid_reactions:
            await confirm_message.add_reaction(add)

        def check(reaction, user):
            valid_reactions = ["✅", "❌", "⛔"]
            return user == ctx.message.author and str(reaction.emoji) in valid_reactions

        async def start_sort():
            print(f"[DEBUG] Starting sort #{target_channel.id}")
            for post in post_data:
                post_tags = post["@tags"].replace("_", "\_")
                embed = Embed(
                    title=f"{search} | page #{page_id}", description=post_tags)
                embed.set_image(url=post["@file_url"])
                embed.set_footer(text="ID {}".format(post["@id"]))
                sort_embed = await ctx.send(embed=embed)
                for add in valid_reactions:
                    await sort_embed.add_reaction(add)
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                except asyncio.TimeoutError:
                    await ctx.send(f"Waiting for reaction timed out, stopped sorting in #{target_channel}")
                    return
                else:
                    reaction = str(reaction)
                    if reaction == "✅":
                        await target_channel.send(embed=embed)
                    elif reaction == "❌":
                        continue
                    elif reaction == "⛔":
                        return

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(f"Waiting for reaction timed out, stopped sorting in #{target_channel}")
            return
        else:
            reaction = str(reaction)
            if reaction == "✅":
                await start_sort()
            elif reaction == "❌":
                return
            elif reaction == "⛔":
                return


def setup(bot):
    bot.add_cog(NSFW(bot))
