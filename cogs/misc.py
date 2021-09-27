import json
import pathlib
import urllib.error

import arrow
import discord
#import tabula
from discord.ext import commands

from cogs._decorators import guild_whitelist

cwd = pathlib.Path().absolute()

with open(cwd/"cogs/config/whitelist.json") as json_file:
    whitelist = json.load(json_file)

# pdf wrapper needs java to run


def get_incidence(time_object=arrow.utcnow().to("Europe/Bucharest")):
    df = None
    date = time_object.format("DDMMYYYY")
    month = time_object.format("MM")
    pdf_url = f"https://is.prefectura.mai.gov.ro/wp-content/uploads/sites/49/2021/{month}/RI1K14_{date}.pdf"
    try:
        df = tabula.read_pdf(pdf_url, pages=1, output_format="json")
    except urllib.error.HTTPError:
        return get_incidence(time_object.shift(days=-1))
    for row in df[0]["data"]:
        if row[1]["text"] == "MUNICIPIUL IASI":
            return [row[2]["text"], time_object.format("DD/MM/YY"), pdf_url]


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(rate="1", per="10")
    @guild_whitelist(whitelist["guilds"]["misc._covid"])
    async def covid(self, ctx):
        i = get_incidence()
        i[0] = float(i[0].replace(",", ".").strip())
        if i[0] < 1:
            color = discord.Colour.green()
        elif i[0] >= 1 and i[0] < 3:
            color = discord.Colour.gold()
        else:
            color = discord.Colour.red()
        menu = discord.Embed(title="COVID-19 Stats",
                             colour=color, url=i[2])
        menu.add_field(name="**Municipiul Iasi** - Incidence Rate", value=i[0])
        menu.set_footer(text=f"latest data available: {i[1]}")
        await ctx.send(embed=menu)

    # TODO: MariaDB Integration, scrap below VV
    """
    @commands.command()
    # TODO: limit checks
    async def note(self, ctx, option, *, message=None):
        option = option.lower().strip()
        try:
            con = sqlite3.connect(db_location)
            cur = con.cursor()
            _temp = cur.execute(
                f"SELECT * FROM notes WHERE userid = {ctx.message.author.id}")
            # con.close()
        except sqlite3.OperationalError:
            await ctx.send(f"{ctx.message.author.mention}, you have no notebooks. You should add one first.")
            execute_sql(
                f"INSERT INTO notes(userid, notebooks) values ({ctx.message.author.id}, '{{}}')", db_location)
            con.commit()
            con.close()
            return
        con = sqlite3.connect(db_location)
        cur = con.cursor()
        if option == "list":
            if message is None:
                cur.execute(
                    f"SELECT notebooks FROM notes WHERE userid = {ctx.message.author.id}")
                _c = cur.fetchone()
                _c = literal_eval(_c[0])

                if len(_c) == 0:
                    await ctx.send(f"{ctx.message.author.mention}, you have no notebooks. You should add one first.")
                else:
                    await ctx.send("```" + "\n".join(list(_c.keys())) + "```")
        if option == "create":
            con = sqlite3.connect(db_location)
            cur = con.cursor()
            cur.execute(
                f"SELECT notebooks FROM notes WHERE userid = {ctx.message.author.id}")
            _c = cur.fetchone()
            _c = literal_eval(_c[0])
            con.commit()
            con.close()
            if message is None:
                await ctx.send(f"{ctx.message.author.mention}, you need to provide an argument.")
            else:
                _c[message.strip().lower()] = {}
                execute_sql(
                    f"UPDATE notes SET notebooks = '{_c}' WHERE userid = {ctx.message.author.id}", db_location)
        """


def setup(bot):
    bot.add_cog(Misc(bot))
