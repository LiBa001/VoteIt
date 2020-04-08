import discord
from discord.ext.commands import when_mentioned_or
from properties import DEFAULT
from bot import Bot
from orm import database, Guild, User, Vote
import logging
import sys
import os


loggers = [logging.getLogger(module) for module in ['bot', 'commands', 'events']]

stream_handler = logging.StreamHandler(stream=sys.stdout)
stream_handler.setLevel(logging.DEBUG)

for logger in loggers:
    logger.setLevel(logging.DEBUG)
    logger.addHandler(stream_handler)


database.connect()

Guild.create_table(safe=True)
User.create_table(safe=True)
Vote.create_table(safe=True)


async def dynamic_prefix(b: Bot, msg):
    if isinstance(msg.channel, discord.DMChannel):
        return DEFAULT['prefix']

    guild = Guild.from_discord_model(msg.guild)

    return when_mentioned_or(guild.prefix)(b, msg)


bot = Bot(command_prefix=dynamic_prefix)


bot.load_extension('commands')
bot.load_extension('events')


bot.run(os.getenv('BOT_TOKEN'))


database.close()
