#!/usr/bin/env python3
import datetime
from discord.ext import commands
from discord import app_commands, Interaction, TextChannel, Role, Permissions, ButtonStyle
from discord.ui import Button, View
import os
import tomlkit
import csv
import random


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
            - Game Night Max Suggestions (Default 3, must be greater than 0. If set to 0 an unlimited number of suggestions can be made)
            - Suggestion Retain Threshold (Default 2, if set to a negative number no suggestions will be retained)
            - The time that the last vote was started (defaults to the start of the epoch)
    '''
    def __init__(self, announcement_channel_id=None, vote_channel_id=None, announcement_role_id=None, vote_role_id=None, game_night_time=None, vote_time=None, announcement_time=None, max_suggestions=3, retain_threshold=2, last_vote_time=0):
        self.announcement_channel_id = announcement_channel_id
        self.vote_channel_id = vote_channel_id
        self.announcement_role_id = announcement_role_id
        self.vote_role_id = vote_role_id
        self.game_night_time = game_night_time
        self.vote_time = vote_time
        self.announcement_time = announcement_time
        self.max_suggestions = max_suggestions
        self.retain_threshold = retain_threshold
        self.last_vote_time = datetime.datetime.fromtimestamp(last_vote_time)
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
        if self.max_suggestions is not None:
            yield 'max_suggestions', self.max_suggestions
        if self.retain_threshold is not None:
            yield 'retain_threshold', self.retain_threshold
        if self.last_vote_time is not None:
            yield 'last_vote_time', self.last_vote_time.timestamp()
        # Is active is based on the announcement channel ID, so it is not needed



class Suggestion:
    ''' Suggestion for a game night game
            Data class that stores the following information about a suggestion:
            
            - The name of the game suggested
            - The user ID of the user who suggested the game
            - A time stamp of when the suggestion was made

            The class overrides the equality operator to allow for easy comparison of suggestions.
            If the name of the games match, regardless of case, the suggestions are considered equal. 
    '''

    def __init__(self, name, user_id, timestamp):
        self.name = name
        self.user_id = user_id if type(user_id) is int else int(user_id)
        self.timestamp = timestamp

    def __eq__(self, other):
        return self.name.lower() == other.name.lower()

    def __hash__(self) -> int:
        return hash(self.name.lower())

    def __str__(self) -> str:
        return f'{self.name} (Suggested by <@{self.user_id}>)'

    def __repr__(self) -> str:
        return f'{self.name} (Suggested by <@{self.user_id}>)'

    def __iter__(self):
        yield from (self.name, self.user_id, self.timestamp)


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
            - A command to set the max number of suggestions that a user can make per voting period
            - A command to set the number of votes required for a suggestion to be retained for the next vote
            - A command to clear the suggestion list
            - A help command to explain how to use the cog

            All of these settings will be saved in a TOML file, will be loaded on start-up, and saved whenever they are changed.
            
            Votes will be taken using discord interaction buttons to prevent vote manipulation and will be saved in a CSV file, one file per server.

            Suggested games will be saved to a CSV file, one file per server, and will be loaded on start-up and saved whenever they are changed.
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

        # All settings and state data is indexed by guild ID
        self._settings = {}
        self._suggestions = {}
        self._votes = {}
        self._vote_titles = {}
        self._vote_messages = {}

        # Load state from file
        self._load_settings()
        self._load_suggestions()
        self._load_votes()


    def __del__(self):
        # Save everything to file
        self._save_settings()
        self._save_suggestions()
        self._save_votes()



    ##########################################################################
    ######                STATE SAVE AND RESTORE METHODS                ######
    ##########################################################################

    # TODO: Add arguments to the save methods to only save the data for a single guild

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
            # Skip non-csv files
            if not filename.endswith('.csv'):
                continue

            # Get the guild ID from the file name
            guild_id = int(filename[:-4])

            # Load the suggestions for this guild
            with open(os.path.join('game_nights', 'suggestions', filename), 'r') as f:
                # The first row is the header
                reader = csv.reader(f)
                next(reader)
                self._suggestions[guild_id] = {Suggestion(*row) for row in reader}


    def _save_suggestions(self):
        ''' Save suggestions to file '''
        # Suggestions are stored in files named game_nights/suggestions/<guild_id>.txt
        for guild_id, suggestions in self._suggestions.items():
            with open(os.path.join('game_nights', 'suggestions', f'{guild_id}.csv'), 'w') as f:
                writer = csv.writer(f)
                writer.writerow(['name', 'user_id', 'timestamp'])
                for suggestion in suggestions:
                    writer.writerow(list(suggestion))


    def _load_votes(self):
        ''' Load votes from file '''

        for filename in os.listdir(os.path.join('game_nights', 'votes')):
            # csv files are vote data files
            if filename.endswith('.csv'):
                # Get the guild ID from the file name
                guild_id = int(filename[:-4])

                # Load the voting data for this guild
                with open(os.path.join('game_nights', 'votes', filename), 'r') as f:
                    reader = csv.reader(f)

                    # The first row is the header, and contains the list of games that are being voted on
                    self._vote_titles[guild_id] = next(reader)[1:]
                    self._votes[guild_id] = {}

                    for row in reader:
                        self._votes[guild_id][int(row[0])] = [int(vote_count) for vote_count in row[1:]]
            
            # txt files are vote message IDs
            elif filename.endswith('.txt'):
                # Get the guild ID from the file name
                guild_id = int(filename[:-4])

                # Load the vote message ID for this guild
                with open(os.path.join('game_nights', 'votes', filename), 'r') as f:
                    self._vote_messages[guild_id] = [int(line) for line in f.readlines()]


    def _save_votes(self):
        ''' Save votes to file '''
        for guild_id, votes in self._votes.items():
            with open(os.path.join('game_nights', 'votes', f'{guild_id}.csv'), 'w') as f:
                writer = csv.writer(f)

                # Write the header data
                writer.writerow(['user_id', *self._vote_titles[guild_id]])

                # Write the vote data
                for user_id, vote_counts in votes.items():
                    writer.writerow([user_id, *vote_counts])

        for guild_id, message_ids in self._vote_messages.items():
            with open(os.path.join('game_nights', 'votes', f'{guild_id}.txt'), 'w') as f:
                f.write('\n'.join(str(message_id) for message_id in message_ids))



    ##########################################################################
    ######                        HELPER METHODS                        ######
    ##########################################################################

    def _init_guild(self, guild):
        ''' Initialize a guild's settings '''
        if guild.id not in self._settings:
            self._settings[guild.id] = GuildSettings()
        
        if guild.id not in self._suggestions:
            self._suggestions[guild.id] = []

        if guild.id not in self._votes:
            self._votes[guild.id] = {}

        if guild.id not in self._vote_titles:
            self._vote_titles[guild.id] = []

        if guild.id not in self._vote_messages:
            self._vote_messages[guild.id] = []

        self._save_settings()
        self._save_suggestions()
        self._save_votes()

        # TODO: set up an object to trigger announcements


    async def _send_uninitialized_error(self, interaction):
        ''' Send a message to the user indicating that the guild has not been initialized '''
        await interaction.response.send_message('Game nights have not been set up for this server yet. Please use the `/game-nights set-announcement-channel` command to initialize the bot.', ephemeral=True)


    async def _create_announcement(self, channel, role):
        ''' Creates a game night announcement for the given suggestions '''

        # Check to make sure that there is a vote in progress
        if not self._vote_titles[channel.guild.id]:
            return

        # Get a list of results that are tied for first place and choose a random one
        votes = []

        for index, title in enumerate(self._vote_titles[channel.guild.id]):
            votes.append((title, sum(vote[index] for vote in self._votes[channel.guild.id].values())))

        votes.sort(key=lambda vote: vote[1], reverse=True)
        max_votes = votes[0][1]
        tied_games = [vote[0] for vote in votes if vote[1] == max_votes]
        game = random.choice(tied_games)

        # Create and send the announcement
        announcement = f'The vote is over {role.mention if role is not None else "young ones"}! '

        if len(tied_games) > 1:
            announcement += f'There was a tie between {", ".join(tied_games[:-1])}{", " if len(tied_games) > 2 else " "}and {tied_games[-1]}. '
            announcement += f'In order to resolve this tie I have consulted the ancient scrolls, and through their guidance I have selected {game}'
        else:
            announcement += f'There was a clear winner, {game} has been chosen for the game night!'

        await channel.send(announcement)

        # Add all options that are above a certain cutoff back into the suggestions list
        for title, vote_count in votes:
            if vote_count >= self._settings[channel.guild.id].retain_threshold:
                self._suggestions[channel.guild.id].add(Suggestion(title, 0, 0))

        # Replace the vote view messages with a static message showing how many votes each game got
        vote_channel = channel.guild.get_channel(self._settings[channel.guild.id].vote_channel_id)
        first_message_id = self._vote_messages[channel.guild.id][0]
        first_message = await vote_channel.fetch_message(first_message_id)

        # Edit the message to contain the vote results
        await first_message.edit(content='\n'.join(f'- {title} ({total_votes} {"vote" if total_votes == 1 else "votes"})' for title, total_votes in votes), view=None)

        # Delete all the other messages
        for message_id in self._vote_messages[channel.guild.id][1:]:
            message = await vote_channel.fetch_message(message_id)
            await message.delete()

        # Clear all the vote stuff
        self._vote_titles[channel.guild.id] = []
        self._votes[channel.guild.id] = {}
        self._vote_messages[channel.guild.id] = []

        self._save_suggestions()
        self._save_votes()


    async def _create_vote(self, channel, role, suggestions):
        ''' Creates a game night vote for the given suggestions '''

        # Clear the suggestions and transfer them to the vote titles list
        self._vote_titles[channel.guild.id] = [suggestion.name for suggestion in suggestions]
        self._votes[channel.guild.id] = {}
        self._vote_messages[channel.guild.id] = []
        self._suggestions[channel.guild.id] = set()
        self._save_votes()

        # Break the suggestions up into sub lists of 25
        # Discord has a limit of 25 options per message
        suggestion_sublists = [self._vote_titles[channel.guild.id][i:i+25] for i in range(0, len(suggestions), 25)]       

        # TODO: You should probably make this all one message at some point. Doesn't really matter for now though
        await channel.send(f'Hello {role.mention if role is not None else "young ones"}! The time has come to collect the votes for the next game night. Please select up to 3 of the games listed below by reacting to this message with the corresponding letter.')
        await channel.send('When the vote is over, the game with the most votes will be announced. If there is a tie, I will consult the ancient scrolls to determine the winner.')
        await channel.send('**_Your Options:_**')

        # Create a vote message for each sub-list
        for suggestion_sublist in suggestion_sublists:
            view = View(timeout=None)

            for suggestion in suggestion_sublist:
                button = Button(style=ButtonStyle.primary, label=suggestion, custom_id=suggestion)
                button.callback = self._handle_vote
                view.add_item(button)

            view_message = await channel.send(view=view)
            self._vote_messages[channel.guild.id].append(view_message.id)

        # Set the time that the last vote was started
        self._settings[channel.guild.id].last_vote_time = datetime.datetime.now()
        self._save_settings()
        self._save_votes()
        self._save_suggestions()


    async def _handle_vote(self, interaction: Interaction) -> None:
        ''' Handle a vote '''
        # Get the index of the game title in the title list
        title_index = self._vote_titles[interaction.guild_id].index(interaction.data['custom_id'])

        if interaction.user.id not in self._votes[interaction.guild_id]:
            self._votes[interaction.guild_id][interaction.user.id] = [0] * len(self._vote_titles[interaction.guild_id])

        # Toggle the vote
        self._votes[interaction.guild_id][interaction.user.id][title_index] = 1 - self._votes[interaction.guild_id][interaction.user.id][title_index]

        self._save_votes()

        # Check to see if the new value is 1 or 0
        if self._votes[interaction.guild_id][interaction.user.id][title_index] == 1:
            await interaction.response.send_message(f'Thank you young {interaction.user.mention}, your vote for {interaction.data["custom_id"]} has been recorded. Click the button again to remove your vote', ephemeral=True)
        else:
            await interaction.response.send_message(f'I have removed your vote for {interaction.data["custom_id"]}, young {interaction.user.mention}.', ephemeral=True)



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

    
    @admin_group.command(name='trigger-announcement', description='Manually triggers an announcement for the next game night')
    async def trigger_announcement(self, interaction: Interaction) -> None:
        ''' Manually trigger an announcement for the next game night '''
        if interaction.guild_id not in self._settings:
            await self._send_uninitialized_error(interaction)
            return

        # Get the channel ID for the announcement channel
        announcement_channel_id = self._settings[interaction.guild.id].announcement_channel_id
        announcement_channel = interaction.guild.get_channel(announcement_channel_id)

        # Get the role ID for the announcement role
        announcement_role_id = self._settings[interaction.guild.id].announcement_role_id
        announcement_role = interaction.guild.get_role(announcement_role_id)

        await self._create_announcement(announcement_channel, announcement_role)
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

        await self._create_vote(vote_channel, vote_role, suggestions)

        await interaction.response.send_message('Vote triggered', ephemeral=True)


    @admin_group.command(name='list-votes', description='Lists the number of votes for each of the games currently in the running')
    async def list_votes(self, interaction: Interaction) -> None:
        ''' Lists the number of votes for each of the games currently in the running '''

        # Create a list of tuples of each title being voted for and the number of votes it has received
        votes = []

        for index, title in enumerate(self._vote_titles[interaction.guild.id]):
            vote_count = sum(i[index] for i in self._votes[interaction.guild.id].values())
            votes.append((title, vote_count))

        # Sort the list by the number of votes
        votes.sort(key=lambda x: x[1], reverse=True)

        # Create the message text
        message_text = 'Here are the current votes:\n'
        for title, vote_count in votes:
            message_text += f'  - {title}: {vote_count}\n'

        await interaction.response.send_message(message_text, ephemeral=True)


    # TODO: We probably want a command that will somehow re-initialize the vote messages if necessary


    ##########################################################################
    ######                SUGGESTION MANAGEMENT COMMANDS                ######
    ##########################################################################

    @app_commands.command(name='suggest', description='Suggest a game for the next game night')
    @app_commands.describe(game_name='The name of the game that you want to suggest')
    async def suggest(self, interaction: Interaction, *, game_name: str) -> None:
        ''' Suggest a game for the next game night '''
        if interaction.guild_id not in self._settings:
            await self._send_uninitialized_error(interaction)
            return

        if interaction.guild_id not in self._suggestions:
            self._suggestions[interaction.guild.id] = []

        # Check to make sure the user hasn't made too many suggestions already
        num_suggestions = sum(suggestion.user_id == interaction.user.id for suggestion in self._suggestions[interaction.guild.id])

        if num_suggestions >= self._settings[interaction.guild.id].max_suggestions > 0:
            response = f'I am sorry young {interaction.user.mention}, but you have already suggested {num_suggestions} games{"s" if num_suggestions != 1 else ""}. Please wait until after the voting starts to make any more suggestions.'
        else:
            response = f'Your suggestion to play {game_name} has been received, young {interaction.user.mention}'
            self._suggestions[interaction.guild.id].add(Suggestion(game_name, interaction.user.id, interaction.created_at))
            self._save_suggestions()

        await interaction.response.send_message(response, ephemeral=True)

    
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



