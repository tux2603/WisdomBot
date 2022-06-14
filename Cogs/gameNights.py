#!/usr/bin/env python3
from discord.ext import commands
from discord_components import Button, ButtonStyle
from random import choice
import yaml


def setup(bot):
    bot.add_cog(GameNights(bot))


class GameNights(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.cheating_proverbs = [
            'Cheating is a sin.',
            'Cheating is a crime.',
            'When one cheats, the other is punished.',
            'If you allow yourself to cheat, you will become a cheater.',
            'A lie has many variations, the truth has none.',
            'If you spit laying down it will only come back in your mouth.',
            'Are you feeling lucky punk?',
            'Cheating is like throwing away a diamond and picking up a rock.',
            'Fool me once, shame on you. Fool me twice, shame on me.',
            'If you cheat again I swear by my pretty floral bonnet, I will end on you.',
            'Nice try',
            'I\'m a robot, I can cheat better than you.'
        ]

    # Requires admin permission
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def gnvote(self, ctx, *games: str):
        buttons_raw = [Button(style=ButtonStyle.green, label=i) for i in games]
        buttons = [buttons_raw[i:i+5] for i in range(0, len(buttons_raw), 5)]

        # print(buttons)

        await ctx.send('It is time for another game night, young gamers! Please vote for any games you would like to play.', components=buttons)
        # await ctx.send('It is time for another game night, young gamers! Please vote for any games you would like to play.')

        # Open up the voting yaml and reset all of the votes
        with open('voting.yml', 'w') as f:
            votes = {i: [] for i in games}
            yaml.dump(votes, f)

    @commands.command()
    async def gnresults(self, ctx):
        with open('voting.yml', 'r') as f:
            votes = yaml.load(f, Loader=yaml.FullLoader)

        games = [(i[0], len(i[1])) for i in votes.items()]
        games.sort(key=lambda x: x[1], reverse=True)


        message = 'Here is the votes as of right now:\n'
        for game in games:
            message += f'Game **{game[0]}** has {game[1]} vote{"s" if game[1] != 1 else ""}\n'

        await ctx.send(message)

    @commands.command()
    async def gnremind(self, ctx):
        with open('voting.yml', 'r') as f:
            votes = yaml.load(f, Loader=yaml.FullLoader)

        games = [(i[0], len(i[1])) for i in votes.items()]
        games.sort(key=lambda x: x[1], reverse=True)
        game = games[0][0]

        print(votes[game])

        # Get the people that voted for the game
        people = []
        for vote in votes[game]:
            member = await ctx.guild.fetch_member(vote)
            if member:
                people.append(member)

        print(people)


        mentions = ' '.join([i.mention for i in people])

        await ctx.send(f'{game} won the vote {mentions}!')


    @commands.Cog.listener()
    async def on_button_click(self, res):
        print(res)
        print(f'{res.user.name} voted for {res.component.label}')
        with open('voting.yml', 'r') as f:
            votes = yaml.load(f, Loader=yaml.FullLoader)
        
        if res.user.id not in votes[res.component.label]:
            votes[res.component.label].append(res.user.id)
            await res.respond(content=f'I will remember your vote for {res.component.label}', ephemeral=True)

        else:
            # send a message to the channel saying that the user has already voted
            proverb = choice(self.cheating_proverbs)
            await self.bot.get_channel(res.channel_id).send(f'You have already voted for that game young {res.user.mention}! A wise, ancient proverb says "{proverb}"')
            await res.respond(content='I am watching you', ephemeral=True, tts=True)

        with open('voting.yml', 'w') as f:
            yaml.dump(votes, f)
