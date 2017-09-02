import discord, jPoints, time

client = discord.Client()
admin_id = "ADMIN-ID" # TODO: insert ADMIN-ID
prefix = '.'

num_emojis = ['🇦', '🇧', '🇨', '🇩', '🇪', '🇫', '🇬', '🇭', '🇮', '🇯']


def leading_options(message_id):
    option_values = []

    for emoji in num_emojis:
        option_values.append([emoji, jPoints.vote.get(message_id + emoji)])

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
    return int(jPoints.vote.get(message_id + "TIME")[3:]) - int(time.strftime('%M'))


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


@client.event
async def on_message(message):
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

        votemsg = await client.send_message(
            message.channel,
            "The voting is over in " + str(duration) + time.strftime(" minutes from now (%H:%M)."),
            embed=voting
        )

        for emoji in num_emojis:
            jPoints.vote.set(votemsg.id + emoji, 0)

        endtime = time.strftime('%H:') + str((int(time.strftime('%M')) + int(duration)) % 60)
        # print(endtime)
        jPoints.vote.set(votemsg.id + "TIME", endtime)

        # add reactions:

        for i in range(len(options)):
            await client.add_reaction(votemsg, num_emojis[i])

    if message.content.startswith(prefix + 'invite'):
        await client.send_message(
            message.channel,
            "Invite me to your server:\n"
            "https://discordapp.com/oauth2/authorize?client_id=353537045320433664&scope=bot&permissions=27712"
        )

    if message.content.startswith(prefix + 'help'):
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

        if message.author.server_permissions.administrator:
            await client.send_message(message.channel, embed=helpmsg)
        else:
            await client.send_message(message.author, embed=helpmsg)


@client.event
async def on_reaction_add(reaction, user):
    if user.id != client.user.id:
        if time_left(reaction.message.id) > 0:
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


@client.event
async def on_reaction_remove(reaction, user):
    if user.id != client.user.id:
        if time_left(reaction.message.id) > 0:
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


if __name__ == "__main__":
    client.run("BOT-TOKEN") # TODO: insert BOT-TOKEN
