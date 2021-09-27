from discord.ext import commands


def guild_whitelist(guild_list):
    def predicate(ctx):
        return ctx.guild.id in guild_list
    return commands.check(predicate)


def member_whitelist(member_list):
    def predicate(ctx):
        return ctx.message.author.id in member_list
    return commands.check(predicate)
