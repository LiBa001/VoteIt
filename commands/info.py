import discord
from discord.ext import commands
from properties import CONFIG, DEFAULT


@commands.command(aliases=['about'])
async def info(ctx):
    """ Shows information about this bot and it's creator. """

    info_emb = discord.Embed(
        title="VoteIt",
        description="About the bot.",
        color=DEFAULT['color'],
        url=CONFIG['website']
    )
    info_emb.set_author(
        name="Linus Bartsch | LiBa01#8817",
        url="https://liba001.github.io/",
        icon_url="https://avatars0.githubusercontent.com/u/30984789?s=460&v=4"
    )
    info_emb.set_thumbnail(
        url=CONFIG['thumbnail']
    )
    info_emb.add_field(
        name="Developer",
        value="Name: **Linus Bartsch**\n"
              "Discord: **LiBa01#8817**\n"
              "GitHub: [LiBa001](https://github.com/LiBa001)\n"
              "I'm also at [top.gg](https://top.gg/user/269959141508775937).\n"
              "I'd be very happy if you'd support me on "
              "[**Patreon**](https://www.patreon.com/user?u=8320690). :heart:\n",
        inline=True
    )
    info_emb.add_field(
        name="Developed in:",
        value="Language: **Python3.7**\n"
              f"Library: **discord.py** ({discord.__version__})\n"
              "Database: **sqlite3**\n"
    )
    info_emb.add_field(
        name="Commands",
        value="Type `{0}help` to get all commands.\n"
              "Join the [Official Support guild](https://discord.gg/z3X3uN4) "
              "if you have any questions or suggestions (or just to be one of the cool guys :sunglasses:)."
              "".format(ctx.prefix)
    )
    info_emb.add_field(
        name="Stats",
        value="guild count: **{0}**\n"
              "Member count: **{1}**".format(len(ctx.bot.guilds), len(list(ctx.bot.get_all_members())))
    )

    await ctx.send(embed=info_emb)
