import discord, jPoints, time
import urllib.request, json
import asyncio

client = discord.Client()
admin_id = "269959141508775937"
prefix = '.'

num_emojis = ['🇦', '🇧', '🇨', '🇩', '🇪', '🇫', '🇬', '🇭', '🇮', '🇯']


def post_to_dbotsorg():
    count_json = json.dumps({
        "server_count": len(client.servers)
    })

    # Resolve HTTP redirects
    dbotsorg_redirect_url = urllib.request.urlopen(
        "https://discordbots.org/api/bots/{0}/stats".format(client.user.id)
    ).geturl()

    # Construct request and post server count
    dbotsorg_req = urllib.request.Request(dbotsorg_redirect_url)

    dbotsorg_req.add_header(
        "Content-Type",
        "application/json"
    )

    dbotsorg_req.add_header(
        "Authorization",
        "<API_KEY>"
    )

    urllib.request.urlopen(dbotsorg_req, count_json.encode("ascii"))


def checkEqual(iterator):
    iterator = iter(iterator)
    try:
        first = next(iterator)
    except StopIteration:
        return True
    return all(first == rest for rest in iterator)


def leading_options(message_id):
    option_values = []

    for emoji in num_emojis:
        option_values.append([emoji, jPoints.vote.get(message_id + emoji)])

    if checkEqual(list(map(lambda x: x[1], option_values))):
        return option_values[0][1], ["*Nothing*"]
    else:
        option_values.sort(key=lambda x: x[1], reverse=True)

    leadings = (option_values[0][1], [])
    for i in range(len(option_values)):
        if i != 0:
            if leadings[0] == option_values[i][1]:
                leadings[1].append(option_values[i][0])
            else:
                return leadings

        elif i == 0:
            leadings[1].append(option_values[i][0])

    return leadings


def time_left(message_id):
    try:
        minutes = int(jPoints.vote.get(message_id + "TIME")[3:])
        hours = int(jPoints.vote.get(message_id + "TIME")[:2])
    except IndexError:
        return None

    mins_now = int(time.strftime('%M'))
    hours_now = int(time.strftime('%H'))

    if hours_now == hours:
        return minutes - mins_now
    elif hours_now < hours:
        return (60 - mins_now) + minutes


def get_leadings_str(message_id):
    leadings_str = ""

    for option in leading_options(message_id)[1]:
        if option != leading_options(message_id)[1][0]:
            leadings_str += ", "
        leadings_str += option

    return leadings_str


def message_update(message_id):
    new_text = "The voting is over in " + \
               str(time_left(message_id)) + \
               time.strftime(" minutes from now (%H:%M).\n") + \
               "Currently leading: " + get_leadings_str(message_id) + \
               " with " + str(leading_options(message_id)[0]) + " vote(s)."

    return new_text


@client.event
async def on_ready():
    print("Eingeloggt als:")
    print(client.user.name)
    print(client.user.id)
    print("-------------")

    post_to_dbotsorg()


@client.event
async def on_message(message):
    commands = ['vote', 'help', 'invite', 'info', 'about']
    commands = list(map(lambda cmd: prefix + cmd, commands))

    if message.content.lower().startswith(tuple(commands)):
        await client.send_typing(message.channel)

    if message.content.startswith(prefix + 'vote'):
        content = message.content[6:]

        commands = ['--title', '-T', '--options', '-O', '-D']
        values = {'title': "voting / poll", '-D': 10}
        for command in commands:
            if content.find(command) != -1:
                quote = content.find('"')
                if quote != -1:
                    content = content[quote + 1:]

                quote = content.find('"')
                if quote != -1:
                    values[command] = content[:content.find('"')]
                    content = content[len(values[command]) + 1:]

        options = []
        for command in values:
            if command in ('--options', '-O'):
                optstring = values[command]

                nextopt = optstring.find(';')
                while nextopt != -1:
                    options.append(optstring[:nextopt].strip())
                    optstring = optstring[nextopt + 1:]
                    nextopt = optstring.find(';')

                options.append(optstring.strip())

            if command in ('--title', '-T'):
                values['title'] = values[command]

        if len(options) > 10:
            options = options[:10]

        # print(options)

        voting = discord.Embed(
            title=values['title'],
            color=0xcd3333,
            description="Click a reaction to vote!"
        )
        voting.set_author(
            name=message.author.name
        )

        # num_emojis = ['🇦', '🇧', '🇨', '🇩', '🇪', '🇫', '🇬', '🇭', '🇮', '🇯']

        option_index = 0
        for option in options:
            voting.add_field(
                name=num_emojis[option_index],
                value=option,
                inline=False
            )
            option_index += 1

        # send message:

        try:
            await client.delete_message(message)
        except discord.errors.Forbidden:
            pass

        duration = values['-D']

        try:
            if int(duration) >= 60:
                duration = 59
        except ValueError:
            await client.send_message(message.channel, "Invalid duration.")
            duration = 10
        
        try:
            votemsg = await client.send_message(
                message.channel,
                "The voting is over in " + str(duration) + time.strftime(" minutes from now (%H:%M)."),
                embed=voting
            )
        except discord.errors.Forbidden:
            return 0

        for emoji in num_emojis:
            jPoints.vote.set(votemsg.id + emoji, 0)

        endtime = time.strftime('%H:') + str(int(time.strftime('%M')) + int(duration))
        # print(endtime)
        if int(endtime[3:]) % 60 < int(time.strftime('%M')):
            endtime = str(int(endtime[:2]) + 1) + ':' + str(int(endtime[3:]) % 60)
        if len(endtime) < 5:
            endtime = endtime[:3] + '0' + endtime[3:]
        jPoints.vote.set(votemsg.id + "TIME", endtime)

        # add reactions:

        for i in range(len(options)):
            await client.add_reaction(votemsg, num_emojis[i])

    elif message.content.startswith(prefix + 'invite'):
        await client.send_message(
            message.channel,
            "Invite me to your server:\n"
            "https://discordapp.com/oauth2/authorize?client_id=353537045320433664&scope=bot&permissions=27712"
        )

    elif message.content.startswith(prefix + 'help'):
        helpmsg = discord.Embed(
            title="VoteIt - Help",
            description="All commands and how they work.",
            color=0xcd3333
        )

        helpmsg.add_field(
            name=prefix + "vote",
            value="Start a voting:\n"
                  "`{0}vote [options]`\n\n"
                  "As options you can use:\n"
                  "Set title: `--title` or `-T`\n"
                  "Set vote options: `--options` or `-O`, separate options with `;`\n"
                  "Set duration: `-D`, value in minutes\n\n"
                  "All values have to stand in double quotes. For example:\n"
                  '`{0}vote -T "Test" -O "option1;option2" -D "15"`'.format(prefix)
        )
        helpmsg.add_field(
            name=prefix + "invite",
            value="Sends a link to invite me to a server.",
            inline=False
        )
        helpmsg.add_field(
            name=prefix + "help",
            value="Shows this help site.",
            inline=False
        )
        helpmsg.add_field(
            name=prefix + "info",
            value="Detailed information about the bot and more.",
            inline=False
        )

        try:
            if message.author.server_permissions.administrator:
                await client.send_message(message.channel, embed=helpmsg)
            else:
                await client.send_message(message.author, embed=helpmsg)
                await client.add_reaction(message, "✅")

        except discord.errors.Forbidden:
            return 0
        except AttributeError:
            return 0

    elif message.content.lower().startswith((prefix + 'info', prefix + 'about')):
        infotext = discord.Embed(
            title="VoteIt",
            description="About the bot.",
            color=0xcd3333,
            url="https://liba001.github.io/VoteIt/"
        )
        infotext.set_author(
            name="Linus Bartsch | LiBa01#8817",
            url="https://liba001.github.io/",
            icon_url="https://avatars0.githubusercontent.com/u/30984789?s=460&v=4"
        )
        infotext.set_thumbnail(
            url="https://images.discordapp.net/avatars/353537045320433664/24558d0686edd48e2e6c6df9e3802c96.png?size=512"
        )
        infotext.add_field(
            name="Developer",
            value="Name: **Linus Bartsch**\n"
                  "Discord: **LiBa01#8817**\n"
                  "GitHub: [LiBa001](https://github.com/LiBa001)\n"
                  "I'm also at [Discordbots.org](https://discordbots.org/user/269959141508775937)",
            inline=True
        )
        infotext.add_field(
            name="Developed in:",
            value="Language: **Python3.6**\n"
                  "Library: **discord.py** (0.16.8)\n"
        )
        infotext.add_field(
            name="Commands",
            value="Type `{0}help` to get all commands.\n"
                  "Join the [Official Support Server](https://discord.gg/z3X3uN4) "
                  "if you have any questions or suggestions.".format(prefix)
        )
        infotext.add_field(
            name="Stats",
            value="Server count: **{0}**\n"
                  "Uptime: **{1}** hours, **{2}** minutes".format(len(client.servers), up_hours, up_minutes)
        )
        infotext.set_footer(
            text="Special thanks to MaxiHuHe04#8905 who supported me a few times."
        )

        await client.send_message(message.channel, embed=infotext)
    
    elif client.user in message.mentions:
        await client.send_message(message.channel, "Type `{0}help` to see available commands.".format(prefix))


@client.event
async def on_reaction_add(reaction, user):
    if user.id != client.user.id and reaction.emoji in num_emojis:
        if time_left(reaction.message.id) is None:
            return None
        elif time_left(reaction.message.id) > 0:
            jPoints.vote.add_to_Value(reaction.message.id + reaction.emoji, 1)
            await client.edit_message(
                reaction.message,
                message_update(reaction.message.id)
            )
        elif time_left(reaction.message.id) <= 0:
            await client.edit_message(
                reaction.message,
                "The voting is over.\n"
                "Winner(s): " + get_leadings_str(reaction.message.id) +
                " with " + str(leading_options(reaction.message.id)[0]) + " vote(s)."
            )
            jPoints.vote.remove_Element(reaction.message.id + "TIME")


@client.event
async def on_reaction_remove(reaction, user):
    if user.id != client.user.id and reaction.emoji in num_emojis:
        if time_left(reaction.message.id) is None:
            return None
        elif time_left(reaction.message.id) > 0:
            jPoints.vote.remove_from_Value(reaction.message.id + reaction.emoji, 1)
            await client.edit_message(
                reaction.message,
                message_update(reaction.message.id)
            )
        elif time_left(reaction.message.id) <= 0:
            await client.edit_message(
                reaction.message,
                "The voting is over.\n"
                "Winner(s): " + get_leadings_str(reaction.message.id) +
                " with " + str(leading_options(reaction.message.id)[0]) + " vote(s)."
            )
            jPoints.vote.remove_Element(reaction.message.id + "TIME")


@client.event
async def on_server_join(server):
    post_to_dbotsorg()


if __name__ == "__main__":
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
    client.run("BOT-TOKEN")  # TODO: insert Token
