from discord.ext import commands
import discord


class Amuzantiu(commands.Bot):
    def __init__(self, *, command_prefix, cogs=None, status="& pulling funnies"):
        print("[INFO] Bot is now loading")
        commands.Bot.__init__(self, command_prefix=command_prefix)
        self.cogs_tuple = cogs
        self.status = status

    async def on_ready(self):
        print("[INFO] Bot is now online")
        self.remove_command("help")
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=self.status))
        if len(self.cogs_tuple) != 0 and self.cogs_tuple is not None:
            print(f"[INFO] Loading {len(self.cogs)} cogs")
            for cog in self.cogs_tuple:
                try:
                    self.load_extension(f"cogs.{cog}")
                    print(f"[INFO] Loading cog: {cog}")
                except Exception as e:
                    print(f"[INFO] Could not load cog: {cog}")
                    print(f"[DEBUG] {e}")
        else:
            print("[INFO] No cogs to load")
