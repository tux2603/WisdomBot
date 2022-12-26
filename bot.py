#!/usr/bin/env python3
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
from Cogs import *
import asyncio


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
client = commands.Bot(intents=discord.Intents.all(), command_prefix='ඞ')


@client.event
async def on_ready():
    print(f'\n\nLogged in as: {client.user.name} - {client.user.id}\nVersion: {discord.__version__}\n')

async def main():
    async with client:
        for file in os.listdir('Cogs'):
            if not file.startswith('__') and file.endswith('.py'):
                try:
                    print(f'Loading extension {file[:-3]}')
                    await client.load_extension(f'Cogs.{file[:-3]}')
                    print('  ...Done')
                except commands.errors.NoEntryPointError:
                    print(f'  ...Failed to load extension {file[:-3]}')

        await client.start(TOKEN)

if __name__ == '__main__':
    print('Starting bot')
    asyncio.run(main())
