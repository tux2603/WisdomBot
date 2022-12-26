#!/usr/bin/env python3
from discord.ext import commands


async def setup(bot):
    await bot.add_cog(Ping(bot))


class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        await ctx.send(f'{latency} ms')