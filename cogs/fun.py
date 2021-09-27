import re
import string
from io import BytesIO
from random import choice, randint

import requests
from discord import File, Member
from discord.ext import commands
try:
    from PIL import Image
except ModuleNotFoundError:
    import Image


def merge_dices(image1_url, image2_url):
    image1 = Image.open(requests.get(image1_url, stream=True).raw)
    image2 = Image.open(requests.get(image2_url, stream=True).raw)
    # resize, first image
    image1 = image1.resize((64, 64))
    image2 = image2.resize((64, 64))
    image1_size = image1.size
    image2_size = image2.size
    new_image = Image.new(
        'RGBA', (2*image1_size[0], image1_size[1]), (250, 250, 250, 0))
    new_image.paste(image1, (0, 0))
    new_image.paste(image2, (image1_size[0], 0))
    #new_image.save("images/merged_image.jpg", "JPEG")
    return new_image


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.digits = {"0": "zero", "1": "one", "2": "two", "3": "three",
                       "4": "four", "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"}
        self.names = ["Hugh Jass", "Mike Hawk", "Ben Dover",
                      "Dixie Normous", "Barry McKockiner"]

    @commands.command()
    async def waifu(self, ctx):
        random_percent = randint(0, 100)
        await ctx.send(f"{ctx.message.author.mention} is {random_percent}% waifu.. yikes")

    @commands.command()
    async def gamer(self, ctx):
        random_percent = randint(0, 100)
        await ctx.send(f"{ctx.message.author.mention} is {random_percent}% epicgamer :sunglasses:")

    @commands.command()
    async def gay(self, ctx):
        random_percent = randint(0, 100)
        await ctx.send(f"{ctx.message.author.mention} is {random_percent}% gay 🏳️‍🌈")

    @commands.command()
    async def simp(self, ctx, member: Member = None):
        random_percent = randint(0, 100)
        if member is not None and member != ctx.message.author:
            tag = member.mention
        elif member == ctx.message.author:
            tag = "your mom"
        else:
            tag = "no one"
        await ctx.send(f"{ctx.message.author.mention} is {random_percent}% simping for {tag}.. yikes")

    @commands.command(name="8ball")
    async def _8ball(self, ctx, *, message=None):
        options = ["it is certain", "looking good", "outlook good", "you may rely on it",
                   "ask again later", "concentrate and ask again", "my reply is no", "my sources say no"]
        random_choice = choice(options)
        if message == None:
            await ctx.send(":8ball: What are you asking the 8ball?")
        else:
            await ctx.send(f":8ball: {random_choice}")

    @commands.command()
    async def imagine(self, ctx, *, message):
        await ctx.send(f"{ctx.message.author.mention} is trying really hard to imagine **{message}** 😳😳")

    @commands.command()
    async def spoiler(self, ctx, * message):
        if message is not None:
            reply = ""
            for word in message:
                for character in word:
                    reply += f"||{character}||"
            await ctx.send(reply)

    @commands.command()
    async def big(self, ctx, *, message):
        if message is not None:
            _lc = None
            reply = ""
            message_split = re.split(r'(\s+)', message)
            for word in message_split:
                for character in word:
                    # disable multiple consecutive whitespaces
                    if _lc in [" ", None] and _lc == character:
                        continue
                    if character in string.ascii_letters:
                        character = character.lower()
                        reply += f":regional_indicator_{character}:"
                    elif character in self.digits:
                        reply += f":{self.digits[character]}:"
                    elif character in [" ", None]:
                        reply += "   "
                    _lc = character

            await ctx.send(reply)

    @commands.command(aliases=["coin"])
    async def coinflip(self, ctx):
        _choice = choice(["heads", "tails"])
        await ctx.send(f"{ctx.message.author.mention} flipped a coin, and it landed on **{_choice}**")

    @commands.command()
    async def dice(self, ctx, member: Member = None):
        p1_name = ctx.message.author.name
        if member is not None:
            p2_name = member.name
        else:
            p2_name = choice(self.names)
        win_p1, win_p2 = False, False
        # Roll player 1 dice
        p1 = []
        done = 0
        while done < 2:
            x = randint(1, 6)
            p1.append(x)
            done += 1
        # Roll player 2 dice
        p2 = []
        done = 0
        while done < 2:
            x = randint(1, 6)
            p2.append(x)
            done += 1
        # Decide winner
        sum1 = p1[0] + p1[1]
        sum2 = p2[0] + p2[1]
        if sum1 > sum2 or sum1 == 2:
            win_p1 = True
        elif sum2 > sum1 or sum2 == 2:
            win_p2 = True
        elif sum1 == sum2:
            win_p1 = win_p2 = True

        # Get image urls
        base_url = "https://www.random.org/dice/dice"  # num.png
        p1_urls, p2_urls = [], []
        for dice in p1:
            p1_urls.append(f"{base_url}{dice}.png")
        for dice in p2:
            p2_urls.append(f"{base_url}{dice}.png")

        p1_merged = merge_dices(p1_urls[0], p1_urls[1])
        p2_merged = merge_dices(p2_urls[0], p2_urls[1])

        # Sending out
        # p1 out
        message_1 = f"**{p1_name}** rolling..\n*({p1[0]} {p1[1]})*"
        await ctx.send(message_1)
        # p1 image out
        with BytesIO() as image_binary:
            p1_merged.save(image_binary, "PNG")
            image_binary.seek(0)
            await ctx.send(file=File(fp=image_binary, filename="player1_rolls.png"))
        # p2 out
        message_2 = f"**{p2_name}** rolling..\n*({p2[0]} {p2[1]})*"
        await ctx.send(message_2)
        # p2 image out
        with BytesIO() as image_binary:
            p2_merged.save(image_binary, "PNG")
            image_binary.seek(0)
            await ctx.send(file=File(fp=image_binary, filename="player2_rolls.png"))

        if win_p1 and win_p2:
            await ctx.send(f"**{p1_name}** and **{p2_name}** tied 😐")
        elif win_p1 and not win_p2:
            await ctx.send(f"**{p1_name}** wins 🥳")
        elif win_p2 and not win_p1:
            await ctx.send(f"**{p2_name}** wins 🥳")


def setup(bot):
    bot.add_cog(Fun(bot))
