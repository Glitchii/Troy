from traceback import format_exc
from discord import Embed, File
from datetime import datetime
from re import sub as re_sub
from random import choice as randchoice
from io import BytesIO as IoBytesIO
from discord.ext import commands
from discord.utils import escape_mentions
from imports import modLogsDB, lineNum, aiohttp_request, loading_msg, dblpy, mutedDB, colrs

def joinLeaveFormat(member, text):
    reg = (
        (r'\{\s*server\.id\s*\}', member.guild.id),
        (r'\{\s*server\.member[_-]?count\s*\}', len(member.guild.members)),
        (r'\{\s*server\.(members|users)?\s*\}', escape_mentions(", ".join(x.display_name for x in member.guild.members))),
        (r'\{\s*server\.owner\s*\}', member.guild.owner),
        (r'\{\s*server\.owner\.name\s*\}', member.guild.owner.name),
        (r'\{\s*server\.owner\.mention\s*\}', member.guild.owner.mention),
        (r'\{\s*server\.owner\.id\s*\}', member.guild.owner.id),
        (r'\{\s*server\.owner\.(nick(name)?|display[_-]name)\s*\}', escape_mentions(member.guild.owner.display_name)),
        (r'\{\s*server\.owner\.(avatar|avatar[_-]url)\s*\}', member.guild.owner.avatar_url),
        (r'\{\s*server\.(icon|icon[_-]url)\s*\}', member.guild.icon_url),
        (r'\{\s*server(\.name)?\s*\}', member.guild.name),
        (r'\{\s*server\.region\s*\}', member.guild.region),
        (r'\{\s*(member|user)\.name\s*\}', member.name),
        (r'\{\s*(member|user)\.mention\s*\}', member.mention),
        (r'\{\s*(member|user)\.id\s*\}', member.id),
        (r'\{\s*(member|user)\.((nick|display)([_-]?name)?)\s*\}', escape_mentions(member.display_name)),
        (r'\{\s*(member|user)\.avatar([_-]?url)?\s*\}', member.avatar_url),
        (r'\{\s*(member|user)\s*\}', member)
    )
    for tupl in reg:
        text = re_sub(tupl[0], f'{tupl[1]}', text)
    return text

class Modlogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Module: Modlogs loaded")
    
    @commands.Cog.listener()
    async def on_message_delete(self, msg):
        try:
            if not msg.author.bot and (mdFind := modLogsDB.find_one({f"{msg.guild.id}.editDelete":{'$exists': True}}, {'_id': False})):
                await msg.guild.get_channel(mdFind[str(msg.guild.id)]["editDelete"]["ID"]).send(embed = Embed(title='Message Delete', description=None, colour=0xf09516, timestamp=datetime.utcnow())
                    .add_field(name="<:User:663295066223411200> Author:", value=f'{msg.author.mention} \n*ID: {msg.author.id}*',inline=True)
                    .add_field(name="<:Hash:663295056060481556> Channel:", value=f'{msg.channel.mention} \n*ID: {msg.channel.id}*', inline=True)
                    .add_field(name='<:ID:663403744314261504> Message ID:', value=msg.id, inline=True)
                    .add_field(name='\\📅 Sent on:', value=msg.created_at.strftime('%d/%m/%Y %H:%M'), inline=True)
                    .add_field(name='\\📅 Deleted on:', value=datetime.utcnow().strftime('%d/%m/%Y %H:%M'), inline=True)
                    .add_field(name='Attachment:', value=f"[File URL]({msg.attachments[0].url})" if msg.attachments else None, inline=True)
                    .add_field(name="<:Message:663295062385360906> Message:", value=msg.content, inline=len(msg.content)<20)
                    .set_thumbnail(url=msg.author.avatar_url))
        except: print(format_exc())
    
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        try:
            if not after.author.system and not after.author.bot and (mdFind := modLogsDB.find_one({f"{before.guild.id}.editDelete":{'$exists': True}}, {'_id': False})):
                await before.guild.get_channel(mdFind[str(before.guild.id)]["editDelete"]["ID"]).send(embed=Embed(title='Message Edit', colour=0x9bc155, timestamp=datetime.utcnow())
                    .add_field(name="<:User:663295066223411200> Author:", value=before.author.mention, inline=True)
                    .add_field(name="<:ID:663403744314261504> Author ID:", value=before.author.id, inline=True)
                    .add_field(name="<:Hash:663295056060481556> Channel:", value=before.channel.mention, inline=True)
                    .add_field(name='<:Edit:663298459419541522> Edited at:', value=datetime.utcnow().strftime('%d/%m/%Y %H:%M'), inline=True)
                    .add_field(name='<:ID:663403744314261504> Message ID:', value=before.id, inline=True)
                    .add_field(name='<:link:663295066357497857> Message link:', value=f'[Click to jump to message]({before.jump_url})', inline=True)
                    .add_field(name='\\📅 Created at:', value=before.created_at.strftime('%d/%m/%Y %H:%M'), inline=True)
                    .add_field(name='Attachment:', value=f"[File URL]({before.attachments[0].url})" if before.attachments else None, inline=True)
                    .add_field(name="<:Left:663400555493851182> Before:", value=before.content, inline=len(before.content)<20)
                    .add_field(name='<:Right:663400557154795528> After:', value=after.content, inline=len(after.content)<20)
                    .set_thumbnail(url=before.author.avatar_url))
        except: print(format_exc())

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if (find := mutedDB.find_one({"_id": f"{member.guild.id}"})) and f"{member.id}" in find['muted']:
            try:
                if roles := [x for x in member.guild.roles if x.name == "Mute​d" and str(x.color) == '#79828a'] or [await member.guild.create_role(name="Mute​d", color=colrs[0])]:
                    for role in roles:
                        await member.add_roles(role)
                        for channel in member.guild.text_channels:
                            try: await channel.set_permissions(role, send_messages=False, reason="Muted member rejoined")
                            except: pass
                        for channel in member.guild.voice_channels:
                            try: await channel.set_permissions(role, speak=False, reason="Muted member rejoined")
                            except: pass
            except: print(format_exc())
            
        if (mdFind := modLogsDB.find_one({f"{member.guild.id}.joinMessage":{'$exists': True}}, {'_id': False})) and not member.bot:
            if mdFind[f'{member.guild.id}']["joinMessage"].get('channel'):
                try:
                    if mdFind[f'{member.guild.id}']["joinMessage"]['channel'].get("message"):
                        if mdFind[f'{member.guild.id}']["joinMessage"]["channel"]["message"].get('attachment'):
                            link = mdFind[f'{member.guild.id}']["joinMessage"]["channel"]["message"]['attachment']
                            attachment = File(IoBytesIO(await aiohttp_request(link, 'read')), filename=f"attachment.{link.split('/')[-1].split('.')[1]}")
                        else: attachment = None
                        await member.guild.get_channel(mdFind[f'{member.guild.id}']["joinMessage"]["channel"]["ID"]).send(joinLeaveFormat(member, mdFind[f'{member.guild.id}']["joinMessage"]["channel"]["message"]["text"]), file=attachment)
                    else:
                        if not member.bot:
                            loading = await (chan := member.guild.get_channel(mdFind[f'{member.guild.id}']["joinMessage"]["channel"]["ID"])).send(loading_msg())
                            embed = (Embed(colour=0x49a56f, timestamp=datetime.utcnow(), title=randchoice((
                                    f"<:Right:663400557154795528> Hey welcome to the server {member}", f"<:Right:663400557154795528> Welcome {member}, remember leaving isn't an option",
                                    f'<:Right:663400557154795528> Welcome aboard {member}', f"<:Right:663400557154795528> Everyone! We got a new member, {member}",
                                    f"<:Right:663400557154795528> Everyone, I introduce you {member}", f'<:Right:663400557154795528> {member.name} just joined, let the party begin',
                                    f"<:Right:663400557154795528> {member.name} we've been waiting for you", f"Look... It's {member.name}!")))
                                .add_field(name="<:User:663295066223411200> Member:", value=member, inline=True)
                                .add_field(name="<:ID:663403744314261504> Member ID:", value=member.id, inline=True)
                                .add_field(name="🤖 Bot Account", value=member.bot, inline=True)
                                .set_thumbnail(url=member.avatar_url)
                                .add_field(name="Member count:", value=len(member.guild.members), inline=True))
                            await chan.send(embed=embed)
                            await loading.delete()
                        else:
                            embed=(Embed(colour=0x4f597d, timestamp=datetime.utcnow(), title=randchoice([
                                f'<:Right:663400557154795528> Looks like we got a new bot in the server.','<:Right:663400557154795528> A new bot just joined']))
                                .set_thumbnail(url=member.avatar_url)
                                .add_field(name="🤖 Bot name:", value=member, inline=True)
                                .add_field(name="<:ID:663403744314261504> Bot ID:", value=member.id, inline=True)
                                .set_footer(text=f"Find out more with 'user info' command"))
                            try:
                                botInfo = await dblpy.http.get_bot_info(member.id)
                                if botInfo.get('prefix'): embed.add_field(name="Prefix:", value=botInfo['prefix'], inline=True)
                                if botInfo.get('lib'): embed.add_field(name="Library:", value='Unknown' if botInfo['lib'].lower() == 'other' else botInfo['lib'], inline=True)
                                if botInfo.get("owners"):
                                    if len(botInfo['owners']) > 1:
                                        try: embed.add_field(name="Developers:", value = ", ".join(str(self.bot.get_user(int(ID))) for ID in botInfo['owners']), inline=True)
                                        except: embed.add_field(name="Developer IDs:", value = ", ".join(map(str, botInfo['owners'])), inline=True); print(format_exc())
                                    else: 
                                        try: embed.add_field(name="Developer:", value = ", ".join(str(self.bot.get_user(int(ID))) for ID in botInfo['owners']), inline=True)
                                        except: embed.add_field(name="Developer's ID:", value = ", ".join(map(str, botInfo['owners'])), inline=True)
                                if botInfo.get("server_count"): embed.add_field(name = "Bot is in:", value=f"{botInfo['server_count']} servers", inline=True)
                                if botInfo.get("shortdesc"): embed.add_field(name = "Short description", value=botInfo['shortdesc'], inline=True)
                            except: pass
                            await member.guild.get_channel(mdFind[f'{member.guild.id}']["joinMessage"]["channel"]["ID"]).send(embed=embed)
                except: print(format_exc())
            if mdFind[f'{member.guild.id}']["joinMessage"].get("user"):
                try:
                    if 'message' in mdFind[f'{member.guild.id}']["joinMessage"]["user"].keys():
                        message = mdFind[f'{member.guild.id}']["joinMessage"]["user"].get('message', {})
                        if message.get('attachment'): link, attachment = message['attachment'], File(IoBytesIO(await aiohttp_request(link, 'read')), filename=f"attachment.{link.split('/')[-1].split('.')[1]}")
                        else: attachment = None
                        await member.send(joinLeaveFormat(member, message.get('text', f"Hey, welcome to {member.guild.name} {member.name}")), file=attachment)
                    if mdFind[f'{member.guild.id}']["joinMessage"]["user"].get("roles"):
                        try: [await member.add_roles(iD) for iD in [member.guild.get_role(role) for role in mdFind[f'{member.guild.id}']["joinMessage"]["user"]["roles"]]]
                        except: print(f"Failed to give roles on join:\n{format_exc()}\n- {lineNum()}")
                except: print(format_exc())
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        try:
            if not member.bot and (mdFind := modLogsDB.find_one({f"{member.guild.id}.leaveMessage":{'$exists': True}}, {'_id': False})):
                if mdFind[f'{member.guild.id}']["leaveMessage"]["channel"].get("message"):
                    if mdFind[f'{member.guild.id}']["leaveMessage"]["channel"]["message"].get('attachment'):
                        link = mdFind[f'{member.guild.id}']["leaveMessage"]["channel"]["message"]['attachment']
                        attachment = File(IoBytesIO(await aiohttp_request(link, 'read')), filename=f"attachment.{link.split('/')[-1].split('.')[1]}")
                    else: attachment = None
                    await member.guild.get_channel(mdFind[f'{member.guild.id}']["leaveMessage"]["channel"]["ID"]).send(joinLeaveFormat(member, mdFind[f'{member.guild.id}']["leaveMessage"]["channel"]["message"]["text"]), file=attachment)
                else:
                    await member.guild.get_channel(mdFind[f'{member.guild.id}']["leaveMessage"]["channel"]["ID"]).send(embed=(Embed(colour=0x8b6660, timestamp=datetime.utcnow(), title=f'<:Left:663400555493851182> {member.name} just left us \\😔')
                        .add_field(name="<:User:663295066223411200> Member:", value=member, inline=True)
                        .add_field(name="<:ID:663403744314261504> Member ID:", value=member.id, inline=True)
                        .add_field(name="Member since", value=member.joined_at.strftime("%B %d, %Y"), inline=True)
                        .add_field(name="Nickname", value=member.nick, inline=True)
                        .add_field(name="Member count:", value=len(member.guild.members), inline=True)
                        .add_field(name="Top Role", value=member.top_role.name if(not member.top_role.is_default()) else None, inline=True)
                        .set_thumbnail(url=member.avatar_url)))
        except AttributeError: pass
        except: print(format_exc())

def setup(bot):
    bot.add_cog(Modlogs(bot))