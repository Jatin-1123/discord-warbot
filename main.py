import discord
import asyncio
import async_timeout
from discord.ext import commands

import random
import datetime
from dotenv import load_dotenv
import os

load_dotenv()


class EmbedHelpCommand(commands.HelpCommand):
    # Set the embed colour here
    COLOUR = discord.Colour(0xff6900)

    def get_ending_note(self):
        return 'Use {0}{1} [command] for more info on a command.'.format(self.clean_prefix, self.invoked_with)

    def get_command_signature(self, command):
        return '{0.qualified_name} {0.signature}'.format(command)

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title = 'Bot Commands', colour = self.COLOUR)
        description = self.context.bot.description
        if description:
            embed.description = description
        embed.set_author(name = client.user.name, icon_url = client.user.avatar_url)

        for cog, commands in mapping.items():
            name = '\u200b' if cog is None else cog.qualified_name
            filtered = await self.filter_commands(commands, sort = True)
            if filtered:
                value = '\n'.join(f"{f'** {c.name} **'.ljust(20, ' ')} -\t{c.brief}" for c in commands)
                if cog and cog.description:
                    value = '{0}\n{1}'.format(cog.description, value)

                embed.add_field(name = name, value = value)

        embed.set_footer(text = self.get_ending_note())
        await self.get_destination().send(embed = embed)

    async def send_cog_help(self, cog):
        embed = discord.Embed(title = '{0.qualified_name} Commands'.format(cog), colour = self.COLOUR)
        embed.set_author(name = client.user.name, icon_url = client.user.avatar_url)

        if cog.description:
            embed.description = cog.description

        filtered = await self.filter_commands(cog.get_commands(), sort = True)
        for command in filtered:
            embed.add_field(name = self.get_command_signature(command), value = command.short_doc or '...', inline = False)

        embed.set_footer(text = self.get_ending_note())
        await self.get_destination().send(embed = embed)

    async def send_group_help(self, group):
        embed = discord.Embed(title = group.qualified_name, colour = self.COLOUR)
        embed.set_author(name = client.user.name, icon_url = client.user.avatar_url)
        if group.help:
            embed.description = group.help

        if isinstance(group, commands.Group):
            filtered = await self.filter_commands(group.commands, sort = True)
            for command in filtered:
                embed.add_field(name = self.get_command_signature(command), value = command.short_doc or '...', inline = False)

        embed.set_footer(text = self.get_ending_note())
        await self.get_destination().send(embed = embed)

    # This makes it so it uses the function above
    # Less work for us to do since they're both similar.
    # If you want to make regular command help look different then override it
    send_command_help = send_group_help


client = commands.Bot(command_prefix = commands.when_mentioned_or("/"),
                      case_insensitive = True,
                      activity = discord.Game(
                          name = 'War Simulator after getting spoilers that Lara won :('),
                      status = discord.Status.online,
                      help_command = EmbedHelpCommand()
                      )
config = {
    "Number of Teams": 2,
    "Teams"          : [],
    "Spawn Rate"     : 30
}

weapons = {
    "Gun"          : {
        "URL"         : "https://raw.githubusercontent.com/GhostMander/discord-warbot/main/assets/gun.png",
        "Desc"        : "Gun! Ranged Weapon that has the highest damage, but recoil makes it miss a few times!\nChance to hit  :  **20%**\nDamage Dealt :  **90 - 100**",
        "Damage Range": {90, 100}, "Chance of Hit": 20, "Emote": "🔫"
    },
    "Bow and Arrow": {
        "URL"         : "https://raw.githubusercontent.com/GhostMander/discord-warbot/main/assets/bow.png",
        "Desc"        : "Bow and Arrow! Ranged Weapon that has a mediocre chance to hit, and deals mediocre damage!\nChance to hit  :  **40%**\nDamage Dealt :  **70 - 80**",
        "Damage Range": {70, 80}, "Chance of Hit": 40, "Emote": "🏹"
    },
    "Axe"          : {
        "URL"         : "https://raw.githubusercontent.com/GhostMander/discord-warbot/main/assets/axe.png",
        "Desc"        : "Axe! Meelee weapon that looks dangerous but sometimes fall off due to it's Weight, Lowering it's Chances to hit!\nChance to hit  :  **60%**\nDamage Dealt :  **50 - 60**",
        "Damage Range": {50, 60}, "Chance of Hit": 60, "Emote": "🪓"
    },
    "Dagger"       : {
        "URL"         : "https://raw.githubusercontent.com/GhostMander/discord-warbot/main/assets/dagger.png",
        "Desc"        : "Dagger! Meelee weapon that any Knight from the Middle Ages would know! With fairly high Chance to Hit, Its very Small making its Damage fairly Low!\nChance to hit  :  **80%**\nDamage Dealt :  **30 - 40**",
        "Damage Range": {30, 40}, "Chance of Hit": 80, "Emote": "🗡️"
    },
    "Knife"        : {
        "URL"         : "https://raw.githubusercontent.com/GhostMander/discord-warbot/main/assets/knife.png",
        "Desc"        : "Knife! Melee Weapon that hits its mark almost every time!, but deals low damage!\nChance to hit  :  **100%**\nDamage Dealt :  **10 - 20**",
        "Damage Range": {10, 20}, "Chance of Hit": 100, "Emote": "🔪"
    }
}
weapon_keys = {
    "🔫" : "Gun",
    "🏹" : "Bow and Arrow",
    "🪓" : "Axe",
    "🗡️": "Dagger",
    "🔪" : "Knife"
}
weapon_list = set(weapon_keys.keys())


def duelHelp():
    return f"\n\n**{'< DAMAGE VALUES >'.center(45, '=')}**\n" + "\n\n".join(f'**{values["Emote"]}**\n{values["Desc"]}' for values in weapons.values())


async def reaction_remover(message):
    msg = await message.channel.fetch_message(message.id)
    for i in msg.reactions:
        l = await i.users().flatten()
        if len(l) == 1:
            continue
        for j in l:
            if j != client.user:
                await msg.remove_reaction(i.emoji, j)


def attack(attacked, dmg_range, attack_chance):
    if attack_chance == 100:
        killed = True
    else:
        killed = random.choices([True, False], weights = [attack_chance * 100000, (100 - attack_chance) * 100000])[0]
    if killed:
        dmg = min([random.randint(min(dmg_range), max(dmg_range)), attacked.health])
        attacked.health -= dmg
        return dmg
    else:
        return 0


async def weapon_choose(ctx, author, opponent, editMessage, round):
    booleans = [False, False]

    def check(reaction, user):
        a = user.display_name == author.user
        b = str(reaction.emoji)
        c = user.display_name == opponent.user
        if a:
            if b in weapon_list:
                author.new_weapon(weapon_keys[b])
                booleans[0] = True
        elif c:
            if b in weapon_list:
                opponent.new_weapon(weapon_keys[b])
                booleans[1] = True
        return booleans[0] and booleans[1]

    try:
        reaction, user = await client.wait_for(event = 'reaction_add', timeout = 15.0, check = check)
    except asyncio.TimeoutError:
        await ctx.send('Timeout. You took too long!')
        await reaction_remover(editMessage)
    else:
        await duel_main(ctx, editMessage, round, author, opponent)


async def duel_main(ctx, editMessage, round, author, opponent):
    oppdmg = opponent.fight(author)
    autdmg = author.fight(opponent)
    duelSim = discord.Embed(
        title = f"__{author.user}__ vs __{opponent.user}__",
        colour = discord.Colour(0x91a386),
        description = f"{author.user} chose **{author.weapon}** and {opponent.user} chose **{opponent.weapon}**\n\n**Choose a new or the same weapon for the next round!**"
    )

    duelSim.add_field(
        name = f"__{author.user} ({author.health}/100)__",
        value = author.healthBar()
    )

    duelSim.add_field(
        name = f"__{opponent.user} ({opponent.health}/100)__",
        value = opponent.healthBar()
    )

    duelSim.add_field(
        name = f"**__Round {round}__**", inline = False,
        value = autdmg
    )

    duelSim.add_field(
        name = "\u200b", inline = False,
        value = oppdmg
    )

    await editMessage.edit(content = None, embed = duelSim)
    await author.next_round(opponent, round, editMessage, ctx)


class Dueler:
    def __init__(self, member: discord.Member, weapon):
        self.user = member.display_name
        self.health = 100
        self.weapon = weapon
        self.weaponStats = weapons[self.weapon]

    def fight(self, opponent):
        h_m = attack(opponent, dmg_range = self.weaponStats["Damage Range"], attack_chance = self.weaponStats["Chance of Hit"])

        if not h_m:
            return f"**{self.user}** missed **{opponent.user}** While using **{self.weapon}**"
        return f"**{self.user}** hits **{opponent.user}** using **{self.weapon}** for a WHOPPING __**{h_m}**__ Damage!"

    def healthBar(self):
        hearts = (self.health) // 10
        heartstr = "♥\u0020" * hearts
        deadstr = ('\u2661\u0020' * (10 - hearts)).strip("\u0020")
        return f"`{heartstr}{deadstr}`"

    def new_weapon(self, weapon):
        self.weapon = weapon

    async def next_round(self, opponent, round, editMessage, ctx):
        await reaction_remover(editMessage)
        if opponent.health and self.health:
            await weapon_choose(ctx, self, opponent, editMessage, round + 1)
        else:
            if not opponent.health and not self.health:
                await ctx.send(content = "**Both opponents fainted, it's a TIE**", embed = None)
            elif self.health:
                await ctx.send(content = F"**{opponent.user} fainted, hence, {self.user} WINS**", embed = None)
            elif opponent.health:
                await ctx.send(content = F"**{self.user} fainted, hence, {opponent.user} WINS**", embed = None)


class Team:
    def __init__(self, name: str, leader: discord.Member, members: list, startingWealth: int):
        self.name = name
        self.leader = leader
        self.wealth = startingWealth
        try:
            members.remove(leader)
        except ValueError:
            pass
        self.members = members


@client.event
async def on_ready():
    print('Ready to battle, Lets goo gamers!')


@client.listen('on_message')
async def spawner(message):
    # print(message.content)
    if len(config["Teams"]) == config["Number of Teams"]:
        chance = config["Spawn Rate"]
        if not message.author.bot:
            spawned = random.choices([True, False], weights = [chance * 100000, (100 - chance) * 100000])[0]
            if spawned and chance != 0:
                weapon = weapon_keys[(random.choice(list(weapon_list)))]
                embed = discord.Embed(name = "Weapon Spawned", colour = discord.Colour(0xff6900), timestamp = datetime.datetime.now(),
                                      description = f"A weapon has Spawned!\nType **/take {weapon.split()[0]}** to get!")
                embed.set_image(url = weapons[weapon]['URL'])
                embed.set_footer(text = f"/take {weapon.split()[0]} to obtain | /help get for more info",
                                 icon_url = client.user.avatar_url)
                embed.set_author(name = "Spawn")
                embed.set_thumbnail(url = client.user.avatar_url)
                await message.channel.send(embed = embed)


@client.command(name = "ping", brief = "Ping", help = f"Displays Latency of the Bot. \nUsage : /ping")
async def _ping(ctx):
    await ctx.send(f'War latency is {round(client.latency * 1000)}ms')


@client.command(name = "configure", aliases = ["config"], brief = "Configure settings for the Bot.", help = f"Change settings for the Bot. **Possible configurations :**\n- Number of Teams\n- Spawn Rate\n\nUsage : /configure [no-of-teams (number greater than/equal to 2)|spawn-rate (0 - 100)] (Pass in No number to get current Setting)")
async def _config(ctx, configuration=None, setting: int = None):
    global config
    if configuration is None:
        await ctx.send("No argument Given.")
    elif "no-of-teams" in configuration.lower():
        if setting is None:
            await ctx.send(f"Current **Number of Teams** are {config['Number of Teams']}")
        elif setting >= 2:
            await ctx.send(f"Changed the Number of Teams from {config['Number of Teams']} to {setting}")
            config["Number of Teams"] = setting
        else:
            await ctx.send("There must be two or more Teams")
    elif "spawn-rate" in configuration.lower():
        if setting is None:
            await ctx.send(f"Current **Spawn Rate** is {config['Spawn Rate']}")
        elif 0 <= setting <= 100:
            await ctx.send(f"Changed the spawn rate from {config['Spawn Rate']} to {setting}")
            config["Spawn Rate"] = setting
        else:
            await ctx.send("Spawn rate must be between 0-100")
    else:
        await ctx.send("Invalid Setting")


@client.command(name = "quit", brief = "Quits Bot", help = f"Logs out the Bot. **(Owner Exclusive)**\nUsage : /quit", hidden = True)
async def _quit(ctx):
    if await client.is_owner(ctx.author):
        await ctx.send(f"As per the request of the Control Devil named {ctx.author.display_name}, I will shoot myself.")
        await client.logout()
    else:
        await ctx.send("GET OFF MY LAWN (and clean up the shit stains you created you demon)")


@client.command(name = "register", brief = "Register for the War.", help = "Two Teams register for the War, and Fight it out in an Epic Battle with Weapons and Items!\nUsage : /register [Starting Money **(Optional)**]")
async def _register(ctx, startingWealth: int = 1000):
    registration_help_embed = discord.Embed(title = "Lets begin registration for War!",
                                            colour = discord.Colour(0xff6900),
                                            description = "Here are the steps for Registration :"
                                            )
    registration_help_embed.set_author(name = ctx.author.name,
                                       icon_url = ctx.author.avatar_url
                                       )
    registration_help_embed.add_field(name = "Team Names",
                                      value = "The names for both teams!",
                                      inline = False
                                      )
    registration_help_embed.add_field(name = "Team Leaders",
                                      value = "Mention the Leader",
                                      inline = False
                                      )
    registration_help_embed.add_field(name = "Team Members",
                                      value = "Mention all team members",
                                      inline = False
                                      )
    await ctx.send(embed = registration_help_embed)

    try:
        for i in range(1, config["Number of Teams"] + 1):
            registration_embed = discord.Embed(title = "Register", colour = discord.Colour(0xff6900), description = f"Enter Team {i}'s Name Below")
            registration_message = await ctx.send(embed = registration_embed)
            team_name = await client.wait_for('message', check = lambda x: (x.channel == ctx.channel and x.author == ctx.author), timeout = 60.0)
            await registration_message.delete()
            await team_name.delete()

            registration_embed = discord.Embed(title = "Register", colour = discord.Colour(0xff6900), description = f"Ping/Mention Team {i}'s Leader Below")
            registration_message = await ctx.send(embed = registration_embed)
            team_leader = await client.wait_for('message', check = lambda x: (x.channel == ctx.channel and x.author == ctx.author and len(x.mentions) == 1), timeout = 60.0)
            await registration_message.delete()
            await team_leader.delete()

            registration_embed = discord.Embed(title = "Register", colour = discord.Colour(0xff6900), description = f"Ping/Mention Team {i}'s members Below")
            registration_message = await ctx.send(embed = registration_embed)
            team_members = await client.wait_for('message', check = lambda x: (x.channel == ctx.channel and x.author == ctx.author), timeout = 60.0)
            await registration_message.delete()
            await team_members.delete()
            config["Teams"].append(Team(teamname.content.strip(' '), teamleader.mentions[0], list(set(teammembers.mentions)), startingWealth = startingWealth))

    except asyncio.TimeoutError:
        ctx.send("Timed Out, Try again Later. (I mean cmon man, you had 60 seconds lmao)")
    else:
        await ctx.send("Confirm Details.")

        confirmation_embed = discord.Embed(title = "__Confirmation__",
                                           color = discord.Colour(0xff6900),
                                           description = "React with ✅ to confirm, and ❎ to deny.")
        for i in range(1, config["Number of Teams"] + 1):
            team = config["Teams"][i - 1]
            name = team.name
            leader = team.leader.mention
            members = ','.join(i.mention for i in team.members)
            confirmation_embed.add_field(name = "Team 1",
                                         value = f"**Name** : {name},\n**Leader** : {leader},\n**Members** : {members}")
        confirm_msg = await ctx.send(embed = confirmation_embed)
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❎")
        confirmed = [True]

        def check(r, u):
            if (u == ctx.author and r.message == confirm_msg):
                if str(r.emoji) == "✅": return True
                elif str(r.emoji) == "❎":
                    confirmed[0] = False
                    raise asyncio.TimeoutError

        try:
            reaction, user = await client.wait_for("reaction_add", timeout = 60.0, check = check)
        except asyncio.TimeoutError:
            if confirmed[0]:
                await ctx.send("Timed Out, Not confirmed.")
            else:
                await ctx.send("Denied.")
                config["Teams"] = []
            del confirmed
        else:
            await ctx.send("Successfully Registered!")


@client.command(name = "duel", brief = "Duel against other Players.", help = f"Two Players Duel till the End, and Fight it out in an Epic Battle with Weapons! Every Weapon has Random chance to Hit, and Random Damage{duelHelp()}\n\n\n**__Usage__ : /duel [Other Player]**")
async def _duel(ctx, member: discord.Member = None):
    if ctx.author != member != client.user and member is not None:
        weaponChoose = discord.Embed(
            title = f"Duel - __{ctx.author.display_name}__ against __{member.display_name}__",
            colour = discord.Colour(0x91a386),
            description = "Choose a Weapon to Fight!"
        )

        weaponChoose.set_author(
            name = f"{ctx.author}",
            icon_url = ctx.author.avatar_url
        )

        for values in weapons.values():
            weaponChoose.add_field(
                name = values["Emote"],
                value = values["Desc"]
            )

        weaponChoose.add_field(
            name = "\u3164", inline = False,
            value = "Choose the First Weapon for either Side. You have 15 seconds."
        )

        chooseMsg = await ctx.send(embed = weaponChoose)

        weapon = {}
        booleans = [False, False]

        for key, value in weapons.items():
            await chooseMsg.add_reaction(value["Emote"])

        def check(reaction, user):
            a = user == ctx.author
            b = str(reaction.emoji)
            c = user == member
            if a:
                if b in weapon_list:
                    weapon[ctx.author] = weapon_keys[b]
                    booleans[0] = True
            if c:
                if b in weapon_list:
                    weapon[member] = weapon_keys[b]
                    booleans[1] = True

            return booleans[0] and booleans[1]

        try:
            reaction, user = await client.wait_for(event = 'reaction_add', timeout = 15.0, check = check)
        except asyncio.TimeoutError:
            await ctx.send('Timeout. You took too long!')
            await reaction_remover(chooseMsg)
        else:
            author = Dueler(ctx.author, weapon[ctx.author])
            opponent = Dueler(member, weapon[member])

            await duel_main(ctx, chooseMsg, 1, author, opponent)
    else:
        if member is None:
            await ctx.send("Mention a user to duel with.")
        elif ctx.author == member:
            await ctx.send("You cant duel against Yourself, cmon Man...")
        elif member == client.user:
            await ctx.send("You cant duel against Me, I dont want to destroy you...")


client.run(os.getenv('BOT_TOKEN'))
