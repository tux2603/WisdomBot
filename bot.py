#!/usr/bin/env python3
import os

import discord
from discord.ext import commands
from discord_components import DiscordComponents
from dotenv import load_dotenv
from Cogs import *


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='ඞ')


@bot.event
async def on_ready():
    print(f'\n\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')

    DiscordComponents(bot)


if __name__ == '__main__':
    print('Starting bot')
    for file in os.listdir('Cogs'):
        if not file.startswith('__') and file.endswith('.py'):
            try:
                bot.load_extension(f'Cogs.{file[:-3]}')
            except commands.errors.NoEntryPointError:
                pass
    bot.run(TOKEN)
