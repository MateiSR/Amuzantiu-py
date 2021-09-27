from discord.ext import commands
from cogs._decorators import member_whitelist
import pathlib
import json
import textwrap
import io
import traceback
from contextlib import redirect_stdout

cwd = pathlib.Path().absolute()

with open(cwd/"cogs/config/whitelist.json") as json_file:
    whitelist = json.load(json_file)


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    @commands.command()
    @commands.cooldown(rate="1", per="10")
    async def ping(self, ctx):
        ms = round(self.bot.latency * 1000, 1)
        await ctx.send(f"Pong! 😂😂😂😂😂\n*{ms} ms*")

    @commands.command(pass_context=True, hidden=True, name='eval')
    @member_whitelist(whitelist["members"]["utils._eval"])
    async def _eval(self, ctx, *, body: str):
        """Evaluates a code"""

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message
        }

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('\u2705')
            except:
                pass

            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
            else:
                self._last_result = ret
                await ctx.send(f'```py\n{value}{ret}\n```')


def setup(bot):
    bot.add_cog(Utils(bot))
