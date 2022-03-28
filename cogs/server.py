from io import BytesIO as IoBytesIO
from colorthief import ColorThief
from discord.ext.commands import command, Cog, group
from re import search as re_search, sub as re_sub, compile as re_compile
from PIL import Image
from traceback import format_exc
from os import remove as os_rem
from datetime import datetime
from discord.utils import escape_mentions
from matplotlib.pyplot import pie as pltPie, axis as pltAxis, savefig as pltSavefig
from discord import (
    Embed, Colour, Status, File,
    Emoji, TextChannel, HTTPException, Member,
    ActivityType, Forbidden
)
from imports import (
    access_ids, colrs, botPrefixDB,
    lineNum, Cmds, loading_msg,
    aiohttp_request, tryInt, tstGuild, dblpy
)


class Server(Cog):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        print("Module: Server loaded")

    @command(description="Check the newest server members")
    async def newmembers(self, ctx, *, count=5):
        try:
            if count > 25: return await ctx.send('Max count is 25')
            if not ctx.guild.chunked: await self.bot.request_offline_members(ctx.guild)
            
            embed = Embed(title=f'{count} Newest members (from the newest)', colour=Colour(0x36393f))
            members = sorted(ctx.guild.members, key=lambda m: m.joined_at, reverse=True)[:count]
            
            for member in members:
                embed.add_field(name=f'{member}', value=f'> Joined on: {member.joined_at:%d of %B, %Y [%A at %I:%M%p}\n> Account made on: {member.created_at:%d of %B, %Y [%A]}', inline=False)
            
            await ctx.send(embed=embed)
        except Exception as e: return await ctx.send(e)

    @group(invoke_without_command=True, description="Shows server commands, Info, and more")
    async def server(self, ctx): await ctx.send(embed=Embed(
        color=colrs[4], title="All server commands:",
        description="\n".join(map(str, Cmds.server))))

    @server.command(description="Change servers prefix")
    async def prefix(self, ctx, *, prefix=None):
        try:
            if prefix == '...':
                try:
                    if not botPrefixDB.find_one({'_id': f'{ctx.guild.id}'}): return await ctx.send('That is the current prefix')
                    botPrefixDB.find_one_and_delete({'_id': f'{ctx.guild.id}'})
                    return await ctx.send("Prefix reset to the default which is `...`")
                except: print(format_exc())
            elif re_search("­|\u200b", prefix): return await ctx.send("Please use a prefix that has no zero width characters so that everyone can be able to use it.")
            elif len(prefix) > 25: return await ctx.send("That prefix is quite long, limit is 25 characters.")
            elif " " in prefix: return await ctx.send("Prefix cannot include spaces")
            else:
                try: botPrefixDB.find_one_and_update({'_id': f'{ctx.guild.id}'}, {'$set': {'prefix': prefix, 'guildName': ctx.guild.name}}, upsert=True)
                except Exception as e:
                    return await ctx.send(f"There was a a little problem while changing the prefix, please use the feedback command to send the error blow to my developer.\n```\n{e}\n```")
                return await ctx.send(embed=Embed(
                    color=colrs[2],
                    title="<:Mark:663230689860386846> Custom prefix created:",
                    description=f"New Prefix: {botPrefixDB.find_one({'_id': f'{ctx.guild.id}'})['prefix']}\n**NOTE:** Bot'll nolonger respond to the default prefix in this server which is ...")
                        .set_footer(text="So don't forget the prefix you set 👀. But if you do forget, ping me."))
        except Exception as e:
            print(format_exc())
            return await ctx(f"There was an error: {e}\nIf you don't know the problem please screenshot this together with your command and say `{ctx.prefix}feedback <upload your screenshot, or say what you want to say>` send the error to the bot owner.")

    @server.command(description="See the roles in the server")
    async def roles(self, ctx, sv: int = None):
        if sv is None: server = ctx.guild
        else: server = self.bot.get_guild(sv)
        try:
            roles = [str(a.mention) for a in server.roles]
            def func(lines, chars=2000):
                message, size = [], 0
                for line in lines:
                    if len(line) + size > chars:
                        yield message
                        message, size = [], 0
                    message.append(line)
                    size += len(line)
                yield message
            for message in func(roles):
                try: embed = Embed(color=Colour.lighter_grey(), description=', '.join(message))
                except: return await ctx.send(', '.join(message))
                return await ctx.send(embed=embed)
        except HTTPException:
            await ctx.send("Error: This server probably has a high number or roles which aren't allowed on embeds")

    @server.command(description="See info about the server members")
    async def members(self, ctx, svID: int = None):
        server = self.bot.get_guild(svID) or ctx.guild
        pltPie((
            sum(x.status.value == 'online' for x in server.members),
            sum(x.status.value == 'offline' for x in server.members),
            sum(x.status.value == 'dnd' for x in server.members),
            sum(x.status.value == 'idle' for x in server.members)),
                labels=None,
                colors=('#43b581', '#747f8d', '#f04747', '#faa61a'),
                shadow=False,
                startangle=140)
        pltAxis('equal')
        pltSavefig('memb_piechart', transparent=True)
        await ctx.send(file=File("memb_piechart.png"), embed=Embed(title="Members in the server")
            .add_field(name="Members:", value=F"<:online:666002136567513088>Online: {sum(not x.bot and x.status.value == 'online' for x in server.members)}\n<:Idle:664140822672834580>Idle: {sum(not x.bot and x.status.value == 'idle' for x in server.members)}\n<:dnd:664140822295347221>DND: {sum(not x.bot and x.status.value == 'dnd' for x in server.members)}\n<:offline:664140822823829514> Offline: {sum(not x.bot and x.status.value == 'offline' for x in server.members)}\n<:Sum:663243303478886461>Sum: {sum(not x.bot for x in server.members)}")
            .add_field(name="Bots:", value=F"<:online:666002136567513088>Online: {sum(x.bot and x.status.value == 'online' for x in server.members)}\n<:Idle:664140822672834580>Idle: {sum(x.bot and x.status.value == 'idle' for x in server.members)}\n<:dnd:664140822295347221>DND: {sum(x.bot and x.status.value == 'dnd' for x in server.members)}\n<:offline:664140822823829514> Offline: {sum(x.bot and x.status.value == 'offline' for x in server.members)}\n<:Sum:663243303478886461>Sum: {sum(x.bot for x in server.members)}")
            .add_field(name="Information on Pie chart", value="_ _", inline=False)
            .set_thumbnail(url=server.icon_url)
            .set_footer(text=f"Say \"{ctx.prefix}newmembers [number]\"to see the newest members in the server")
            .set_image(url="attachment://memb_piechart.png"))
        os_rem('memb_piechart.png')

    @server.command(name="invites", description="See servers active invites")
    async def serverInvites(self, ctx, svID: int = None):
        server = self.bot.get_guild(svID) or ctx.guild
        try:
            invites = {str(invite) for invite in await server.invites()}
            if not invites: return await ctx.send("There're currently no active invite links in this server")
            else: return await ctx.send(embed=Embed(colour=colrs[4])
                .add_field(name=f"Total invite links: {len(invites)}", value="   <:link:663295066357497857> \n".join(map(str, invites))+"   <:link:663295066357497857> ")
                .set_footer(text=f"Say \"{ctx.prefix}invite info <invite>\" for info about an invite"))
        except Forbidden:
            return await ctx.send("I can't show invites because I don't have `Manage server` permissions")

    @server.command(name="info", description="Use to see information about the server")
    async def serverInfo(self, ctx, severID: int = None):
        try:
            embed, loading, server = Embed(), await ctx.send(loading_msg("Gathering server information")), self.bot.get_guild(severID) or ctx.guild
            voiceC, textC, stageC, prefixes = server.voice_channels, server.text_channels, server.stage_channels, botPrefixDB.find_one({'_id': f'{ctx.guild.id}'})
            if server.icon_url:
                try:
                    color_thief = ColorThief(IoBytesIO(await aiohttp_request(str(server.icon_url_as(format='png')), 'read')))
                    color_thief.get_color(quality=1)
                    palette = color_thief.get_palette(color_count=6)
                    x, y, z = palette[4][0] if len(palette) >= 6 else palette[0][0], palette[4][1] if len(
                        palette) >= 6 else palette[0][1], palette[4][2] if len(palette) >= 6 else palette[0][2]
                    iconCol = Colour(int('0x%02x%02x%02x' % (x, y, z), 16))
                    embed.color = iconCol
                    # img = Image.open(IoBytesIO(await aiohttp_request(str(server.icon_url_as(format='png')), 'read')))
                    # img = img.convert("RGB")
                    # img = img.resize((1, 1), resample=0)
                    # embed = Embed(colour=Colour.lighter_grey(), description=f"{server.name}")
                    # embed.color = Colour(int('0x%02x%02x%02x' % img.getpixel((0, 0)), 16))
                except: print(f"{format_exc()}\n - {lineNum(True)}")
            embed.set_thumbnail(url=server.icon_url).set_footer(text=f"Looking for my info? The command is '{ctx.prefix}info'")
            embed.add_field(name="Owner", value=server.owner, inline=True)
            embed.add_field(name="ID", value=server.id, inline=True)
            if type(server.region) != str:
                embed.add_field(name='Region', value=server.region.value.capitalize(), inline=True)
            embed.add_field(name='Name', value=server.name, inline=True)
            embed.add_field(name="Created on", value=f"{server.created_at:%d/%m/%Y} ({(ctx.message.created_at - server.created_at).days} days ago)", inline=True)
            embed.add_field(name="System channel", value=server.system_channel.mention if server.system_channel else None, inline=True)
            embed.add_field(name="Server description", value=server.description, inline=True)
            embed.add_field(name="Shard ID", value=server.shard_id, inline=True)
            embed.add_field(name="Server Icon", value=f"[Click Here]({server.icon_url})" if len(server.icon_url) >= 2 else None, inline=True)
            embed.add_field(name="Server features", value=(", ".join(server.features)).capitalize().replace('_', ' ') if server.features else None, inline=len(server.features) <= 5)
            embed.add_field(name="Server emotes", value=len(server.emojis), inline=True)
            embed.add_field(name="Roles", value=len(server.roles), inline=True)
            embed.add_field(name="Premium boosters", value=server.premium_subscription_count, inline=True)
            embed.add_field(name="Members", value=f"\
                <:online:666002136567513088>{sum(x.status.value == 'online' and x.bot for x in server.members)} bots, {sum(x.status.value == 'online' and not x.bot for x in server.members)} {'person' if sum(x.status.value == 'online' and not x.bot for x in server.members) == 1 else 'people'}\n\
                <:Idle:664140822672834580>{sum(x.status.value == 'idle' and x.bot for x in server.members)} bots, {sum(x.status.value == 'idle' and not x.bot for x in server.members)} {'person' if sum(x.status.value == 'idle' and not x.bot for x in server.members) == 1 else 'people'}\n\
                <:dnd:664140822295347221>{sum(x.status.value == 'dnd' and x.bot for x in server.members)} bots, {sum(x.status.value == 'dnd' and not x.bot for x in server.members)} {'person' if sum(x.status.value == 'dnd' and not x.bot for x in server.members) == 1 else 'people'}\n\
                <:offline:664140822823829514> {sum(x.status.value == 'offline' and x.bot for x in server.members)} bots, {sum(x.status.value == 'offline' and not x.bot for x in server.members)} {'person' if sum(x.status.value == 'offline' and not x.bot for x in server.members) == 1 else 'people'}\n\
                <:Sum:663243303478886461>{server.member_count} in total", inline=True)
            embed.add_field(name="Channels", value=f"\
                <:Textchannel:776521784307875891> {len(textC)}\n\
                <:Voicechannel:776521783980326944> {len(voiceC)}\n\
                <:Stagechannel:866906785842200636> {len(stageC)}\n\
                {len(voiceC) + len(textC) + len(stageC)} Total channels", inline=True)
            embed.add_field(name="Nitro boosting level", value=server.premium_tier, inline=True)
            
            try: embed.add_field(name="Active invites", value=len(await server.invites()), inline=True)
            except: pass
            try: embed.set_image(url=server.banner_url)
            except: pass
            embed.add_field(name="Animated icon?", value="Yes" if server.is_icon_animated() else "No", inline=True)
            embed.add_field(name="My prefix", value=prefixes.get('prefix', '...') if prefixes else '...', inline=True)

            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Looks like I fell into a little error; {e}")
            print(format_exc(), lineNum(True))
        finally:
            try: await loading.delete()
            except: print(format_exc(), lineNum(True))

    @server.command(aliases=("emojis",), description="See custom emojis in the server")
    async def emotes(self, ctx, sv: int = None):
        if sv is None: server = ctx.guild
        else: server = self.bot.get_guild(sv)
        try:
            emotes = [str(x) for x in server.emojis]
            def func(lines, chars=2000):
                message, size = [], 0
                for line in lines:
                    if len(line) + size > chars:
                        yield message
                        message, size = [], 0
                    message.append(line)
                    size += len(line)
                yield message
            for message in func(emotes): await ctx.send(embed=Embed(
                color=Colour.lighter_grey(),
                description=' '.join(message))
                    .set_footer(text=f"{len(server.emojis)} emojis in the server"))
        except:
            try:
                emotes = [str(x) for x in server.emojis]
                def func(lines, chars=2000):
                    message, size = [], 0
                    for line in lines:
                        if len(line) + size > chars:
                            yield message
                            message, size = [], 0
                        message.append(line)
                        size += len(line)
                    yield message
                for message in func(emotes): return await ctx.send(' '.join(message))
            except Exception as e:
                await ctx.send(e)

    @server.command(hidden=True, name="list", description="See all the servers I'm in")
    async def serverList(self, ctx):
        if ctx.author.id not in access_ids: return # Not allowed to everyone if adding bot to top.gg
        await ctx.send(embed=Embed(title="All servers I'm powering:", description="```\n" + ', '.join(map(str, self.bot.guilds)) + "```", colour=0x0af78a)
            .add_field(name=f"<:Server:663296208537911347> {len(self.bot.guilds)} Servers", value="[Remove yours](https://i.imgur.com/I4tUSRF.png)", inline=True)
            .add_field(name=f"<:Users:663295067280244776> {len(set(self.bot.get_all_members()))} users", value=f"[Invite me](https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=1479928959)", inline=True))

    @group(invoke_without_command=True, aliases=("who",), description="See number of messages, avatar, permision, information about a server member and more")
    async def user(self, ctx): await ctx.send(embed=Embed(
        color=colrs[4], title="All user commands:",
        description="\n".join(x for x in Cmds.server if (x.startswith('user')))))

    @user.command(aliases=("msg", "messages",), description="See how many messages you or a server member has sent in a channel")
    async def msgs(self, ctx, user: Member = None):
        try:
            user, msgs = user or ctx.author, 0
            loading = await ctx.send(loading_msg(f'Counting messages from {escape_mentions(user.display_name)} in this channel. This could take long...'))
            async for elem in ctx.channel.history(limit=None):
                if elem.author.id == user.id: msgs += 1
            await ctx.send(escape_mentions(("I have" if user == self.bot.user else f"{user.display_name} has") + f" sent {msgs} messages in {ctx.channel.mention} so far"))
        except: print(format_exc())
        finally: await loading.delete()

    @user.command(aliases=("img", "pfp", "av",), description="See a server member's avatar image")
    async def avatar(self, ctx, user: Member = None):
        ignore = (access_ids[0], 663074487335649292)
        if not user: user = ctx.author
        if user.id in ignore and ctx.author.id not in ignore: return await ctx.send('https://media1.tenor.com/images/17a17ae6b93faf667b39af6d8fe34d68/tenor.gif')
        try: await ctx.send(embed=Embed(title=f"{user.display_name}'s avatar",
            description=f"Download [ [PNG]({user.avatar_url_as(format='png')}) | [WEBP]({user.avatar_url_as(format='webp')}) | [JPEG]({user.avatar_url_as(format='jpeg')}) | [JPG]({user.avatar_url_as(format='jpg')})" + (f" | [GIF]({user.avatar_url_as(format='gif')}) ]" if user.is_avatar_animated() else " ]"))
            .set_image(url=user.avatar_url)
            .set_footer(text=f"As requested by {ctx.author.display_name}"))
        except Exception as e:
            await ctx.send(f"There was an error:\n{e}")
            return print(f"User avatar command failed with error \n{format_exc()}\n - By {ctx.author.name} in the {ctx.guild.name} server")

    @user.command(name="info", aliases=("is", "about",), brief="Get information about a server member", description="Information includes when they joined the server, when they created their discord account and more")
    async def userInfo(self, ctx, member: Member = None):  # sourcery no-metrics
        try:
            member, loading = member or ctx.author, await ctx.send(loading_msg("Getting information..."))
            col = member.color

            if member.avatar_url:
                try:
                    img = Image.open(IoBytesIO(await aiohttp_request(str(member.avatar_url_as(format='png')), 'read')))
                    img = img.convert("RGB")
                    img = img.resize((1, 1), resample=0)
                    col = Colour(int('0x%02x%02x%02x' % img.getpixel((0, 0)), 16))
                except:
                    print(f"{format_exc()}\n - {lineNum(True)}")
                    if str(member.color) == "#000000":
                        col = member.status == 0xf04747 if Status.do_not_disturb else 0x43b581 if member.status == Status.online else 0xfaa61a if member.status == Status.idle else 0x747f8d
            else:
                if str(member.color) == "#000000":
                    col = member.status == 0xf04747 if Status.do_not_disturb else 0x43b581 if member.status == Status.online else 0xfaa61a if member.status == Status.idle else 0x747f8d

            embed = Embed(color=col)
            embed.set_thumbnail(url=member.avatar_url)
            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar_url)
            embed.add_field(name="Name", value=f"{member.name}#{member.discriminator}", inline=True)
            embed.add_field(name="ID", value=member.id, inline=True)
            embed.add_field(name="Animated Avatar", value="Yes" if member.is_avatar_animated() else "No", inline=True)
            embed.add_field(name="Nickname", value=member.nick, inline=True)
            embed.add_field(name="Top Role", value=member.top_role.name if not member.top_role.is_default() else None, inline=True)
            embed.add_field(name="Active on mobile?", value="Yes" if member.is_on_mobile() else "No", inline=True)
            embed.add_field(name="Status", value=(f"<:online:666002136567513088>" if member.status==Status.online else f"<:offline:664140822823829514>" if member.status == Status.offline else f"<:dnd:664140822295347221>" if member.status==Status.do_not_disturb else f"<:Idle:664140822672834580>" if member.status==Status.idle else "") +member.status.value, inline=True)
            roles = [x for x in member.roles if not x.is_default()]
            try:
                if str(member.color) == "#000000": embed.add_field(name="Name color", value=f"Default", inline=True)
                else:
                    emoji = await tstGuild().create_custom_emoji(name=f"color", image=await aiohttp_request(f'http://www.colorhexa.com/{str(member.color)[1:]}.png', 'read'))
                    embed.add_field(name="Name color", value=f"{member.color} │ {emoji}", inline=True)
            except:
                if len(member.roles) >= 2: embed.add_field(name="Name color", value=f"{member.color}", inline=True)
                else: embed.add_field(name="Name color", value=f"Default", inline=True)
            embed.add_field(name="Avatar URL", value=f"[Click Here]({member.avatar_url})", inline=True)
            embed.add_field(name="Activity", value='No activity' if not member.activity
                else f"Playing {member.activity.name}" if member.activity.type == ActivityType.playing
                else f"Watching {member.activity.name}" if member.activity.type == ActivityType.watching
                else f"Listening to {member.activity.name}" if member.activity.type == ActivityType.listening
                else member.activity.name, inline=True)
            embed.add_field(name="Bot Account", value="Yes" if member.bot else "No", inline=True)
            embed.add_field(name="Joined Server on", value=f"{member.joined_at:%d/%m/%Y} ({(ctx.message.created_at - member.joined_at).days} days ago)", inline=True)
            embed.add_field(name="Joined Discord on", value=f"{member.created_at:%d/%m/%Y} ({(datetime.now() - member.created_at).days} days ago)", inline=True)
            if member.bot:
                try:
                    botInfo = await dblpy.http.get_bot_info(member.id)
                    if botInfo.get('prefix'): embed.add_field(name="Prefix:", value=botInfo['prefix'], inline=True)
                    if botInfo.get('lib'): embed.add_field(name="Library:", value='Unknown' if botInfo['lib'].lower() == 'other' else botInfo['lib'], inline=True)
                    if botInfo.get("owners"):
                        if len(botInfo['owners']) > 1:
                            try: embed.add_field(name="Developers:", value=", ".join(str(self.bot.get_user(int(ID))) for ID in botInfo['owners']), inline=True)
                            except:
                                embed.add_field(name="Developer IDs:", value=", ".join(map(str, botInfo['owners'])), inline=True)
                                print(format_exc())
                        else:
                            try: embed.add_field(name="Developer:", value=", ".join(str(self.bot.get_user(int(ID))) for ID in botInfo['owners']), inline=True)
                            except: embed.add_field(name="Developer's ID:", value=", ".join(map(str, botInfo['owners'])), inline=True)
                    if botInfo.get("server_count"): embed.add_field(name="Bot is in:", value=f"{botInfo['server_count']} servers", inline=True)
                    if botInfo.get("tags"): embed.add_field(name="Categories", value=f', '.join(str(tag).lower() for tag in botInfo['tags']), inline=True)
                    if botInfo.get("shortdesc"): embed.add_field(name="Short description", value=botInfo['shortdesc'], inline=True)
                except: pass
            embed.add_field(
                name=f"Roles ({len(roles)})",
                value=", ".join(role.mention for role in roles)
                if roles
                else 'No roles',
                inline=True,
            )

            await ctx.send(embed=embed)
        except Exception as e: await ctx.send(embed=Embed(
            title="There was an error:",
            description=f"```\n{e}\n - {lineNum(True)}\n```\nPlease send that error to bot owner if you don't know what's wrong"))
        finally:
            await loading.delete()
            try: await emoji.delete()
            except: pass

    @user.command(name="perms", description="See yours or someones permissions in the server")
    async def userPerms(self, ctx, member: Member = None, server_ID: int = None):
        guild = self.bot.get_guild(server_ID) or ctx.guild
        if not member: member = ctx.author
        perms = member.guild_permissions
        return await ctx.send(embed=Embed(color=colrs[4])
            .add_field(name="Kick Members", value=perms.kick_members, inline=True).add_field(name="Ban Members", value=perms.ban_members, inline=True)
            .add_field(name="Manage Channels", value=perms.manage_channels, inline=True).add_field(name="Manage Server", value=perms.manage_guild, inline=True)
            .add_field(name="Add Reactions", value=perms.add_reactions, inline=True).add_field(name="View Audit Log", value=perms.view_audit_log, inline=True)
            .add_field(name="Read Messages", value=perms.read_messages, inline=True).add_field(name="Send Messages", value=perms.send_messages, inline=True)
            .add_field(name="Manage Messages", value=perms.manage_messages, inline=True).add_field(name="Mention Everyone", value=perms.mention_everyone, inline=True)
            .add_field(name="Manage Nicknames", value=perms.manage_nicknames, inline=True).add_field(name="Manage Roles", value=perms.manage_roles, inline=True)
            .add_field(name="Manage Webhooks", value=perms.manage_webhooks, inline=True).add_field(name="Manage Emojis", value=perms.manage_emojis, inline=True)
            .add_field(name="Move Members", value=perms.move_members, inline=True).add_field(name="Mute Members", value=perms.mute_members, inline=True)
            .add_field(name="Read Message History", value=perms.read_message_history, inline=True).add_field(name="Send TTS Messages", value=perms.send_tts_messages, inline=True)
            .add_field(name="Change Nickname", value=perms.change_nickname, inline=True).add_field(name="Mange Nicknames", value=perms.manage_nicknames, inline=True)
            .add_field(name="Embed Links", value=perms.embed_links, inline=True).add_field(name="Mute members", value=perms.mute_members, inline=True)
            .set_author(name=f"{member.name}'s permissions in {guild.name}", icon_url=member.avatar_url)
            .set_footer(text=f"{member} is the server owner" if guild.owner == member else f"{member.name} is an administrator" if perms.administrator else " "))
    
    @group(aliases=('emote',), invoke_without_command=True, description="Used to add an emoji to server, see information about it like who created it etc. You can also use it to steal an emoji to any of the servers I'm in, If no paremeters give it shows the emoji image")
    async def emoji(self, ctx, *, msg=None):
        if not msg:
            return await ctx.send(embed=Embed(color=colrs[4], title="All emoji commands:",
                description="\n".join(x for x in Cmds.server if (x.startswith('emoji')))))
        def find_emoji(msg):
            msg, colors, name = re_sub("<a?:(.+):([0-9]+)>", "\\2", msg), ("1f3fb", "1f3fc", "1f3fd", "1f44c", "1f3fe", "1f3ff"), None
            for guild in self.bot.guilds:
                for emoji in guild.emojis:
                    if msg.strip().lower() in emoji.name.lower():
                        url, id, name, guild_name = emoji.url, emoji.id, emoji.name + (".gif" if emoji.animated else ".png"), guild.name
                    if msg.strip() in (str(emoji.id), emoji.name):
                        url, name = emoji.url, emoji.name + (".gif" if emoji.animated else ".png")
                        return name, url, emoji.id, guild.name
            if name: return name, url, id, guild_name
            
            # Check for a stock emoji before returning a failure
            codepoint_regex = re_compile(r'([\d#])?\\[xuU]0*([a-f\d]*)')
            unicode_raw = msg.encode('unicode-escape').decode('ascii')
            codepoints = codepoint_regex.findall(unicode_raw)
            if codepoints == []: return "", "", "", ""
            if len(codepoints) > 1 and codepoints[1][1] in colors: codepoints.pop(1)
            if codepoints[0][0] == '#': emoji_code = '23-20e3'
            elif codepoints[0][0] == '':
                codepoints = [x[1] for x in codepoints]
                emoji_code = '-'.join(codepoints)
            else: emoji_code = f"3{codepoints[0][0]}-{codepoints[0][1]}"
            url = f"https://raw.githubusercontent.com/astronautlevel2/twemoji/gh-pages/128x128/{emoji_code}.png"
            name = "emoji.png"
            return name, url, "N/A", "Official"

        emojis = msg.split()
        if msg.startswith('s '): emojis, get_guild  = emojis[1:], True
        else: get_guild = False
        if len(emojis) > 5: return await ctx.send("Maximum of 5 emojis at a time.")
        images = []
        for emoji in emojis:
            name, url, id, guild = find_emoji(emoji)
            if not url:
                await ctx.send(f"Could not find {emoji}. Skipping.")
                continue
            images.append((guild, str(id), url, File(IoBytesIO(await aiohttp_request(str(url), 'read')), name)))
        
        for (guild, id, url, file) in images:
            if ctx.channel.permissions_for(ctx.author).attach_files:
                if get_guild: await ctx.send(content=f'**ID:** {id}\n**Server:** {guild}', file=file)
                else: await ctx.send(file=file)
            else:
                if get_guild: await ctx.send(f'**ID:** {id}\n**Server:** {guild}\n**URL: {url}**')
                else: await ctx.send(url)
            file.close()

    @emoji.command(description="Copy an emoji from any of the servers bot is in.\nThe bot'll look through all the servers it is in to find an emoji with the given name, if found bot'll copy that emoji (name and image) and add it to this server.")
    async def copy(self, ctx, *, msg):
        try:
            loading, match = await ctx.send(loading_msg("Looking through servers for this emoji name")), None
            if not ctx.author.guild_permissions.manage_emojis: return await ctx.send("You must have `Manage Emojis` permission to copy emojis")
            for guild in self.bot.guilds:
                for emoji in guild.emojis:
                    if emoji.name.lower() == msg.lower():
                        match = emoji
            if not match: return await ctx.send('Could not find emoji.')
            emoji = await ctx.guild.create_custom_emoji(name=match.name, image=(await aiohttp_request(f"{match.url}", 'read')))
            await ctx.send(f"Successfully added the emoji {emoji.name} <{'a' if emoji.animated else ''}:{emoji.name}:{emoji.id}>!")
        except:
            print(format_exc())
            await ctx.send(f"Fell into an error on line {lineNum()}, please send the following error to my developer\n {format_exc()}")
        finally: await loading.delete()

    @emoji.command(name="add", description="Add emoji to server.\nGive emoji name wich will be used to name the emoji and image url which will be used as emoji image when I create the emoji. If name name given, bot'll go for name in url. I must have manage_emojis permissions first to do this.")
    async def emojiAdd(self, ctx, url='', *, name=None):
        if ctx.author.guild_permissions.manage_emojis:
            if not url: return await ctx.send(f"You must say a link, Usage: `{ctx.prefix}emoji add <link to an image> <name> `")
            if not name:
                if '.' in url: name = url.split('.')[-2]
                name = name.split('/')[-1]
            elif " " in name: name = "".join(x.capitalize() for x in name.split())
            try: response = await aiohttp_request(url, 'read')
            except:
                print(format_exc())
                return await ctx.send(f"This url `{url}` you have provided is invalid or not well formed.")
            if (await aiohttp_request(url)).status == 404: return await ctx.send("The URL link you have provided leads to a 404 (not found) page.")
            emoji = await ctx.guild.create_custom_emoji(name=name, image=response)
            await ctx.send(f"Successfully added the emoji \"`{emoji.name}`\" <{'a' if emoji.animated else ''}:{emoji.name}:{emoji.id}>")
        else: await ctx.channel.send("You must have `Manage Emojis` permission to add an emoji")

    @emoji.command(name="del", description="To remove an emoji that matches the name you give for you.")
    async def delete(self, ctx, name):
        if not ctx.author.guild_permissions.manage_emojis: return await ctx.channel.send("You need '`Manage Emojis`' to use this ccommand.")
        if not ctx.guild.me.guild_permissions.manage_emojis: return await ctx.channel.send("I need '`Manage Emojis`' permission to delete an emoji.")
        if search := re_search(r'<:(\w+):\d{10,}>', name): name = search[1]
        else: name = name.replace(':', '')
        emotes, emote_length = [x for x in ctx.guild.emojis if x.name == name], 0
        if not emotes: return await ctx.send(f"I couldn't find any custom emojis with the name `{name}` in this server.")
        for emote in emotes:
            try:
                await emote.delete()
                emote_length+=1
            except: return await ctx.send('There was an error deleting')
        await ctx.send(f"Successfully deleted the emoji '`{emotes[0].name}`'" if emote_length == 1 else f"Successfully removed {emote_length} emojis.")
    
    @emoji.command(aliase="rename", description="To rename an emoji that matches the name you give.")
    async def ren(self, ctx, name, new_name):
        if not ctx.author.guild_permissions.manage_emojis: return await ctx.channel.send("You need '`Manage Emojis`' to use this ccommand.")
        if not ctx.guild.me.guild_permissions.manage_emojis: return await ctx.channel.send("I need '`Manage Emojis`' permission to rename an emoji.")
        if search := re_search(r'<:(\w+):\d{10,}>', name): name = search[1]
        else: name = name.replace(':', '')
        emotes, emote_length = [x for x in ctx.guild.emojis if x.name == name], 0
        if not emotes: return await ctx.send(f"I couldn't find any custom emojis with the name `{name}` in this server.")
        for emote in emotes:
            try:
                await emote.edit(name=new_name)
                new_name, emote_length = self.bot.get_emoji(emote.id), emote_length+1
            except: return await ctx.send('There was an error renaming')
        await ctx.send(f"Successfully renamed the emoji from '`{emotes[0].name}`'" if emote_length == 1 else f"Successfully renamed {emote_length} emojis.")

    @emoji.command(name="info", description="Shows information about emoji.\nShows information about emoji like who added it to the server, when it was added, or to get the it's image and more.")
    async def emojiInfo(self, ctx, emoji:Emoji):
        try:
            embed = Embed()
            embed.add_field(name="Name", value=emoji.name, inline=True)
            embed.add_field(name="ID", value=emoji.id, inline=True)
            if emoji.user is None:
                try:
                    emoji2 = await ctx.guild.fetch_emoji(emoji.id)
                    embed.add_field(name="Creator", value=emoji2.user, inline=True)
                except: pass
            else: embed.add_field(name="Creator", value=emoji.user, inline=True)
            embed.add_field(name="Animated?", value="Yes" if emoji.animated else "No", inline=True)
            embed.add_field(name="Created on", value=emoji.created_at.strftime("%d/%m/%y"), inline=True)
            embed.add_field(name="Requires colons?", value="Yes" if emoji.require_colons else "No", inline=True)
            embed.add_field(name="Emoji Icon", value=f"[Click Here]({emoji.url})", inline=True)
            embed.add_field(name="Server it's made in", value=emoji.guild, inline=True)
            embed.add_field(name="Managed by a Twitch integration?", value="Yes" if emoji.managed else "No", inline=True)
            if not emoji.roles: embed.add_field(name="Roles allowed to use it", value="All roles", inline=True)
            else: embed.add_field(name="Roles allowed to use it", value=', '.join(map(lambda r: r.mention,  emoji.roles)), inline=True)
            try: embed.set_thumbnail(url=emoji.url)
            except: pass
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"There was an error:\n```\n{e}\n```\nPlease send the above error to my developer if you don't know what is wrong")

    @command(invoke_without_command=True, brief="Get mine or a certain bot's invite, or get info about an invite link", description="**Examples:**\n\t<<prefix>>invite\n\t<<prefix>>invite @MEE6\n\t<<prefix>>invite info <discord server invite>")
    async def invite(self, ctx, user=None, invite = None):
        if not user or user == self.bot.user:
            embed = Embed(color=colrs[1], title=None, description=f"<:link:663295066357497857>  [Invite me](https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=1479928959)\nBot is currently still in beta. If you have some feedback please let me know.\nYou can also get invite link to another bot and probably some info about it by pinging it or saying it's ID with the command eg. `{ctx.prefix}invite @{ctx.guild.me.display_name}`", colour=Colour.green())
            embed.set_thumbnail(url="https://i.imgur.com/CNYbdaV.png")
            embed.set_footer(text=f"Looking for this server's invites instead? Say \"{ctx.prefix}server invites\"")
            await ctx.send(embed=embed)
        
        if user.lower() == "info": #inviteinfo
            if not invite: return await ctx.send('No Discord server invite provided')
            invite = await self.bot.fetch_invite(re_sub(r"(https?:\/\/)?((discord\.gg\/)|(.+\/invite\/))", "", re_sub('[<>]', '', invite)))
            if not invite: return await ctx.send(f'Invite not found, is it a discord server invite?')
            data = Embed(title="**Information about Invite:** %s" % invite.id)
            if invite.revoked: data.colour = Colour.red() if invite.revoked else Colour.green()
            data.add_field(name="Expires", value=f"{invite.max_age:%s} seconds" if invite.max_age else "Never")
            data.add_field(name="Temp membership", value="Yes" if invite.temporary else "No")
            data.add_field(name="Uses", value=invite.uses, inline=False)
            if invite.guild.name:
                data.add_field(name="Server", value="**Name:** " + invite.guild.name + "\n**ID:** %s" % invite.guild.id, inline=True)
            if invite.guild.icon_url:
                data.set_thumbnail(url=invite.guild.icon_url)
            if invite.channel.name:
                channel = "%s\n#%s" % (invite.channel.mention, invite.channel.name) if isinstance(invite.channel, TextChannel) else invite.channel.name
                data.add_field(name="Channel", value=f"**Name:** {channel}\n**ID:** {invite.channel.id}", inline=True)
            try:
                data.add_field(name="Total members", value=invite.approximate_member_count, inline=True)
                data.add_field(name="Active members", value=invite.approximate_presence_count, inline=True)
            except: pass
            if invite.inviter.name: data.set_footer(
                text="Creator: "+invite.inviter.name + '#' + invite.inviter.discriminator + " (%s)" % invite.inviter.id,
                icon_url=invite.inviter.avatar_url)
            try: return await ctx.send(embed=data)
            except: await ctx.send(content="I need the `Embed links` permission to send this")
        
        elif user.isdigit():
            try:
                member, embed = self.bot.get_user(int(user)), Embed(color=Colour.green(), title="Bot invite")
                try:
                    botInfo = await dblpy.http.get_bot_info(member.id)
                    if botInfo.get("id") and botInfo.get("avatar"): embed.set_thumbnail(url=member.avatar_url)
                    if botInfo.get("username"): embed.description = f"<:link:663295066357497857>  [Invite {botInfo['username']}]({botInfo['invite'] if botInfo.get('invite') else f'https://discordapp.com/oauth2/authorize?client_id={user}&scope=bot&permissions=2146958839'})"
                    else: embed.description = f"Click below to invite the bot with that ID\n<:link:663295066357497857>  [Bot invite](https://discordapp.com/oauth2/authorize?client_id={user}&scope=bot&permissions=2146958839)"
                    if botInfo.get('prefix'):
                        embed.add_field(name="Prefix:", value=botInfo['prefix'], inline=True)
                    if botInfo.get('lib'):
                        embed.add_field(name="Library:", value='Unknown' if botInfo['lib'].lower() == 'other' else botInfo['lib'], inline=True)
                    if botInfo.get("owners"):
                        if len(botInfo['owners']) > 1:
                            try: embed.add_field(name="Developers:", value=", ".join(str(self.bot.get_user(int(ID))) for ID in botInfo['owners']), inline=True)
                            except:
                                embed.add_field(name="Developer IDs:", value=", ".join(map(str, botInfo['owners'])), inline=True)
                                print(format_exc())
                        else:
                            try: embed.add_field(name="Developer:", value=", ".join(str(self.bot.get_user(int(ID))) for ID in botInfo['owners']), inline=True)
                            except: embed.add_field(name="Developer's ID:", value=", ".join(map(str, botInfo['owners'])), inline=True)
                    if botInfo.get("server_count"):
                        embed.add_field(name="Bot is in:", value=f"{botInfo['server_count']} servers", inline=True)
                    if botInfo.get("tags"): embed.add_field(name="Categories", value=f', '.join(str(tag).lower() for tag in botInfo['tags']), inline=True)
                    embed.set_footer(text="If you meant to invite me say the command without an ID.")
                except:embed.description = f"Click below to invite the bot with that ID\n<:link:663295066357497857>  [Bot invite](https://discordapp.com/oauth2/authorize?client_id={user}&scope=bot&permissions=2146958839)"
                await ctx.send(embed=embed)
            except AttributeError:
                await ctx.send(f"Error: Check if the ID is right or if the bot is in any server I'm in `{ctx.prefix}invite [bot ID OR ping a bot]`")
        
        elif '<@' and '>' in user:
            member, embed = self.bot.get_user(tryInt(user.strip(' <@!&> '))), Embed(color=Colour.green(), title="Bot invite")
            if not member:
                if r := ctx.guild.get_role(tryInt(user.strip(' <@!&> '))):
                    if r.managed and len(r.members) == 1 and sum(m.bot for m in r.members):member = r.members[0]
                    else: return await ctx.send(escape_mentions(f"\"{r.name}\" is neither a bot nor a bot role but a role"))
                else: return await ctx.send(f'Member not found, perhaps they\'re nolonger part of this server')
            if not member.bot: return await ctx.send(escape_mentions(f'{member.display_name} isn\'t a bot'))
            try:
                botInfo = await dblpy.http.get_bot_info(member.id)
                if botInfo.get("id") and botInfo.get("avatar"):
                    embed.set_thumbnail(url=f"https://images.discordapp.net/avatars/{botInfo['id']}/{botInfo['avatar']}.png")
                if botInfo.get("username"):
                    embed.description = f"<:link:663295066357497857>  [Invite {botInfo['username']}]({botInfo['invite'] if botInfo.get('invite') else f'https://discordapp.com/oauth2/authorize?client_id={member.id}&scope=bot&permissions=2146958839'})"
                else: embed.description = f"Click below to invite {member.display_name}\n<:link:663295066357497857>  [Bot invite](https://discordapp.com/oauth2/authorize?client_id={member.id}&scope=bot&permissions=2146958839)"
                if botInfo.get('prefix'): embed.add_field(name="Prefix:", value=botInfo['prefix'], inline=True)
                if botInfo.get('lib'): embed.add_field(name="Library:", value='Unknown' if (botInfo['lib'].lower() == 'other') else botInfo['lib'], inline=True)
                if botInfo.get("owners"):
                    if len(botInfo['owners']) > 1:
                        try: embed.add_field(name="Developers:", value=", ".join(str(self.bot.get_user(int(ID))) for ID in botInfo['owners']), inline=True)
                        except:
                            embed.add_field(name="Developer IDs:", value=", ".join(map(str, botInfo['owners'])), inline=True)
                            print(format_exc())
                    else:
                        try: embed.add_field(name="Developer:", value=", ".join(str(self.bot.get_user(int(ID))) for ID in botInfo['owners']), inline=True)
                        except: embed.add_field(name="Developer's ID:", value=", ".join(map(str, botInfo['owners'])), inline=True)
                if botInfo.get("server_count"): embed.add_field(name="Bot is in:", value=f"{botInfo['server_count']} servers", inline=True)
                if botInfo.get("tags"): embed.add_field(name="Categories", value=f', '.join(str(tag).lower() for tag in botInfo['tags']), inline=True)
                embed.set_footer(text="If you meant to invite me say the command without pinging a bot.")
            except: embed.description = f"Click below to invite {member.display_name}\n<:link:663295066357497857>  [Bot invite](https://discordapp.com/oauth2/authorize?client_id={int(user.strip(' <@!> '))}&scope=bot&permissions=2146958839)"
            await ctx.send(embed=embed)
        
        else:
            await ctx.send(escape_mentions(f"Parameter \"{user}\" is not valid, please say `{ctx.prefix}help {ctx.command}` for help with the command."))

def setup(bot):
    bot.add_cog(Server(bot))