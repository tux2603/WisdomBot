# This cog will gather and save training data for the automated AI model
from discord.ext import commands
from discord import Member
import csv
import os

async def setup(bot):
    await bot.add_cog(Train(bot))


class Train(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # TODO: I think these would be better used in postprocessing instead of preprocessing
        self._no_content_messages = [
            '**[REDACTED]**',
            '**[CENSORED]**',
            '...something that I will not say',
            '...something that I will not repeat',
            'probably nothing',
            'some meme or file that I can\'t read because I am a bot',
            'something that I can\'t read because I am a bot',
            'a meme or file that I can\'t read because I am a bot',
            'nothing at all',
            ':crickets:',
            'a meme that I will not share',
            'a meme, but I will not share it',
            'a meme, but I have no way of making memes',
            'a meme, but I am not a meme bot',
            'a meme, but I am not a meme machine',
            'something that is inappropriate for the present audience',
        ]

    async def get_channel_messages(self, channel):
        messages = []
        async for message in channel.history(limit=None):
            messages.append(message)
        return messages

    async def save_message_data_csv(self, messages, filename):
        # check to make sure that the data directory exists, and if not, create it
        if not os.path.exists('data'):
            os.makedirs('data')
        
        # message data will be saved in the following format:
        # message id, guild name, channel name, timestamp, user id, user name, user nickname, message content, and message id of the message that was replied to
        # Make sure the messages are sorted from oldest to newest
        messages.sort(key=lambda message: message.created_at)

        with open(os.path.join('data', filename), 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['message id', 'guild name', 'channel name', 'timestamp', 'user id', 'user name', 'user nickname', 'message content', 'reply id'])
            for message in messages:
                try:
                    message_data = [message.id, message.guild.name, message.channel.name, message.created_at, message.author.id, message.author.name]

                    # Check to see if the user has a nickname, otherwise use their username
                    if type(message.author) is Member and message.author.nick is not None:
                        message_data.append(message.author.nick)
                    else:
                        message_data.append(message.author.name)

                    # Check to see if there is any content in the message
                    if message.content is not None:
                        message_data.append(message.content)
                    else:
                        message_data.append('')

                    # Check to see if the message is a reply to another message
                    if message.reference is not None:
                        message_data.append(message.reference.message_id)
                    else:
                        message_data.append('')

                    writer.writerow(message_data)
                except Exception as e:
                    print(f'Failed to write message {message.id} to data/{filename}')
                    print(f'  Error: {e}')

        print(f'Wrote {len(messages)} messages to data/{filename}')
        
    @commands.command()
    async def gather_channel_data(self, ctx):
        await ctx.send(f'Gathering training data from {ctx.channel.name}...')
        messages = await self.get_channel_messages(ctx.channel)
        await self.save_message_data_csv(messages, f'{ctx.guild.name}_{ctx.channel.name}.csv')
        await ctx.send('Done')

    @commands.command()
    async def gather_guild_data(self, ctx):
        await ctx.send(f'Gathering training data from {ctx.guild.name}...')
        for channel in ctx.guild.text_channels:
            print(f'Gathering training data from {channel.name}...')
            messages = await self.get_channel_messages(channel)
            if messages:
                await self.save_message_data_csv(messages, f'{ctx.guild.name}_{channel.name}.csv')
        await ctx.send('Done')

    @commands.command()
    async def gather_all_data(self, ctx):
        await ctx.send('Gathering training data from all channels on all servers...')
        for guild in self.bot.guilds:
            await ctx.send(f'Gathering training data from {guild.name}...')
            for channel in guild.text_channels:
                try:
                    print(f'Gathering training data from {channel.name}...')
                    messages = await self.get_channel_messages(channel)
                    if messages:
                        await self.save_message_data_csv(messages, f'{guild.name}_{channel.name}.csv')
                except Exception as e:
                    print(f'Failed to gather training data from {channel.name}')
                    print(f'  Error: {e}')
        await ctx.send('Done')