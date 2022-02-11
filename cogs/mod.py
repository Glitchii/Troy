from discord import Embed, Colour, Member, Object, PermissionOverwrite
from asyncio import sleep as asyncio_sleep
from discord.errors import Forbidden
from discord.ext.commands import command, Cog, Greedy
from imports import access_ids, colrs, opts, tryInt, loading_msg, mutedDB, aiohttp_request, fson
from datetime import datetime
from traceback import format_exc
from re import search as re_search
from json import loads as json_loads

class Mod(Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @Cog.listener()
    async def on_ready(self):
        print("Module: Mod loaded")
    
    @command(brief="Change everyones nickname to a certain name.", description="If not nickname is given with the command, everyone will be given random names.\nUse massunick to reverse")
    async def massnick(self, ctx, *, name:opts = False):
        if name and name.get('server') and ctx.author.id in access_ids: ctx.guild = self.bot.get_guild(int(name['server']))
        if not ctx.author.guild_permissions.manage_nicknames and not ctx.author.id in access_ids: return await ctx.send(f"You need '`Manage Nicknames`' permission to use the massnick command {ctx.author.mention}.")
        if not ctx.guild.me.guild_permissions.manage_nicknames: return await ctx.send(f"I need '`Manage Nicknames`' permission to change other people's nicknames.")
        await ctx.message.add_reaction(loading_msg(emoji=True))
        await ctx.send(ctx.guild)
        _dict = {}
        def filter_(m):
            return m.nick and m != self.bot.user
        for m in filter(filter_, ctx.guild.members):
            _dict[str(m.id)] = m.nick
        for m in ctx.guild.members:
            if m != self.bot.user:
                try: await m.edit(nick=name.get('text', (await aiohttp_request('https://randomuser.me/api/', 'json'))['results'][0]['name']['first']))
                except: pass
        await ctx.send(f"Command complete. To reset all the nicknames, copy and paste everything below:\n{ctx.prefix}massunnick" + f"\n```json\n{fson(_dict)}\n```" if _dict else "")
        await ctx.message.remove_reaction(loading_msg(emoji=True), ctx.guild.me)
        await ctx.message.add_reaction(self.bot.get_emoji(663230689860386846))
    
    @command(brief="Reset nicknames performed by massnick command.", description="If no JSON is provided, everyone's nickname will be removed.")
    async def massunnick(self, ctx, *, nicks:opts=None):
        if nicks and nicks.get('server') and ctx.author.id in access_ids: ctx.guild = self.bot.get_guild(int(nicks['server']))
        if not ctx.author.guild_permissions.manage_nicknames and not ctx.author.id in access_ids: return await ctx.send(f"You need '`Manage Nicknames`' permission to use this command {ctx.author.mention}.")
        if not ctx.guild.me.guild_permissions.manage_nicknames: return await ctx.send(f"I need '`Manage Nicknames`' permission to change other people's nicknames.")
        await ctx.message.add_reaction(loading_msg(emoji=True))
        if (nicks := nicks.get('text')) and (find := re_search(r"```(?:json|.*)\n*\s*(\{(.|\n)+\})\s*\n*\s*```\s*\n*$|(\{(.|\n)+\})", nicks)):
            try: nicks = json_loads(find.groups()[0])
            except:
                try: nicks = json_loads(nicks)
                except:
                    await ctx.send('JSON incorrect, has it been altered?')
                    return await ctx.message.remove_reaction(loading_msg(emoji=True), ctx.guild.me)
        else: nicks = {}
        for m in ctx.guild.members:
            try: await m.edit(nick=nicks.get(str(m.id)))
            except: pass
        await ctx.message.remove_reaction(loading_msg(emoji=True), ctx.guild.me)
        await ctx.message.add_reaction(self.bot.get_emoji(663230689860386846))


    @command(aliases=('purge',), description="Clear a number of messages you want from a channel or users")
    async def clear(self, ctx, limit:int, members:Greedy[Member]=None):
        if not ctx.author.id in access_ids and not ctx.author.guild_permissions.manage_messages: return await ctx.send("You need '`Manage Messages`' permissions.")
        if not ctx.guild.me.guild_permissions.manage_messages: return await ctx.send("'`Manage Messages`' permission is required to delete other people's messages, which I don't have.")
        if not members:
            deleted = await ctx.channel.purge(limit=limit+1)
            return await ctx.send(embed=Embed(description=f"<:Mark:663230689860386846> {len(deleted or '1')-1} message{'s have' if len(deleted or '1')-1 != 1 else ' has'} been deleted", color=colrs[2]), delete_after=10)
        for member in members: deleted = await ctx.channel.purge(limit=limit+1, check=lambda m:m.author == member)
        await (ctx.send(embed=Embed(description=f"<:Mark:663230689860386846> {len(deleted  or '1')-1} {'message from ' + f'{members[0]}' + ' has ' if len(deleted or '1')-1 == 1 else 'messages from ' + ' and '.join([', '.join(map(str, members[:-1])), str(members[-1])]) + ' have '}been deleted", color=colrs[2]), delete_after=10) if ctx.channel.permissions_for(ctx.guild.me).read_message_history else ctx.send(f"<:Mark:663230689860386846> {ctx.author} cleared {limit} {'message from ' + str(members[0]) if len(members) == 1 else 'messages from ' + ' and '.join([', '.join(map(str, members[:-1])), str(members[-1])])}\n*If some messages were not deleted, it's most likely I don't have 'view message history' permission in this channel*", delete_after=20))

    @command(aliases=('massban',), description="Ban a person. Just like a massban command, you can ban more than one person by seperating the names with a space eg.\n'ban @member1 @member2 [Optional reason]'  \n'massban' command is just an aliase to this.")
    async def ban(self, ctx, members:Greedy[Member], *, reason=None):
        if membrs := [m for m in members if m.top_role.position > ctx.author.top_role.position]: return await ctx.send(f"{membrs[0] if len(membrs) == 1 else ' and '.join([', '.join(map(str, membrs[:-1])), str(membrs[-1])])} can't be banned as their top role is higher than yours")
        if not reason: reason = f"Unspecified by {ctx.author}"
        if not members: return await ctx.send(f"You must say a valid ID, name, or ping a user in the server to {ctx.invoked_with} {ctx.author.mention}.")
        if not ctx.author.guild_permissions.ban_members: return await ctx.send("This command requires you have `Ban Members` permission.")
        if not ctx.guild.me.guild_permissions.ban_members: return await ctx.send("This command requires I have `Ban Members` permission.")
        ignored = []
        for member in members:
            if (member == ctx.guild.me or member == ctx.author) and len(members) == 1: return await ctx.message.add_reaction('🤔')
            try: await ctx.guild.ban(member, reason=reason)
            except: ignored.append(member)
        if ignored: return await ctx.send(f"I couldn't kick {ignored[0] if len(ignored) == 1 else ' and '.join([', '.join(map(str, ignored[:-1])), str(ignored[-1])])} as my role is under one or more of theirs")
        await ctx.send(embed=Embed(title=f"<:Mark:663230689860386846> Member(s) successfully banned", timestamp=datetime.now(), color = Colour.orange())
            .add_field(name="❔ Reason", value=f"```\n{reason}\n```" if not '`' in reason else reason, inline=True)
            .set_thumbnail(url="https://i.imgur.com/7F7Q4x9.png"))
    
    @command()
    async def unban(self, ctx, members: Greedy[Object], *, reason=None):
        if not reason: reason = f"Unspecified by {ctx.author}"
        if not ctx.author.guild_permissions.ban_members: return await ctx.send("This command requires you have `Ban Members` permission.")
        if not ctx.guild.me.guild_permissions.ban_members: return await ctx.send("This command requires I have `Ban Members` permission.")
        for member in members:
            if type(member) != Object: return await ctx.send(f"Couldn't find a member with the ID \"{member}\". Perhaps it's not correct?")
            try: await ctx.guild.unban(member, reason=reason)
            except Exception as e: return await ctx.send(f"Go the following error while trying to unban: `{e}`\nIf it's an 'Unknown Ban' error then the person whose ID you gave is probably not banned, or wrong ID, or deleted their account")
        
        await ctx.send(
            embed=Embed(
                title=f"<:Mark:663230689860386846> Member(s) successfully unbanned",
                value=f"```\n{reason}\n```" if not '`' in reason else reason,
                timestamp=datetime.now(),
                color=colrs[2],
            )
            .set_footer(text=f"'{ctx.prefix}banned' to check banned members in server")
            .set_thumbnail(url="https://i.imgur.com/7F7Q4x9.png"))
    
    @command()
    async def tempban(self, ctx, members:Greedy[Member], seconds, *, reason=None):
        if membrs := [m for m in members if m.top_role.position > ctx.author.top_role.position]: return await ctx.send(f"{membrs[0] if len(membrs) == 1 else ' and '.join([', '.join(map(str, membrs[:-1])), str(membrs[-1])])} can't be banned as their top role is higher than yours")
        if not reason: reason = f"Unspecified by {ctx.author}"
        if not seconds: return await ctx.send(f"You must say seconds to wait before unbanning after banning.")
        if not tryInt(seconds):
            if not members: return await ctx.send(f"There was a problem. If you pinged one or more members that have the same name as a certain role (most likely a bot), make sure you didn't accidentally ping the role instead of the member")
            return await ctx.send(f"Seconds must be full numbers not \"{seconds}\"")
        if not ctx.author.guild_permissions.ban_members: return await ctx.send("This command requires you have `Ban Members` permission.")
        if not ctx.guild.me.guild_permissions.ban_members: return await ctx.send("This command requires I have `Ban Members` permission.")
        wontBan, toBan, banned = [], [], []
        for member in members:
            if ctx.guild.me.top_role.position < member.top_role.position: wontBan.append(str(member))
            else: toBan.append(member)
        if toBan:
            for member in toBan:
                if (member == ctx.guild.me or member == ctx.author) and len(members) == 1: return await ctx.message.add_reaction('🤔')
                try: await ctx.guild.ban(member, reason=reason); banned.append(member.id)
                except: pass
        embed = Embed(title = "<:Cross:663201785237995520> Failed to ban", color = Colour.orange()).set_thumbnail(url="https://i.imgur.com/7F7Q4x9.png")
        if toBan:
            embed.title = f"<:Mark:663230689860386846> Membe{'rs' if len(toBan)>1 else 'r'} successfully banned for {seconds} seconds!"
            embed.set_footer(text=f"Reason: {reason}")
        if wontBan: embed.description = (embed.description or "") + (f"I can't ban the following members therefore skipped them. One or more of their top roles are over my top role. (This can be changed in the settings role section)\n```\n{', '.join(map(str, wontBan))}\n```\n" if len(wontBan)>1 else f"{wontBan[0]} hasn't been banned because one or more of his/her top roles are over my top role in the settings role section")
        await ctx.send(embed=embed)
        if banned:
            await asyncio_sleep(int(seconds))
            for iD in banned:
                try:
                    member = Object(iD)
                    await ctx.guild.unban(member)
                except: pass

    @command(description="Ban one or more people from the server after certain seconds")
    async def timedban(self, ctx, members:Greedy[Member], seconds, *, reason=None):
        if membrs := [m for m in members if m.top_role.position > ctx.author.top_role.position]: return await ctx.send(f"{membrs[0] if len(membrs) == 1 else ' and '.join([', '.join(map(str, membrs[:-1])), str(membrs[-1])])} can't be banned as their top role is higher than yours")
        if not reason: reason = f"Unspecified by {ctx.author}"
        if not tryInt(seconds):
            if not members: return await ctx.send(f"There was a problem. If you pinged one or more members that have the same name as a certain role (most likely a bot), make sure you didn't accidentally ping the role instead of the member")
            return await ctx.send(f"Seconds must be full numbers not \"{seconds}\"")
        if not ctx.author.guild_permissions.ban_members: return await ctx.send("This command requires you have `Ban Members` permission.")
        if not ctx.guild.me.guild_permissions.ban_members: return await ctx.send("This command requires I have `Ban Members` permission.")
        wontBan, toBan = [], []
        for member in members:
            if (member == ctx.guild.me or member == ctx.author) and len(members) == 1: return await ctx.message.add_reaction('🤔')
            if ctx.guild.me.top_role.position < member.top_role.position: wontBan.append(str(member))
            else: toBan.append(member)
        if not toBan and not wontBan: return
        embed = Embed(colour=Colour.orange()).set_author(name=f"Timed ban", icon_url="https://i.imgur.com/7F7Q4x9.png").set_footer(text=f"Reason: {reason}")
        if toBan: embed.description = (embed.description or "") + (f"The members below wll be banned in **{seconds} seconds** from now\n```\n{', '.join(map(str, toBan))}\n```\n" if len(toBan)>1 else f"{toBan[0]} will be banned in **{seconds} seconds**\n\n")
        if wontBan: embed.description = (embed.description or "") + (f"The following members will not be banned because one or more of their top roles are over my top role in the settings role section\n```\n{', '.join(map(str, wontBan))}\n```\n" if len(wontBan)>1 else f"{wontBan[0]} will not be banned because one or more of his/her top roles are over my top role in the settings role section")
        await ctx.send(embed=embed)
        if toBan:
            await asyncio_sleep(int(seconds))
            for member in toBan:
                try: await ctx.guild.ban(member, reason=reason)
                except: pass
    
    @command(description="Kick one or more people from the server after certain seconds")
    async def timedkick(self, ctx, members:Greedy[Member], seconds, *, reason=None):
        if membrs := [m for m in members if m.top_role.position > ctx.author.top_role.position]: return await ctx.send(f"{membrs[0] if len(membrs) == 1 else ' and '.join([', '.join(map(str, membrs[:-1])), str(membrs[-1])])} can't be kicked as their top role is higher than yours")
        if not reason: reason = f"Unspecified by {ctx.author}"
        if not tryInt(seconds):
            if not members: return await ctx.send(f"There was a problem. If you pinged one or more members that have the same name as a certain role (most likely a bot), make sure you didn't accidentally ping the role instead of the member")
            return await ctx.send(f"Seconds must be full numbers not \"{seconds}\"")
        if not ctx.author.guild_permissions.kick_members: return await ctx.send("This command requires you have `kick Members` permission.")
        if not ctx.guild.me.guild_permissions.kick_members: return await ctx.send("This command requires I have `Kick Members` permission.")
        wontKick, toKick = [], []
        for member in members:
            if (member == ctx.guild.me or member == ctx.author) and len(members) == 1: return await ctx.message.add_reaction('🤔')
            if ctx.guild.me.top_role.position < member.top_role.position: wontKick.append(str(member))
            else: toKick.append(member)
        if not toKick and not wontKick: return
        embed = Embed(colour=Colour.orange()).set_author(name=f"Timed kick", icon_url="https://i.imgur.com/7F7Q4x9.png").set_footer(text=f"Reason: {reason}")
        if toKick: embed.description = (embed.description or "") + (f"The members below wll be kicked in **{seconds} seconds** from now\n```\n{', '.join(map(str, toKick))}\n```\n" if len(toKick)>1 else f"{toKick[0]} will be kicked in **{seconds} seconds**\n\n")
        if wontKick: embed.description = (embed.description or"") + (f"The following members will not be kicked because one or more of their top roles are over my top role in the settings role section\n```\n{', '.join(map(str, wontKick))}\n```\n" if len(wontKick)>1 else f"{wontKick[0]} will not be kicked because one or more of his/her top roles are over my top role in the settings role section")
        await ctx.send(embed=embed)
        if toKick:
            await asyncio_sleep(int(seconds))
            for member in toKick:
                try: await ctx.guild.kick(member, reason=reason)
                except: pass
    
    @command(aliases=('masskick',), description="Kick a person. You can kick more than one person by seperating their names/id/pings with a space eg.\n'kick <member1> [member2] [Optional reason]'\n'masskick' command is just an aliase to this.")
    async def kick(self, ctx, members:Greedy[Member], *, reason=None):
        if not reason: reason = f"Unspecified by {ctx.author}"
        if not ctx.author.guild_permissions.kick_members: return await ctx.send("This command requires you have `Kick Members` permission.")
        if not ctx.guild.me.guild_permissions.kick_members: return await ctx.send("This command requires I have `Kick Members` permission.")
        if membrs := [m for m in members if m.top_role.position > ctx.author.top_role.position]: return await ctx.send(f"{membrs[0] if len(membrs) == 1 else ' and '.join([', '.join(map(str, membrs[:-1])), str(membrs[-1])])} can't be kicked as their top role is higher than yours")
        ignored = []
        for member in members:
            if (member == ctx.guild.me or member == ctx.author) and len(members) == 1: return await ctx.message.add_reaction('🤔')
            try: await ctx.guild.kick(member, reason=reason)
            except: ignored.append(member)
        if ignored: return await ctx.send(f"I couldn't kick {ignored[0] if len(ignored) == 1 else ' and '.join([', '.join(map(str, ignored[:-1])), str(ignored[-1])])} as my role is under one or more of theirs")
        await ctx.send(embed=Embed(title=f"<:Mark:663230689860386846> Member(s) successfully kicked", timestamp=datetime.now(), color = Colour.orange())
            .add_field(name="❔ Reason", value=f"```\n{reason}\n```" if not '`' in reason else reason, inline=True))
            # .set_thumbnail(url="https://i.imgur.com/7F7Q4x9.png"))
    
    @command(brief="Mute a person.", description="You can mute more than one person by seperating their names/id/pings with a space eg.\n'mute <member1> [member2] [Optional reason]'")
    async def mute(self, ctx, members:Greedy[Member], *, reason=None):
        if not members: return await ctx.send('No one to mute')
        loading = await ctx.send(loading_msg())
        try:
            if not reason: reason = f"Unspecified by {ctx.author}"
            if not ctx.author.guild_permissions.manage_messages and not ctx.author.id in access_ids: return await ctx.send("This command requires you have `Manage Messages` permission.")
            if membrs := [m for m in members if m.top_role.position > ctx.author.top_role.position and not ctx.author.id in access_ids]: return await ctx.send(f"{membrs[0] if len(membrs) == 1 else ' and '.join([', '.join(map(str, membrs[:-1])), str(membrs[-1])])} can't be muted as their top role is higher than yours")
            if not ctx.guild.me.guild_permissions.mute_members or not ctx.guild.me.guild_permissions.manage_channels or not ctx.guild.me.guild_permissions.manage_roles:
                return await ctx.send("I need '`mute members`', '`manage channels`', and '`manage roles`' permissions to create a 'muted' role and mute it from talking in voice and text channels")
            ignored = []
            for member in members:
                if (member == ctx.guild.me or member == ctx.author) and len(members) == 1: return await ctx.message.add_reaction('🤔')
                try:
                    roles = [x for x in ctx.guild.roles if x.name == "Mute​d" and str(x.color) == '#79828a']
                    if roles:
                        if len(roles) > 1: return await ctx.send(f"There are {len(roles)} 'Mute​d' roles, {len(roles)-1} of them probably not created by me. Please remove one and try again.")
                        role = roles[0]
                    else: role = await ctx.guild.create_role(name="Mute​d", color=colrs[0])
                    if role.position > ctx.guild.me.top_role.position: return await ctx.send(f"The position of my top role should be over {member}'s top role so I can add a muted role to them.")
                    await member.add_roles(role)
                    for channel in member.guild.text_channels:
                        try: await channel.set_permissions(role, send_messages=False, reason=reason)
                        except: pass
                    for channel in ctx.guild.voice_channels:
                        try: await channel.set_permissions(role, speak=False, reason=reason)
                        except: pass
                    if find := mutedDB.find_one({"_id": f"{ctx.guild.id}"}):
                        not f"{member.id}" in find['muted'] and find['muted'].append(f"{member.id}")
                        mutedDB.find_one_and_update({"_id": f"{ctx.guild.id}"}, {'$set': find})
                    else: mutedDB.insert_one({"_id": f"{ctx.guild.id}", "muted": [f"{member.id}"]})
                except Forbidden:
                    print(format_exc())
                    return await ctx.send("Couldn't mute some or all of the mentioned members, check my top role is above all theirs.")
                except Exception:
                    print(format_exc())
                    ignored.append(member)
            if ignored: return await ctx.send(f"I couldn't fully mute {str(ignored[0]) if len(ignored) == 1 else ' and '.join([', '.join(map(str, ignored[:-1])), str(ignored[-1])])} for an unknown reason, they may have left the server or have higher permissions to mine")
            await ctx.send(embed=Embed(title=f"<:Mark:663230689860386846> {str(members[0]) if len(members) == 1 else ' and '.join([', '.join(map(str, members[:-1])), str(members[-1])])} successfully muted", timestamp=datetime.now(), color = Colour.orange())
                .add_field(name="❔ Reason", value=f"```\n{reason}\n```" if not '`' in reason else reason, inline=True))
        except:print(format_exc())
        finally: await loading.delete()
    
    @command(description="Unmute a person. You can unmute more than one person by seperating their names/id/pings with a space eg.\n'unmute <member1> [member2] [Optional reason]'")
    async def unmute(self, ctx, members:Greedy[Member], *, reason=None):
        if not members: return await ctx.send('No one to unmute')
        loading = await ctx.send(loading_msg())
        try:
            if not reason: reason = f"Unspecified by {ctx.author}"
            if not ctx.author.guild_permissions.manage_messages: return await ctx.send("This command requires you have `Manage Messages` permission.")
            if not ctx.guild.me.guild_permissions.mute_members or not ctx.guild.me.guild_permissions.manage_channels or not ctx.guild.me.guild_permissions.manage_roles:
                return await ctx.send("I need '`mute members`', '`manage channels`', and '`manage roles`' permissions")
            ignored = []
            for member in members:
                try:
                    roles = [x for x in ctx.guild.roles if x.name == "Mute​d" and f"{x.color}" == '#79828a']
                    if roles:
                        if len(roles) > 1:
                            mutedDB.find_one_and_delete({"_id": f"{member.id}"})
                            return await ctx.send(f"{member} has {len(roles)} 'Mute​d' roles, {len(roles)-1} of them probably not given by me. Please remove the right one yourself to fully unmute.")
                        if roles[0].position > ctx.guild.me.top_role.position:
                            return await ctx.send(f"The position of my top role should be over {member}'s top role so I can remove the 'muted' role from them.")
                        await member.remove_roles(roles[0])
                    
                    if find := mutedDB.find_one({"_id": f"{ctx.guild.id}"}):
                        if f"{member.id}" in find['muted']: find['muted'].remove(f"{member.id}")
                        if not len(find['muted']): mutedDB.find_one_and_delete({"_id": f"{ctx.guild.id}"})
                        else: mutedDB.find_one_and_update({"_id": f"{ctx.guild.id}"}, {'$set': find})
                except Forbidden:return await ctx.send("Couldn't unmute some or all of the mentioned members, check my top role is above all theirs.")
                except:
                    print(format_exc())
                    ignored.append(member)
            if ignored: return await ctx.send(f"I couldn't fully unmute {str(ignored[0]) if len(ignored) == 1 else ' and '.join([', '.join(map(str, ignored[:-1])), str(ignored[-1])])} for an unknown reason, they may have left the server or have higher permissions to mine")
            await ctx.send(embed=Embed(title=f"<:Mark:663230689860386846> {str(members[0]) if len(members) == 1 else ' and '.join([', '.join(map(str, members[:-1])), str(members[-1])])} successfully unmuted", timestamp=datetime.now(), color = 0x55f297)
                .add_field(name="❔ Reason", value=f"```\n{reason}\n```" if not '`' in reason else reason, inline=True))
        except: print(format_exc())
        finally: await loading.delete()

def setup(bot):
    bot.add_cog(Mod(bot))