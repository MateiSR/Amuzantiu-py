import json
import os
from random import choice
from time import sleep
import discord
from discord.ext import commands, tasks
from gtts import gTTS
from cogs._decorators import member_whitelist
import pathlib

cwd = pathlib.Path().absolute()
with open(cwd/"cogs/config/whitelist.json") as json_file:
    whitelist = json.load(json_file)


class Abuse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_disconnect = []
        self.active_mute = []
        self.active_deafen = []
        self.active_mute_deafen = []

    @tasks.loop()
    async def force_disconnect(self):
        for member in self.active_disconnect:
            status = member.voice
            if status is not None:
                await discord.Member.edit(member, voice_channel=None, reason=None)

    @tasks.loop()
    async def force_mute(self):
        for member in self.active_mute:
            status = member.voice
            if not status:
                status = member.voice
                continue
            if not status.mute:
                await discord.Member.edit(member, mute=True, reason=None)

    @tasks.loop()
    async def force_deafen(self):
        for member in self.active_deafen:
            status = member.voice
            if not status:
                status = member.voice
                continue
            if not status.deaf:
                await discord.Member.edit(member, deafen=True, reason=None)

    @tasks.loop()
    async def force_mute_deafen(self):
        for member in self.active_mute_deafen:
            status = member.voice
            if not status:
                status = member.voice
                continue
            if not status.deaf or not status.mute:
                await discord.Member.edit(member, deafen=True, mute=True, reason=None)

    @commands.command()
    @member_whitelist(whitelist["members"]["abuse"])
    async def moveall(self, ctx):
        author = ctx.message.author
        channels = ctx.message.author.guild.channels
        if author.voice is None:
            return
        else:
            author_voice = ctx.message.author.voice.channel
            for channel in channels:
                if type(channel) == discord.channel.VoiceChannel:
                    for member in channel.members:
                        await discord.Member.edit(member, voice_channel=author_voice, reason=None)

    @commands.command()
    @member_whitelist(whitelist["members"]["abuse"])
    async def mute(self, ctx, member: discord.Member = None):
        if member not in self.active_mute:
            self.active_mute.append(member)
            await ctx.message.add_reaction("✅")
            try:
                self.force_mute.start()
            except RuntimeError:
                pass
        elif member in self.active_mute:
            self.active_mute.remove(member)
            await ctx.message.add_reaction("⛔")
            await discord.Member.edit(member, mute=False, reason=None)

    @commands.command()
    @member_whitelist(whitelist["members"]["abuse"])
    async def deafen(self, ctx, member: discord.Member = None):
        if member not in self.active_deafen:
            self.active_deafen.append(member)
            await ctx.message.add_reaction("✅")
            try:
                self.force_deafen.start()
            except RuntimeError:
                pass
        elif member in self.active_deafen:
            self.active_deafen.remove(member)
            await ctx.message.add_reaction("⛔")
            await discord.Member.edit(member, deafen=False, reason=None)

    @commands.command(aliases=['torture'])
    @member_whitelist(whitelist["members"]["abuse"])
    async def punish(self, ctx, member: discord.Member = None):
        if member not in self.active_mute_deafen:
            self.active_mute_deafen.append(member)
            await ctx.message.add_reaction("✅")
            try:
                self.force_mute_deafen.start()
            except RuntimeError:
                pass
        elif member in self.active_mute_deafen:
            self.active_mute_deafen.remove(member)
            await ctx.message.add_reaction("⛔")
            await discord.Member.edit(member, mute=False, deafen=False, reason=None)

    @commands.command()
    @member_whitelist(whitelist["members"]["abuse"])
    async def multispam(self, ctx, *, message="the time for funny has come!"):
        for channel in ctx.message.author.guild.channels:
            if channel.type == discord.ChannelType.text:
                await channel.send(message)

    @commands.command()
    @member_whitelist(whitelist["members"]["abuse"])
    async def disconnect(self, ctx, member: discord.Member = None):
        if member not in self.active_disconnect:
            self.active_disconnect.append(member)
            await ctx.message.add_reaction("✅")
            try:
                self.force_disconnect.start()
            except RuntimeError:
                pass
        elif member in self.active_disconnect:
            self.active_disconnect.remove(member)
            await ctx.message.add_reaction("⛔")

    @commands.command()
    @member_whitelist(whitelist["members"]["abuse"])
    async def massacre(self, ctx):
        author = ctx.message.author
        channel = author.voice.channel
        members = channel.members
        for member in members:
            await discord.Member.edit(member, voice_channel=None, reason=None)

    # Messy code aswell

    @commands.command(aliases=["carousel"])
    @member_whitelist(whitelist["members"]["abuse"])
    async def fastmove(self, ctx, member: discord.Member = None):
        fastmove_start = None
        fastmove_count = 0
        if member.voice is None:
            return
        for channel in ctx.message.author.guild.channels:
            if member.voice is None:
                break
            if fastmove_start is None:
                fastmove_start = member.voice.channel
            if channel.type == discord.ChannelType.voice:
                fastmove_count += 1
                if fastmove_count == 6:
                    try:
                        await discord.Member.edit(member, voice_channel=fastmove_start, reason=None)
                        break
                    except:
                        break
                await discord.Member.edit(member, voice_channel=channel, reason=None)


def setup(bot):
    bot.add_cog(Abuse(bot))
