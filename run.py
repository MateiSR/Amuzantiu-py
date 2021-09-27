from amuzantiu import *
from discord.ext import commands
import json
import pathlib

cwd = pathlib.Path().absolute()
with open(cwd/"config.json") as json_file:
    config = json.load(json_file)

# Make sure to run the bot in the same directory that amuzantiu.py is in

c_m = config["modules"]
c_m.append("help")
client = Amuzantiu(command_prefix=config["prefix"],
                   cogs=c_m,
                   status="Coloana Dragonului")

"""
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"you've been scorched :fire: `{round(error.retry_after, 2)}s` :fire:")
    elif isinstance(error, commands.NSFWChannelRequired):
        await ctx.send("Can only be used in NSFW channels.")
    else:
        print(f"[DEBUG] {error}")
"""

client.run(config["TOKEN"])
