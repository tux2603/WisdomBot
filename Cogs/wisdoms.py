#!/usr/bin/env python3
from discord.ext import commands
import inspirobot
from random import choice


def setup(bot):
    bot.add_cog(Wisdoms(bot))


class Wisdoms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.wisdom_strings = ['share your wisdom great one', 'what is your wisdom great one']
        self.wisdom_thanks = ['thank you for your wisdom, oh great one', 'thank you great one']

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
            if message.author.id not in self.user_last_request or (message.created_at - self.user_last_request[message.author.id]).seconds > 120:
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

        if message.content.lower() in self.wisdom_thanks:
            self.user_thanked[message.author.id] = True
            
            # add "n" and "p" regional characters to the message followed by a kissing winky face
            await message.add_reaction('🇳')
            await message.add_reaction('🇵')
            await message.add_reaction('😘')