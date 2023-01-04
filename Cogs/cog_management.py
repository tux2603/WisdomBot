#!/usr/bin/env python3
from discord import app_commands, Interaction
from discord.ext import commands
import os


async def setup(bot):
    await bot.add_cog(CogManagement(bot))


class CogManagement(commands.GroupCog, name='cog-management', description='Commands to manage cogs. Don\'t unload the cog-management cog!'):
    # TODO: See if there's any way to use the autocomplete feature for the cog names
    def __init__(self, bot):
        self.bot = bot


    @app_commands.command(name='reload', description='Reloads a cog')
    @app_commands.default_permissions(administrator=True)
    async def reload_cog(self, interaction: Interaction, cog_name: str) -> None:
        await interaction.response.send_message(f'Reloading cog {cog_name}...')

        # Check if the cog exists
        if not os.path.exists(os.path.join('Cogs', f'{cog_name}.py')):
            await interaction.edit_original_response(content=f'Cog {cog_name} does not exist')
            return

        try:
            await self.bot.reload_extension(f'Cogs.{cog_name}')
            await interaction.edit_original_response(content=f'Cog {cog_name} reloaded')
        except Exception as e:
            print(f'Error reloading cog {cog_name}: {e}')
            await interaction.edit_original_response(content=f'Error reloading cog {cog_name}: {e}')


    @app_commands.command(name='load', description='Loads a cog')
    @app_commands.default_permissions(administrator=True)
    async def load_cog(self, interaction: Interaction, cog_name: str) -> None:
        await interaction.response.send_message(f'Loading cog {cog_name}...')

        # Check if the cog exists
        if not os.path.exists(os.path.join('Cogs', f'{cog_name}.py')):
            await interaction.edit_original_response(content=f'Cog {cog_name} does not exist')
            return

        try:
            await self.bot.load_extension(f'Cogs.{cog_name}')
            await interaction.edit_original_response(content=f'Cog {cog_name} loaded')
        except Exception as e:
            print(f'Error loading cog {cog_name}: {e}')
            await interaction.edit_original_response(content=f'Error loading cog {cog_name}: {e}')

    
    @app_commands.command(name='unload', description='Unloads a cog')
    @app_commands.default_permissions(administrator=True)
    async def unload_cog(self, interaction: Interaction, cog_name: str) -> None:
        await interaction.response.send_message(f'Unloading cog {cog_name}...')

        # Check if the cog exists
        if not os.path.exists(os.path.join('Cogs', f'{cog_name}.py')):
            await interaction.edit_original_response(content=f'Cog {cog_name} does not exist')
            return

        try:
            await self.bot.unload_extension(f'Cogs.{cog_name}')
            await interaction.edit_original_response(content=f'Cog {cog_name} unloaded')
        except Exception as e:
            print(f'Error unloading cog {cog_name}: {e}')
            await interaction.edit_original_response(content=f'Error unloading cog {cog_name}: {e}')