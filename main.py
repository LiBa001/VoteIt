from handler import *

client = discord.Client()


@client.event
async def on_ready():
    print("Logged in as:")
    print(client.user.name)
    print("=============")

    all_votes = sqlib.votes.get_all()
    pending_votes = list(filter(lambda v: v[2] > 0, all_votes))

    for vote in pending_votes:
        client.loop.create_task(timer(client, vote[0]))

    post_to_apis(client)


@client.event
@handle_commands(client)
async def on_message(message):
    prefix = sqlib.server.get(message.server.id, 'prefix')[0]

    if alias_in(message.content, 'vote', prefix=prefix):
        content = get_cmd_content(message.content)

        title = "Vote/Poll"
        options = None
        duration = get_config('default_duration')
        notify_when_ending = False

        async def command_error(reason=" :confused: "):
            await client.send_message(message.channel, "Command error: *{0}*\n"
                                                       "Type `{prefix}vote help` to check how it works!"
                                                       "".format(reason, prefix=prefix))

        if content.count('"') > 1:
            subcommands = list(map(lambda x: x.strip(), content.split('"')))
            last_item = subcommands.pop()  # delete empty item at the end

            if "--notify" in last_item or "-N" in last_item:
                notify_when_ending = True

            skip_next = False

            try:
                for i in range(len(subcommands)):
                    if skip_next:
                        skip_next = False
                        continue

                    subcmd = subcommands[i]
                    nextone = subcommands[i+1]

                    if any(x in subcmd for x in ["-T", "--title"]):
                        title = nextone
                        skip_next = True

                    elif any(x in subcmd for x in ["-O", "--options"]):
                        options = nextone
                        skip_next = True

                    elif any(x in subcmd for x in ["-D", "--duration"]):
                        duration = int(nextone)
                        skip_next = True

                    if any(x in subcmd for x in ["-N", "--notify"]):
                        notify_when_ending = True

                if options is None:
                    await command_error("No options set.")
                    return 0

                if duration < 1:
                    await command_error("Duration has to be at least 1 minute.")
                    return None
                elif duration > 60:
                    await command_error("max. duration are 60 minutes.")
                    return None

            except ValueError:
                await command_error("Duration has to be a number.")
                return 0
            except Exception:
                await command_error("Invalid syntax.")
                return 0

        else:
            content = content.split("|")

            if len(content) == 2:
                title = content[0]
                options = content[1]
            else:
                options = content[0]

        vote_embed = discord.Embed(
            title=title,
            description="Use the reactions to vote!",
            color=int(get_config('color'), 16)
        )
        vote_embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
        vote_embed.set_footer(text=get_config('default_footer'))

        options = options.split(';')
        if len(options) > 20:
            await command_error("To many options were given. (max. 20)")
            return 0
        elif len(options) < 2:
            await command_error("You have to set at least 2 options. Otherwise this makes no sense . . .")
            return 0

        emojis = []
        for i in range(len(options)):  # generates unicode emojis and embed-fields
            hex_str = hex(224 + (6 + i))[2:]
            reaction = b'\\U0001f1a'.replace(b'a', bytes(hex_str, "utf-8"))
            reaction = reaction.decode("unicode-escape")
            emojis.append(reaction)

            if len(options[i]) == 0:
                await command_error("Empty options are not allowed.")
                return None

            vote_embed.add_field(
                name=reaction,
                value=options[i],
                inline=False
            )

        msg = await client.send_message(message.channel, embed=vote_embed)

        emoji_dict = {}
        for emoji in emojis:
            await client.add_reaction(msg, emoji)
            emoji_dict[emoji] = 0

        sqlib.votes.add_element(msg.id, {"options": json.dumps(emoji_dict),
                                         "duration": duration,
                                         "channel": msg.channel.id})

        await refresh_vote_msg(msg, emoji_dict, int(duration), client, notify=notify_when_ending)
        client.loop.create_task(timer(client, msg.id, notify=notify_when_ending))

    elif alias_in(message.content, "invite", prefix=prefix):
        invite = discord.Embed(
            title="Invite Me!",
            color=int(get_config('color'), 16),
            url=get_config('invite_link')
        )
        invite.set_thumbnail(url=get_config("thumbnail"))
        invite.set_footer(text=get_config('default_footer'))

        await client.send_message(message.channel, embed=invite)

    elif alias_in(message.content, "support", prefix=prefix):
        await client.send_message(message.channel, get_config('support_server'))

    elif alias_in(message.content, "prefix", prefix=prefix):
        if not message.author.server_permissions.administrator:
            await client.send_message(message.channel, "You have to admin to change the prefix.")
            return None

        content = get_cmd_content(message.content).lower()

        if len(content) == 0:
            await client.send_message(message.channel, "Prefix too short.")
        elif len(content) > 2:
            await client.send_message(message.channel, "Prefix too long. (max. 2 chars)")
        else:
            sqlib.server.update(message.server.id, {'prefix': content})
            await client.send_message(message.channel, f"Okay, new prefix is `{content}`.")

    elif alias_in(message.content, "info", prefix=prefix):
        infotext = discord.Embed(
            title="VoteIt",
            description="About the bot.",
            color=int(get_config('color'), 16),
            url=get_config('website')
        )
        infotext.set_author(
            name="Linus Bartsch | LiBa01#8817",
            url="https://liba001.github.io/",
            icon_url="https://avatars0.githubusercontent.com/u/30984789?s=460&v=4"
        )
        infotext.set_thumbnail(
            url=get_config('thumbnail')
        )
        infotext.add_field(
            name="Developer",
            value="Name: **Linus Bartsch**\n"
                  "Discord: **LiBa01#8817**\n"
                  "GitHub: [LiBa001](https://github.com/LiBa001)\n"
                  "I'm also at [Discordbots.org](https://discordbots.org/user/269959141508775937).\n"
                  "I'd be very happy if you'd support me on "
                  "[**Patreon**](https://www.patreon.com/user?u=8320690). :heart:\n",
            inline=True
        )
        infotext.add_field(
            name="Developed in:",
            value="Language: **Python3.6**\n"
                  "Library: **discord.py** (0.16.12)\n"
        )
        infotext.add_field(
            name="Commands",
            value="Type `{0}help` to get all commands.\n"
                  "Join the [Official Support Server](https://discord.gg/z3X3uN4) "
                  "if you have any questions or suggestions (or just to be one of the cool guys :sunglasses:)."
                  "".format(prefix)
        )
        infotext.add_field(
            name="Stats",
            value="Server count: **{0}**\n"
                  "Uptime: **{1}** hours, **{2}** minutes\n"
                  "Member count: **{3}**".format(len(client.servers), up_hours, up_minutes,
                                                 len(list(client.get_all_members())))
        )
        infotext.set_footer(
            text="Special thanks to MaxiHuHe04#8905 who supported me a few times."
        )

        await client.send_message(message.channel, embed=infotext)

    elif alias_in(message.content, "donate", prefix=prefix):
        await client.send_message(message.channel, "I'd be very thankful for your support. :heart:\n"
                                                   "{0}".format(get_config('patreon')))


async def update_votes(reaction, user):
    if user.id != client.user.id:
        duration = sqlib.votes.get(reaction.message.id, "duration")

        if duration is None:  # proves if message is in database
            return None
        else:
            duration = duration[0]

        if duration == 0:
            return None

        options = json.loads(sqlib.votes.get(reaction.message.id, "options")[0])

        emoji = reaction.emoji
        if emoji in options:
            votes = reaction.count - 1

            options[emoji] = votes
            sqlib.votes.update(reaction.message.id, {"options": json.dumps(options)})

            if ":bell:" in reaction.message.content:
                notify = True
            else:
                notify = False

            await refresh_vote_msg(reaction.message, options, duration, client, notify=notify)


@client.event
async def on_reaction_add(reaction, user):
    await update_votes(reaction, user)


@client.event
async def on_reaction_remove(reaction, user):
    await update_votes(reaction, user)


@client.event
async def on_server_join(server):
    post_to_apis(client)


@client.event
async def on_server_remove(server):
    post_to_apis(client)


async def uptime_count():
    await client.wait_until_ready()
    global up_hours
    global up_minutes
    up_hours = 0
    up_minutes = 0

    while not client.is_closed:
        await asyncio.sleep(60)
        up_minutes += 1
        if up_minutes == 60:
            up_minutes = 0
            up_hours += 1


client.loop.create_task(uptime_count())
client.run(get_config('token'))
