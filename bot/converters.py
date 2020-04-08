from discord.ext.commands import Converter, BadArgument


class OptionsConverter(Converter):
    async def convert(self, ctx, argument):
        options = [o.strip() for o in argument.split(';')]
        if len(options) > 20:
            await ctx.send("To many options were given. (max. 20)")
        elif len(options) < 2:
            await ctx.send("You have to set at least 2 options. Otherwise this makes no sense . . .")
        else:
            return options

        raise BadArgument("Wrong syntax usage or invalid number of options.")
