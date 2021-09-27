from discord.ext import commands
import discord
import json
import pathlib

cwd = pathlib.Path().absolute()
with open(cwd/"config.json") as json_file:
    config = json.load(json_file)

with open(cwd/"cogs/config/help_menu.json") as json_file:
    help_menu = json.load(json_file)


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(rate="1", per="5")
    async def help(self, ctx, option=None):
        valid_options = config["modules"]
        response = discord.Embed(
            title="Amuzantiu Command List", color=discord.Colour.gold())

        if option is not None:
            option = option.lower().strip()

        if option in valid_options:
            commands = help_menu[option]
            commands_str = ""
            for command in commands:
                commands_str += f"`{command}` "
            response.add_field(name=f"{option} commands", value=commands_str)
        else:
            for option_to_add in valid_options:
                response.add_field(name=option_to_add.capitalize(),
                                   value=f"help {option_to_add}", inline=True)
        await ctx.send(embed=response)


def setup(bot):
    bot.add_cog(Help(bot))
