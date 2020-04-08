from properties import DEFAULT
from discord.ext import commands
from disputils import BotMultipleChoice
from bot import OptionsConverter, Context


class Vote(BotMultipleChoice):
    def __init__(self, ctx, options, title, description="", color=DEFAULT['color']):
        if description == "":
            description = "Use the reactions to vote!"

        super().__init__(ctx, options, title, description, color=color)

    def _generate_embed(self):
        embed = super()._generate_embed()

        embed.set_author(name=str(self._ctx.author),
                         icon_url=self._ctx.author.avatar_url)
        self._embed = embed

        return embed

    async def run(self, users=None, channel=None, **kwargs):
        if users is None:
            users = []

        await super().run(users, channel, **kwargs)


@commands.command()
async def simple(ctx: Context, title, *, options: OptionsConverter()):
    """ Creates a simple reaction poll without any further evaluation. """

    vote = Vote(ctx, options, title)
    await vote.run(closable=False, timeout=0)  # create vote, but don't wait for reaction
