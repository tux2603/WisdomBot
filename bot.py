#!/usr/bin/env python3
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
from Cogs import *
import asyncio


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(intents=discord.Intents.all(), command_prefix='ඞ')


@bot.event
async def on_ready():
    print(f'\n\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="over the world from my sanctuary in the clouds"))

async def main():
    async with bot:
        for file in os.listdir('Cogs'):
            if not file.startswith('__') and file.endswith('.py'):
                try:
                    print(f'Loading extension {file[:-3]}')
                    await bot.load_extension(f'Cogs.{file[:-3]}')
                    print('  ...Done')
                except commands.errors.NoEntryPointError:
                    print(f'  ...Failed to load extension {file[:-3]}')
        await bot.start(TOKEN)

if __name__ == '__main__':
    print('Starting bot')
    asyncio.run(main())
