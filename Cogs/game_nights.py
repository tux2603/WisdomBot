#!/usr/bin/env python3
from discord.ext import commands
from discord import app_commands, Interaction, TextChannel, Role, Permissions
import os
import tomlkit
from typing import Literal


async def setup(bot):
    await bot.add_cog(GameNights(bot))


class GuildSettings:
    ''' Per Guild Game Night Settings
            Data class used to store the settings for each guild that uses this cog.
            It is used to store the following settings:

            - Game Night Announcement Channel ID (Must be specified, cog is inactive for this guild if not specified)
            - Game Night Vote Channel ID (Default None, uses announcement channel if not specified)
            - Game Night Announcement Role ID (Default None, no role pinged if not specified)
            - Game Night Vote Role ID (Default None, uses announcement role if not specified)
            - Game Night Time (Default None, requires manual trigger if not specified)
            - Game Night Vote Time (Default None, requires manual trigger if not specified)
            - Game Night Announcement Time (Default None, requires manual trigger if not specified)
            - Game Night Max Votes (Default 3, must be greater than 0. If set to 0 an unlimited number of votes can be cast)
            - Suggestion Retain Threshold (Default 2, if set to a negative number no suggestions will be retained)
    '''
    def __init__(self, announcement_channel_id=None, vote_channel_id=None, announcement_role_id=None, vote_role_id=None, game_night_time=None, vote_time=None, announcement_time=None, max_votes=3, retain_threshold=2):
        self.announcement_channel_id = announcement_channel_id
        self.vote_channel_id = vote_channel_id
        self.announcement_role_id = announcement_role_id
        self.vote_role_id = vote_role_id
        self.game_night_time = game_night_time
        self.vote_time = vote_time
        self.announcement_time = announcement_time
        self.max_votes = max_votes
        self.retain_threshold = retain_threshold
        self.is_active = announcement_channel_id is not None

    # Used to convert the class to a dictionary
    def __iter__(self):
        if self.announcement_channel_id is not None:
            yield 'announcement_channel_id', self.announcement_channel_id
        if self.vote_channel_id is not None:
            yield 'vote_channel_id', self.vote_channel_id
        if self.announcement_role_id is not None:
            yield 'announcement_role_id', self.announcement_role_id
        if self.vote_role_id is not None:
            yield 'vote_role_id', self.vote_role_id
        if self.game_night_time is not None:
            yield 'game_night_time', self.game_night_time
        if self.vote_time is not None:
            yield 'vote_time', self.vote_time
        if self.announcement_time is not None:
            yield 'announcement_time', self.announcement_time
        if self.max_votes is not None:
            yield 'max_votes', self.max_votes
        if self.retain_threshold is not None:
            yield 'retain_threshold', self.retain_threshold
        # Is active is based on the announcement channel ID, so it is not needed



class GameNights(commands.Cog):
    ''' Game Nights
            This cog is for managing weekly game nights, and when fully implemented will
            have the following features:

            - A command to set the game night announcement and vote channel
            - A command to set the game night time (probably using cron style syntax)
            - A command to set the game night vote post time (probably using cron style syntax)
            - A command to set the game night vote post end/announcement time (probably using cron style syntax)
            - A command to suggest a game to be played
            - A command to set a role to be pinged for game night announcements
            - A command to set the max number of votes a user can make
            - A command to set the number of votes required for a suggestion to be retained for the next vote
            - A command to clear the suggestion list
            - A help command to explain how to use the cog

            All of these settings will be saved in a TOML file, will be loaded on start-up, and saved whenever they are changed.
            
            Votes will be taken using discord interaction buttons to prevent vote manipulation and will be saved in a CSV file, one file per server.

            Suggested games will be saved in a plain text file, one file per server, one suggestion per line.
    '''

    admin_group = app_commands.Group(name='game-night-admin', description='Admin commands for game nights', default_permissions=Permissions(administrator=True))

    def __init__(self, bot):
        self.bot = bot

        # If the directories used by this cog do not exist, create them
        if not os.path.exists('game_nights'):
            os.makedirs('game_nights')

        if not os.path.exists(os.path.join('game_nights', 'votes')):
            os.makedirs(os.path.join('game_nights', 'votes'))

        if not os.path.exists(os.path.join('game_nights', 'suggestions')):
            os.makedirs(os.path.join('game_nights', 'suggestions'))

        # Settings are indexed by guild ID
        self._settings = {}
        self._suggestions = {}

        # Load state from file
        self._load_settings()
        self._load_suggestions()

        # TODO: Load votes from file


    def __del__(self):
        # Save everything to file
        self._save_settings()
        self._save_suggestions()
        # self._save_votes()



    ##########################################################################
    ######                STATE SAVE AND RESTORE METHODS                ######
    ##########################################################################

    def _load_settings(self):
        ''' Load settings from file '''
        if not os.path.exists(os.path.join('game_nights', 'settings.toml')):
            self._settings = {}
            self._save_settings()
            return

        with open(os.path.join('game_nights', 'settings.toml'), 'r') as f:
            settings = tomlkit.parse(f.read())

        for guild_id, guild_settings in settings.items():
            self._settings[int(guild_id)] = GuildSettings(**guild_settings)


    def _save_settings(self):
        ''' Save settings to file '''
        settings = {str(guild_id): dict(guild_settings) for guild_id, guild_settings in self._settings.items()}
        with open(os.path.join('game_nights', 'settings.toml'), 'w') as f:
            f.write(tomlkit.dumps(settings))


    def _load_suggestions(self):
        ''' Load suggestions from file '''
        # Suggestions are stored in files named game_nights/suggestions/<guild_id>.txt

        # Iterate over all files in the suggestions directory
        for filename in os.listdir(os.path.join('game_nights', 'suggestions')):
            # Skip non-text files
            if not filename.endswith('.txt'):
                continue

            # Get the guild ID from the filename
            guild_id = int(filename[:-4])

            # Load the suggestions for this guild
            with open(os.path.join('game_nights', 'suggestions', filename), 'r') as f:
                self._suggestions[guild_id] = [line.strip() for line in f.readlines()]


    def _save_suggestions(self):
        ''' Save suggestions to file '''
        # Suggestions are stored in files named game_nights/suggestions/<guild_id>.txt
        for guild_id, suggestions in self._suggestions.items():
            with open(os.path.join('game_nights', 'suggestions', f'{guild_id}.txt'), 'w') as f:
                for suggestion in suggestions:
                    f.write(f'{suggestion}\n')


    def _load_votes(self):
        ''' Load votes from file '''
        raise NotImplementedError('This method has not been implemented yet.')


    def _save_votes(self):
        ''' Save votes to file '''
        raise NotImplementedError('This method has not been implemented yet.')



    ##########################################################################
    ######                        HELPER METHODS                        ######
    ##########################################################################

    def _init_guild(self, guild):
        ''' Initialize a guild's settings '''
        if guild.id not in self._settings:
            self._settings[guild.id] = GuildSettings()
        
        if guild.id not in self._suggestions:
            self._suggestions[guild.id] = []

        self._save_settings()
        self._save_suggestions()

        # TODO: set up an object to trigger announcements


    async def _send_uninitialized_error(self, interaction):
        ''' Send a message to the user indicating that the guild has not been initialized '''
        await interaction.response.send_message('Game nights have not been set up for this server yet. Please use the `/game-nights set-announcement-channel` command to initialize the bot.', ephemeral=True)


    async def _create_announcement(self, channel, role, suggestions):
        ''' Creates a game night announcement for the given suggestions '''
        # TODO: This will rely on the vote results
        raise NotImplementedError('This method has not been implemented yet.')


    async def _create_vote(self, channel, role, suggestions, max_votes):
        ''' Creates a game night vote for the given suggestions '''

        # We're just going to do a simple reaction based vote for now, so make sure there are no more than 20 suggestions
        if len(suggestions) > 20:
            raise ValueError('Too many suggestions')

        message_text = f'Hello {role.mention if role is not None else "young ones"}! The time has come to collect the votes for the next game night.'
        if max_votes == 0:
            message_text += ' Please select as many of the games listed below as you would like by reacting to this message with the corresponding letter.'
        else:
            message_text += f' Please select up to {max_votes} of the games listed below by reacting to this message with the corresponding letter.'
        message_text += ' When the vote is over, the game with the most votes will be announced. If there is a tie, I will consult the ancient scrolls to determine the winner.'
        message_text += '\n\n**_Your options:_**\n'

        # Generate a list of letter emojis for the reactions
        # :regional_indicator_k: 
        emojis = [chr(0x1F1E6 + i) for i in range(20)]

        # Add the suggestions to the message
        message_text += '\n'.join(f'  {emoji} - {suggestion}' for emoji, suggestion in zip(emojis, suggestions))

        # Send the vote message
        vote_message = await channel.send(message_text)

        # Add the reactions
        for emoji, _ in zip(emojis, suggestions):
            await vote_message.add_reaction(emoji)



    # ##########################################################################
    # ######               ANNOUNCEMENT MANAGEMENT COMMANDS               ######
    # ##########################################################################

    @admin_group.command(name='set-announcement-channel', description='Set the channel to be used for game night announcements')
    @app_commands.describe(channel='The channel to be used for game night announcements')
    async def set_announcement_channel(self, interaction: Interaction, channel: TextChannel) -> None:
        ''' Set the channel to be used for game night announcements '''
        if interaction.guild_id not in self._settings:
            self._init_guild(interaction.guild)

        self._settings[interaction.guild.id].announcement_channel_id = channel.id
        self._save_settings()

        await interaction.response.send_message(f'Announcement channel set to {channel.mention}', ephemeral=True)


    @admin_group.command(name='set-announcement-role', description='Set the role to be pinged for game night announcements')
    @app_commands.describe(role='The role to be pinged for game night announcements')
    async def set_announcement_role(self, interaction: Interaction, role: Role) -> None:
        ''' Set the role to be pinged for game night announcements '''
        if interaction.guild_id not in self._settings:
            
            return

        self._settings[interaction.guild.id].announcement_role_id = role.id
        self._save_settings()

        await interaction.response.send_message(f'Announcement role set to {role.mention}', ephemeral=True)

    
    # TODO: Make this an actual announcement and make the code DRY
    @admin_group.command(name='trigger-announcement', description='Manually triggers an announcement for the next game night')
    async def trigger_announcement(self, interaction: Interaction) -> None:
        ''' Manually trigger an announcement for the next game night '''
        if interaction.guild_id not in self._settings:
            await self._send_uninitialized_error(interaction)
            return

        # Get the channel ID for the announcement channel
        announcement_channel_id = self._settings[interaction.guild.id].announcement_channel_id

        # Get the role ID for the announcement role
        announcement_role_id = self._settings[interaction.guild.id].announcement_role_id

        if announcement_role_id is None:
            message_text = 'This is a manually triggered announcement for the next game night. Please join us at 8pm EST!'
        else:
            announcement_role = interaction.guild.get_role(announcement_role_id)
            message_text = f'This is a manually triggered announcement for the next game night. Please join us at 8pm EST! {announcement_role.mention}'

        # Send the announcement message
        announcement_channel = interaction.guild.get_channel(announcement_channel_id)
        await announcement_channel.send(message_text)

        await interaction.response.send_message('Announcement triggered', ephemeral=True)



    ##########################################################################
    ######                   VOTE MANAGEMENT COMMANDS                   ######
    ##########################################################################

    @admin_group.command(name='set-vote-channel', description='Set the channel to be used for game night votes')
    @app_commands.describe(channel='The channel to be used for game night votes')
    async def set_vote_channel(self, interaction: Interaction, channel: TextChannel) -> None:
        ''' Set the channel to be used for game night votes '''
        if interaction.guild_id not in self._settings:
            await self._send_uninitialized_error(interaction)
            return

        self._settings[interaction.guild.id].vote_channel_id = channel.id
        self._save_settings()

        await interaction.response.send_message(f'Vote channel set to {channel.mention}', ephemeral=True)


    @admin_group.command(name='set-vote-role', description='Set the role to be pinged for game night votes')
    @app_commands.describe(role='The role to be pinged for game night votes')
    async def set_vote_role(self, interaction: Interaction, role: Role) -> None:
        ''' Set the role to be pinged for game night votes '''
        if interaction.guild_id not in self._settings:
            await self._send_uninitialized_error(interaction)
            return

        self._settings[interaction.guild.id].vote_role_id = role.id
        self._save_settings()

        await interaction.response.send_message(f'Vote role set to {role.mention}', ephemeral=True)


    @admin_group.command(name='trigger-vote', description='Manually triggers a vote for the next game night')
    async def trigger_vote(self, interaction: Interaction) -> None:
        ''' Manually a vote for the next game night '''
        if interaction.guild_id not in self._settings:
            await self._send_uninitialized_error(interaction)
            return

        # Get the channel ID for the vote channel
        vote_channel_id = self._settings[interaction.guild.id].vote_channel_id
        if vote_channel_id is None:
            vote_channel_id = self._settings[interaction.guild.id].announcement_channel_id
        vote_channel = interaction.guild.get_channel(vote_channel_id)

        # Get the role ID for the vote role
        vote_role_id = self._settings[interaction.guild.id].vote_role_id
        vote_role = interaction.guild.get_role(vote_role_id)

        suggestions = self._suggestions[interaction.guild.id]
        max_votes = self._settings[interaction.guild.id].max_votes

        await self._create_vote(vote_channel, vote_role, suggestions, max_votes)

        await interaction.response.send_message('Vote triggered', ephemeral=True)



    ##########################################################################
    ######                SUGGESTION MANAGEMENT COMMANDS                ######
    ##########################################################################

    # TODO Add suggestion time out
    @app_commands.command(name='suggest', description='Suggest a game for the next game night')
    @app_commands.describe(game_name='The name of the game that you want to suggest')
    async def suggest(self, interaction: Interaction, *, game_name: str) -> None:
        ''' Suggest a game for the next game night '''
        if interaction.guild_id not in self._settings:
            await self._send_uninitialized_error(interaction)
            return

        if interaction.guild_id not in self._suggestions:
            self._suggestions[interaction.guild.id] = []

        self._suggestions[interaction.guild.id].append(game_name)
        self._save_suggestions()

        await interaction.response.send_message(f'Your suggestion to play "{game_name}" has been received, young {interaction.user.mention}', ephemeral=True)

    
    @admin_group.command(name='list-suggestions', description='List all of the suggestions for the next game night')
    async def list_suggestions(self, interaction: Interaction) -> None:
        ''' List all of the suggestions for the next game night '''
        if interaction.guild_id not in self._settings:
            await self._send_uninitialized_error(interaction)
            return

        if interaction.guild_id not in self._suggestions or len(self._suggestions[interaction.guild.id]) == 0:
            await interaction.response.send_message('There are no suggestions for the next game night', ephemeral=True)
            return

        suggestion_list = '\n'.join(f'  - {suggestion}' for suggestion in self._suggestions[interaction.guild.id])
        await interaction.response.send_message(f'The following suggestions have been received:\n{suggestion_list}', ephemeral=True)

    
    @admin_group.command(name='clear-suggestions', description='Clear all of the suggestions for the next game night')
    async def clear_suggestions(self, interaction: Interaction) -> None:
        ''' Clear all of the suggestions for the next game night '''
        if interaction.guild_id not in self._settings:
            await self._send_uninitialized_error(interaction)
            return

        if interaction.guild_id not in self._suggestions or len(self._suggestions[interaction.guild.id]) == 0:
            await interaction.response.send_message('There are already no suggestions for the next game night', ephemeral=True)
            return

        self._suggestions[interaction.guild.id] = []
        self._save_suggestions()

        await interaction.response.send_message('All suggestions have been cleared', ephemeral=True)



