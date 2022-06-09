#!/usr/bin/env python3
from discord.ext import commands
import inspirobot
import re
from random import choice


def setup(bot):
    bot.add_cog(Wisdoms(bot))


class Wisdoms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.wisdom_strings = ['share your wisdom great one', 'what is your wisdom great one']
        self.wisdom_thanks = ['thank you for your wisdom, oh great one', 'thank you great one']
        
        self.wisdom_request = re.compile(r'oh great one, please respond to message (\d+) with your wisdom', re.IGNORECASE)
        self.custom_request = re.compile(r'oh great one, please respond to message (\d+) with your message (.*)', re.IGNORECASE)

        self.patience_proverbs = [
            'Patience is the companion of wisdom.',
            'Patience is the mother of good luck.',
            'Patience is the mother of wisdom.',
            'Without patience, wisdom is a fruitless tree.',
            'With time and patience the mulberry will grow into an olive.',
            'One moment of patience is worth a lifetime of war.',
            'With time and patience, the mulberry leaf becomes a silk gown.',
            'Better a diamond with a flaw than a pebble without.',
            'Without patience, I\'m going to have to eat my vegetables.',
            'The more you wait, the more you have to wait.',
            'The person who waits the longest is the one who is most patient.',
            'The person who removes a mountain begins by carrying away small stones.',
            'Make like a tree and leave.',
            'You can\'t handle the truth!',
            'I want to be alone',
            'I\'m sleeping',
            'I\'m not a tree',
            'The channel name is daily wisdoms for a reason'
        ]

        self.humility_proverbs = [
            'Humility is the companion of wisdom.',
            'Humility is the mother of good luck.',
            'Humility is the mother of wisdom.',
            'Be like bamboo, the higher you grow the deeper you bow.',
            'Arrogance is the enemy of humility.',
            'Arrogance invites danger, humility avoids it.',
            'Through giving thinks, you are given wisdom.',
            'When one gives thanks, the cherry tree grows',
            'Are you feeling lucky, punk?',
            'The more you give, the more you get.',
            'The person who gives the most is the one who receives the most.',
            'Of all the gin joints in all the towns in all the world, she walks into mine.',
            'You talkin\' to me?',
            'What we\'ve got here is failure to communicate.'
        ]

        self.user_thanked = {}
        self.user_last_request = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        # Check if the lower case message content is in 
        if message.content.lower() in self.wisdom_strings:
            # users aren't allowed to request wisdom more than once every five minutes
            if message.author.id not in self.user_last_request or (message.created_at - self.user_last_request[message.author.id]).seconds > 300:
                if message.author.id not in self.user_thanked or self.user_thanked[message.author.id]:
                    self.user_thanked[message.author.id] = False
                    self.user_last_request[message.author.id] = message.created_at
                    wisdom = inspirobot.generate()
                    await message.channel.send(wisdom.url)
                else:
                    proverb = choice(self.humility_proverbs)
                    await message.reply(f'You didn\'t thank me for my last wisdom, young {message.author.mention}. A wise, ancient proverb says "{proverb}"')
            else:
                proverb = choice(self.patience_proverbs)
                await message.reply(f'Have patience, young {message.author.mention}. A wise, ancient proverb says "{proverb}"')

        elif message.content.lower() in self.wisdom_thanks:
            self.user_thanked[message.author.id] = True
            
            # add "n" and "p" regional characters to the message followed by a kissing winky face
            await message.add_reaction('🇳')
            await message.add_reaction('🇵')
            await message.add_reaction('😘')

        elif match := self.wisdom_request.match(message.content):
            # get the message id from the match
            message_id = match.group(1)

            await message.channel.send(f'I will try to find that message for you, young {message.author.mention}')
            message_found = False

            # Iterate over every channel in every server to try and find the message
            for server in self.bot.guilds:
                for channel in server.channels:
                    try:
                        other_message = await channel.fetch_message(message_id)
                        wisdom = inspirobot.generate()
                        await other_message.reply(wisdom.url)
                        message_found = True
                        break
                    except Exception:
                        continue

            if not message_found:
                await message.reply(f'I couldn\'t find that message, young {message.author.mention}')
            else:
                await message.reply(f'It is done, young {message.author.mention}.')

        elif match := self.custom_request.match(message.content):
            # get the message id from the match
            message_id = match.group(1)

            # get the custom message from the match
            custom_message = match.group(2)

            await message.channel.send(f'I will try to find that message for you, young {message.author.mention}')
            message_found = False

            # Iterate over every channel in every server to try and find the message
            for server in self.bot.guilds:
                for channel in server.channels:
                    try:
                        other_message = await channel.fetch_message(message_id)
                        await other_message.reply(custom_message)
                        message_found = True
                        break
                    except Exception:
                        continue

            if not message_found:
                await message.reply(f'I couldn\'t find that message, young {message.author.mention}')
            else:
                await message.reply(f'It is done, young {message.author.mention}.')