import json
import functools
import discord
import time
import asyncio
import sqlib
import urllib.request


def get_config(key: str):
    with open('./data/config.json', 'r', encoding='utf8') as f:
        config = json.load(f)
        return config[key]


def concat_elements(iterable: list or tuple or dict, space: str=" "):
    if iterable is None:
        return None
    elif len(iterable) == 0:
        return ""

    return functools.reduce(lambda x, y: f"{x}{space}{y}", iterable)


def get_commands():
    with open('./data/commands.json', 'r', encoding='utf8') as f:
        return json.load(f)


def get_cmd_by_alias(alias: str):
    commands = get_commands()
    for cmd in commands:
        if alias in commands[cmd]['aliases']:
            return cmd


def get_aliases(cmd: str, prefix: str=None):
    commands = get_commands()
    aliases = commands[cmd]['aliases']

    if prefix is not None:
        aliases = tuple(map(lambda alias: prefix + alias, aliases))
    else:
        aliases = tuple(aliases)

    return aliases


def get_help_text(cmd: str, prefix):
    commands = get_commands()
    return concat_elements(commands[cmd]['help'], space="").format(prefix=prefix)


def get_help_embed(alias: str, prefix):
    commands = get_commands()

    if alias in commands:
        cmd = alias
    else:
        cmd = get_cmd_by_alias(alias)

    help_text = get_help_text(cmd, prefix)
    embed = discord.Embed(
        title=cmd,
        description=help_text,
        color=int(get_config('color'), 16)
    )
    embed.set_footer(
        text=get_config('default_footer')
    )
    return embed


def get_all_aliases(prefix=None):
    commands = get_commands()
    aliases = []
    for cmd in commands:
        for alias in get_aliases(cmd, prefix=prefix):
            aliases.append(alias)

    return tuple(aliases)


def alias_in(content: str, cmd: str, prefix=None):
    aliases = get_aliases(cmd, prefix=prefix)
    return content.lower().startswith(aliases)


def get_cmd_content(content: str):
    content = content.split(' ')
    if len(content) > 1:
        content = concat_elements(content[1:])
        return content

    else:
        return ""


def get_aliases_str(cmd: str, prefix=None):
    aliases = get_aliases(cmd, prefix=prefix)
    aliases_str = concat_elements(aliases, space=', ')
    return aliases_str


def get_aliases_embed(alias: str, prefix=None):
    cmd = get_cmd_by_alias(alias)
    aliases_str = get_aliases_str(cmd, prefix=prefix)

    aliases_embed = discord.Embed(
        title=f"`{cmd}` aliases",
        description=aliases_str,
        color=int(get_config('color'), 16)
    )
    aliases_embed.set_footer(
        text=get_config('default_footer')
    )
    return aliases_embed


def get_leading_options(options: dict):
    options = list(map(lambda o: (o, options[o]), options))
    options = sorted(options, key=lambda o: o[1], reverse=True)

    highest = options[0][1]

    leading_emojis = list(map(lambda o: o[0], filter(lambda o: o[1] == highest, options)))

    if len(leading_emojis) == len(options):
        leading_emojis = ["`A draw`"]

    return concat_elements(leading_emojis, ", "), highest


async def refresh_vote_msg(message: discord.Message, options: dict, duration: int, coro_client: discord.Client,
                           clock=True, notify=False):

    leading_options = get_leading_options(options)

    if clock:
        clock_emoji = f":clock{duration % 12 if duration % 12 != 0 else 12}:"
    else:
        clock_emoji = ""

    if leading_options[1] == 1:
        vote_plural = ""
    else:
        vote_plural = "s"

    if duration == 0:
        if len(leading_options[0]) > 1:
            winner_plural = "s"
        else:
            winner_plural = ""

        winners = "Final winner{0}: {1[0]} with {1[1]} vote{2}.".format(winner_plural, leading_options, vote_plural)

        await message.edit(content=f"The voting is over.\n{winners}")

        if notify:
            await message.channel.send(f":bell: Voting is over. :bell: \n")

    else:
        if notify:
            notification = "Notification turned on. :bell: \n"
        else:
            notification = ""

        await message.edit(content="The voting is over in {0} minutes. {clock_emoji} \n"
                                         "{notification}"
                                         "Currently leading: {1[0]} with {1[1]} vote{2}."
                                         "".format(duration, leading_options, vote_plural,
                                                   clock_emoji=clock_emoji,
                                                   notification=notification)
                           )
    return message


async def timer(client: discord.Client, vote_id: str, notify: bool=False):
    t_needed = 0
    while not client.is_closed():
        await asyncio.sleep(60 - t_needed)

        t_start = time.time()

        vote = sqlib.votes.get(vote_id)

        msg_id, options, duration, channel_id = vote

        duration -= 1

        sqlib.votes.update(msg_id, {"duration": duration})
        channel = client.get_channel(int(channel_id))

        try:
            message = await channel.get_message(msg_id)
        except AttributeError:
            print("AttributeError")
            continue

        await refresh_vote_msg(message, json.loads(options), duration, client, notify=notify)

        if duration == 0:
            break

        t_end = time.time()
        t_needed = t_end - t_start


def handle_commands(client):
    def decorated(func):
        @functools.wraps(func)
        async def wrapper(message):
            if isinstance(message.channel, discord.DMChannel):
                if message.author != client.user:
                    await message.channel.send("Sorry, I can't help you in a private chat.")
                return None

            client_member = message.guild.get_member(client.user.id)
            if not client_member.permissions_in(message.channel).send_messages:
                return None

            prefix = sqlib.server.get(message.guild.id, 'prefix')
            if prefix is None:
                prefix = get_config('prefix')
                sqlib.server.add_element(message.guild.id, {'prefix': prefix})
            else:
                prefix = prefix[0]

            all_aliases = get_all_aliases(prefix=prefix)
            embed_color = int(get_config('color'), 16)
            footer = get_config('default_footer')

            if message.content.lower().startswith(all_aliases):  # checks if message is a command
                async with message.channel.typing():
                    pass

                if alias_in(message.content, 'help', prefix=prefix):
                    content = get_cmd_content(message.content)

                    if content.lower() in get_all_aliases(prefix=None):
                        help_embed = get_help_embed(content.lower(), prefix)

                    else:
                        commands = get_commands()

                        help_embed = discord.Embed(
                            title="Help",
                            description="All commands and how to use them.",
                            color=embed_color,
                            url=get_config("website")
                        )
                        for cmd in commands:
                            help_embed.add_field(
                                name=cmd,
                                value=get_help_text(cmd, prefix),
                                inline=False
                            )
                        help_embed.set_footer(
                            text=footer
                        )
                        help_embed.set_thumbnail(url=get_config("thumbnail"))

                    if message.author.guild_permissions.administrator:
                        await message.channel.send(embed=help_embed)

                    else:
                        try:
                            await client.send_message(message.author, embed=help_embed)
                            await message.channel.send("Help sent. :white_check_mark:")
                        except discord.Forbidden:
                            await message.channel.send("You have to turn on your PM.")

                elif alias_in(message.content, 'aliases', prefix=prefix):
                    content = get_cmd_content(message.content)

                    if content.lower() in get_all_aliases(prefix):
                        aliases_embed = get_aliases_embed(content.lower())

                    else:
                        commands = get_commands()

                        aliases_embed = discord.Embed(
                            title="Aliases",
                            description="The aliases of all commands.",
                            color=embed_color
                        )
                        for cmd in commands:
                            aliases_embed.add_field(
                                name=cmd,
                                value=get_aliases_str(cmd),
                                inline=False
                            )
                        aliases_embed.set_footer(
                            text=footer
                        )

                    await message.channel.send(embed=aliases_embed)

                else:
                    content = get_cmd_content(message.content)
                    cmd_without_prefix = message.content.split(' ')[0][
                                         len(prefix):]  # splits command from prefix and other content
                    if content.lower().startswith('help'):
                        help_embed = get_help_embed(cmd_without_prefix, prefix)
                        await message.channel.send(embed=help_embed)  # sends cmd specific help

                    elif content.lower().startswith('aliases'):
                        aliases_embed = get_aliases_embed(cmd_without_prefix)
                        await message.channel.send(embed=aliases_embed)

                    else:
                        return await func(message)

            elif client.user in message.mentions:
                await client.send_message(
                    message.channel,
                    f"Type `{sqlib.server.get(message.guild.id, 'prefix')[0]}help` to see the command list!"
                )
                return await func(message)

            return None  # exits if it's not in command list -> !!! Add new commands to 'commands.json' !!!

        return wrapper
    return decorated


def post_to_apis(client: discord.Client()):
    domains = {
        'discordbots.org': get_config('API_TOKEN(discordbots.org)'),
        'bots.discord.pw': get_config('API_TOKEN(bots.discord.pw)')
    }
    for domain in domains:
        count_json = json.dumps({
            "server_count": len(client.guilds)
        })

        # Resolve HTTP redirects
        api_redirect_url = "https://{0}/api/bots/{1}/stats".format(domain, client.user.id)

        # Construct request and post server count
        api_req = urllib.request.Request(api_redirect_url)

        api_req.add_header(
            "Content-Type",
            "application/json"
        )

        api_req.add_header(
            "Authorization",
            domains[domain]
        )

        urllib.request.urlopen(api_req, count_json.encode("ascii"))
