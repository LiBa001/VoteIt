from discord.ext.commands import Bot
from .info import info
from .vote import simple


def setup(bot: Bot):
    bot.add_command(info)
    bot.add_command(simple)
