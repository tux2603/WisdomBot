#!/usr/bin/env python3
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
from Cogs import *
import asyncio
import sys
from getopt import getopt

# Get command line arguments
opts, args = getopt(sys.argv[1:], '', ['beta'])
flags = [opt[0] for opt in opts if not opt[1]]

# Load environment variables
load_dotenv()

# Set up bot
if '--beta' in flags:
    TOKEN = os.getenv('DISCORD_BETA_TOKEN')
    bot = commands.Bot(intents=discord.Intents.all(), command_prefix='-')
else:
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
    if '--beta' in flags:
        print('Starting bot in beta testing mode (prefix: -)')
    else:
        print('Starting bot in production mode (prefix: ඞ)')
        
    asyncio.run(main())
