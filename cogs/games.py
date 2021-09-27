from discord.ext import commands
from discord import Embed, Colour
from cogs._wfmhandler import wfm_search, wfm_find, wfm_load, wfm_getuserf
from datetime import datetime
import random
import json
import pathlib

cwd = pathlib.Path().absolute()

with open(cwd/"cogs/config/lol_runes.json") as json_file:
    runes = json.load(json_file)

with open(cwd/"cogs/config/lol_items.json") as json_file:
    items = json.load(json_file)

with open(cwd/"cogs/config/lol_champions.json") as json_file:
    champions = json.load(json_file)

items = items["data"]
mythics = []
mythic_ids = []
for item in items:
    item_ = items[item]
    if item_["description"].find("Mythic") != -1:
        mythics.append(item_)
        mythic_ids.append(item)

for id in mythic_ids:
    del items[id]


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.item_data, self.item_names = wfm_load()

    @commands.command()
    async def build(self, ctx):
        # Champion
        champion = random.choice(champions)
        champion = champion["name"]
        # Get path
        path = random.choice(list(runes.keys()))
        # Get keystone
        keystone = random.choice(runes[path]["keystones"])
        # Get secondary runes
        secondary = []
        for secondary_list in runes[path]["secondary"]:
            chosen_secondary = random.choice(secondary_list)
            secondary.append(chosen_secondary)
        # Get secondary path
        runes_secondary = dict(runes)
        del runes_secondary[path]
        secondary_path = random.choice(list(runes_secondary.keys()))
        secondary_2 = []
        for secondary_list in runes[secondary_path]["secondary"]:
            chosen_secondary = random.choice(secondary_list)
            secondary_2.append(chosen_secondary)
        secondary_2_old = secondary_2
        secondary_2 = []
        c = random.choice(secondary_2_old)
        secondary_2_old.remove(c)
        secondary_2.append(c)
        c = random.choice(secondary_2_old)
        secondary_2.append(c)
        # get items
        item_build = []
        i = 0
        while i < 5:
            ci = random.choice(list(items.values()))
            if ci["gold"]["total"] >= 1600 and ci["gold"]["total"] <= 3800:
                item_build.append(ci["name"])
                i += 1
        chosen_mythic = random.choice(mythics)["name"]
        # get spells
        all_spells = ["Ghost", "Heal", "Barrier", "Exhaust",
                      "Flash", "Teleport", "Cleanse", "Ignite", "Smite"]
        spells = []
        c = random.choice(all_spells)
        spells.append(c)
        all_spells.remove(c)
        c = random.choice(all_spells)
        spells.append(c)
        # max order
        abilities = ["Q", "W", "E"]
        random.shuffle(abilities)
        # convert to string & other formatting in embed
        secondary_str = "\n".join(secondary)
        secondary_tree_str = "\n".join(secondary_2)
        items_str = " **>** ".join(item_build)
        spells_str = " **&** ".join(spells)
        abilities_str = " **>** ".join(abilities)
        embed = Embed(
            title=f"{champion}", color=Colour.gold())
        embed.add_field(
            name=path, value=f"**{keystone}**\n{secondary_str}", inline=True)
        embed.add_field(name=secondary_path,
                        value="\n"+secondary_tree_str, inline=True)
        embed.add_field(name="Spells", value=spells_str, inline=False)
        embed.add_field(name="Abilities", value=abilities_str, inline=True)
        embed.add_field(
            name="Items", value=f"**{chosen_mythic}** **>** {items_str}", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def wfm(self, ctx, subcommand, *, message=None):
        response = None
        if message is not None:
            message = str(message.strip().title())
            if subcommand == "item":
                _items = []
                _item = None
                _parts = ["", "Set", "Prime Set", "Relic"]
                for _p in _parts:
                    _items.append(
                        wfm_find(message + " " + _p.strip(), self.item_data))
                for _i in _items:
                    if _i is not None:
                        _item = _i
                if _item is None:
                    return
                _icon = "https://warframe.market/static/assets/"+_item["thumb"]
                _url = "https://warframe.market/items/" + _item["url_name"]
                response = Embed(
                    title=_item["item_name"], url=_url, color=Colour.blue())
                response.set_thumbnail(url=_icon)
                _price_avg, _count, _cheapest = wfm_search(_item)
                response.add_field(
                    name="Price", value=f"Average price: **{_price_avg} platinum** from **{_count} listings**", inline=False)
                whisper = "/w **{}** Hi! WTB: **{}** for **{} platinum**. (warframe.market)".format(
                    _cheapest["user"], _item["item_name"], _cheapest["price"])
                response.add_field(name="Best offer (/whisper)",
                                   value=whisper, inline=False)
                dt = datetime.now().strftime("%d %b %Y - %H:%M:%S")
                response.add_field(
                    name="http://bit.ly/wfdropdb - for more info on item drops", value=f"*{dt}*", inline=False)
            elif subcommand == "user" or subcommand == "profile":
                _orders = wfm_getuserf(message)
                if _orders is not None:
                    _url = "https://warframe.market/profile/" + message
                    response = Embed(title=message, url=_url,
                                     color=Colour.green())
                    # orders_sell, orders_buy = _orders[0], _orders[1]\
                    _sell = _buy = []
                    # wts listings
                    for _wts in _orders[0]:
                        _item = wfm_find(_wts["item_name"], self.item_data)
                        _price_avg, _count, _cheapest = wfm_search(_item)
                        reply = "**{}** for **{} platinum** | avg. **{} platinum** from **{} listings**".format(
                            _wts["item_name"], _wts["platinum"], _price_avg, _count)
                        _sell.append(reply)
                    # wtb listings
                    for _wtb in _orders[1]:
                        _item = wfm_find(_wtb["item_name"], self.item_data)
                        _price_avg, _count, _cheapest = wfm_search(_item)
                        reply = "**{}** for **{} platinum** | avg. **{} platinum** from **{} listings**".format(
                            _wtb["item_name"], _wtb["platinum"], _price_avg, _count)
                        _buy.append(reply)
                    # add fields
                    response.add_field(
                        name="Want to sell", value="\n".join(_sell), inline=False)
                    response.add_field(
                        name="Want to buy", value="\n".join(_buy), inline=False)

        if response is not None:
            await ctx.send(embed=response)


def setup(bot):
    bot.add_cog(Games(bot))
