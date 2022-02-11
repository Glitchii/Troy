from pymongo import MongoClient
from inspect import currentframe, getframeinfo
from traceback import format_exc
from re import compile as re_compile, sub as re_sub, search as re_search, findall as re_findall
from discord import Embed, Color, Intents
from random import choice as randchoice
from discord.ext.commands import Bot
from json import dumps as json_dumps
from aiohttp import ClientSession
from os import environ as env
from dbl import DBLClient
from threading import Thread
from discord.utils import escape_mentions
from dotenv import load_dotenv
load_dotenv()
tkn, mongoURI, dblTkn = env['token'], env['mongoURI'], env['dblToken']

# Database setup
MongoClient = MongoClient(mongoURI)
botPrefixDB, modLogsDB, botBanDB, customCmdsDB, mutedDB, hangmanDB = (
    MongoClient['db']['prefix'], MongoClient['db']['modLogs'], MongoClient['db']['botBans'],
    MongoClient['db']['customCmds'], MongoClient['db']['muted'], MongoClient['hangman']['leaderboard'])

# User IDs with full access to the bot
access_ids = (642791754160013312, int(env['altID']))

# prefix
prefixes = {pref['_id']: pref['prefix'] for pref in botPrefixDB.find()}

def dbTriggers():
    with MongoClient.db.prefix.watch() as stream:
        for change in stream:
            if change['ns']['coll'] == 'prefix':
                if data := botPrefixDB.find_one(change['documentKey']):
                    if change['documentKey']['_id'] in prefixes:
                        prefixes[data['_id']] = data['prefix']
                    else:
                        prefixes[change['documentKey']['_id']] = data['prefix']
                elif prefixes.get(change['documentKey']['_id']):
                    del prefixes[change['documentKey']['_id']]
# Listen for changes in the prefixes database in a thread and update the prefixes dict accordingly
Thread(target=dbTriggers).start()

intents, guildPrefix = Intents.default(), lambda guildID: (botPrefixDB.find_one({'_id': guildID}) or {}).get('prefix', '...')
intents.members=intents.emojis=intents.messages=intents.guild_reactions=intents.voice_states=intents.presences = True
intents.invites=intents.bans=intents.integrations=intents.webhooks=intents.dm_messages=intents.bans=intents.dm_reactions=intents.dm_reactions=intents.typing=intents.guild_typing=intents.dm_typing = False

get_prefix = lambda bot, msg: prefixes.get(f'{msg.guild.id}', '...') if msg.guild else '...'
bot = Bot(command_prefix=get_prefix, case_insensitive=True, intents = intents)

#       Mute      orange    green     d-orange  d-grey    d-green
colrs = 0x79828a, 0xee9f1b, 0x41ee97, 0xf55711, 0x6e7073, 0x00c198

class ExitRequest(Exception): pass
class Cmds:
    misc = ("gender <name>", "screenshot <person> <message>", "fight <person> <weapon>", "embed <channel> [Json]", "reverse <text/image>", "hack <person>", "eval <code_in_codeblock>", "dice [min/max]", "shorten/unshorten <url>", "translate/tr <lang-abbreviation e.g. en> <text>","detect <hola>", "weather <city>", "timer|reminder <seconds> [Message]", "fancify <text>", "marry <person>", "regional <text>", "color <Hex code>", "joke", "8ball <question>", "funfact", "log [limit]", "ask <Question>", "meme")
    music = ('play <yt url/key-word>', 'pause/resume', 'skip', 'stop', 'playing', 'queue')
    mod = ('ban/massban <person> [person2...] [reason]', 'unban <ID> [ID2...] [reason]','tempban <person> [person2...] <seconds> [reason]', 'timedban <person> [person2...] <seconds> [reason]', 'timedkick <person> [person2...] <seconds> [reason]', 'kick/masskick <person> [person2...] [reason]', 'clear <number> [person]', 'pin <message/image>', 'mute <person> [person2...] [reason]', 'unmute <person> [person2...] [reason]')
    games = ('hangman', 'hangman leaderboard/l','rps <choice eg. rock/r>', '8ball <Question>', 'guess')
    server = ('server info', 'server emotes', 'server members', 'server roles', 'user info [person]', 'user avatar [person]', 'user msgs [person]', 'user perms [person]', 'invite info <server invite url>', 'emoji <:emoji:>', 'emoji info <:emoji:>', 'emoji add <name> <url>', 'emoji del <:emoji:>', 'emoji ren <:emoji:> <new name>', 'emoji copy <emoji name>', 'newmembers [number]')
    info = ('feedback <message/screenshot>', 'help [command name]', 'about', "invite [@bot/bot ID]", "ping")

dblpy = DBLClient(bot, dblTkn, autopost=True)
bot_owner = lambda: bot.get_user(642791754160013312)
tstGuild = lambda guild1 = True: bot.get_guild(int(env['gID']) if guild1 else int(env['gID1']))
loading_msg = lambda customMsg = None, alone = False, emoji = False: ("<a:Preloader:663234181219745813>" if alone else "Loading... <a:Preloader:663234181219745813>" if not customMsg else f"{customMsg} <a:Preloader:663234181219745813>") if not emoji else bot.get_emoji(663234181219745813)

async def aiohttp_request(URL, Type = None, params = None, get = True, data = {}, headers = {}, timeout = None):
    async with ClientSession() as sess:
        if get:
            async with sess.get(URL, params=params) as get:
                if Type is None: return get
                elif Type.lower() == 'read': return await get.read()
                elif Type.lower() == 'json': return await get.json()
                raise ValueError(f"Expected string argument 'read' or 'json', got '{Type}'")
        else:
            async with sess.post(URL, headers=headers, data=json_dumps(data), timeout=timeout) as post:
                if Type is None: return post
                elif Type.lower() == 'read': return await post.read()
                elif Type.lower() == 'json': return await post.json()
                raise ValueError(f"Expected string argument 'read' or 'json', got '{Type}'")

def fson(Dict, formatted=True):
    try: return json_dumps(Dict, indent=4 if formatted else None, ensure_ascii=False)
    except: return Dict

def lineNum(sayText = True):
    line = currentframe().f_back.f_lineno
    return f"line: {line}" if sayText else line

def tryInt(arg):
    try: return int(arg)
    except: return False

def sendingTo(ctx, ID):
    try:
        if not tryInt(ID): return eval(str(ID))
        got, gotServer = bot.get_channel(int(ID)) or bot.get_user(int(ID)), bot.get_guild(int(ID))
        if got: return got
        elif gotServer:
            for chan in gotServer.text_channels:
                if chan.permissions_for(gotServer.me).send_messages: return chan
        return None
    except Exception as exc: print(exc); return None

def send_me():
    return bot.get_channel(663485400870027274) or bot_owner()

def successful(Message, Embeded=True):
    return Embed(description=f"<:Mark:663230689860386846> {Message}", color=colrs[2]) if(Embeded) else (f"<:Mark:663230689860386846> {Message}")

def unsuccessful(Message, Embeded=True):
    return Embed(description=f"❗{Message}", color=Color.red()) if(Embeded) else (f"❗{Message}")

async def get_fun_fact():
    data = await aiohttp_request('https://uselessfacts.jsph.pl/random.json?language=en', 'json')
    return str(data['text']).replace("`","\\`")

def greetings(name=''):
    return str(randchoice((f'Hey there {name}', f'good day {name}', f'hello there {name}', f'hola {name}',
    f"how's it going {name}?", f'sup {name}', f"what's up {name}?", f'how do {name}?',
    f"how goes it {name}?", f"what's crackin' {name}?",
    f"what's poppin' {name}?", f"what's hangin' {name}?", f"what's the dizzle {name}?", f"what's up {name}?", f'bonjour {name}', f'salut {name}'))).capitalize()

def position_number(number):
    return (f'{number}' + ('st' if f'{number}'[-1]=='1' else 'nd' if f'{number}'[-1]=='2' else 'rd' if f'{number}'[-1]=='3' else 'th')) if len(f'{number}')==1 else (f'{number}' + ('st' if f'{number}'[-1]=='1' and f'{number}'[-2:]!='11' else 'nd' if f'{number}'[-1]=='2' and f'{number}'[-2:]!='12' else 'rd' if f'{number}'[-1]=='3' and f'{number}'[-2:]!='13' else 'th'))

def errorMsg(ctx):
    return f"Oops... It looks like I fell into a little error.\nPlease screen shot this error together with the command you said for the error to happen then say `{ctx.prefix}feedback [any message if you want]` and also attach the screenshot. Thanks."

def msg_formated(Text, **kwargs):
    locals().update(kwargs)
    if patt := re_search(r'\{\{.*?\}\}', Text):
        for x in re_compile(r'\{\{.*?\}\}').finditer(Text):
            Text2 = re_sub(r"\{\{|\}\}", "", x.group()).strip()
            try: Text = Text.replace(patt.group(), str(eval(Text2)))
            except:
                exec(Text2)
                Text = Text.replace(patt.group(), "")
    return Text

#  --- Custom CMDs ---
def custom_cmd_format(ctx, text):
    reg = (
        (r'\{ *server\.id *\}', ctx.guild.id),
        (r'\{ *server\.member[_-]?count *\}', len(ctx.guild.members)),
        (r'\{ *server\.(members|users)? *\}', escape_mentions(", ".join(x.display_name for x in ctx.guild.members))),
        (r'\{ *server\.owner *\}', ctx.guild.owner),
        (r'\{ *server\.owner\.name *\}', ctx.guild.owner.name),
        (r'\{ *server\.owner\.mention *\}', ctx.guild.owner.mention),
        (r'\{ *server\.owner\.id *\}', ctx.guild.owner.id),
        (r'\{ *server\.owner\.(nick(name)?|display[_-]name) *\}', escape_mentions(ctx.guild.owner.display_name)),
        (r'\{ *server\.owner\.(avatar|avatar[_-]url) *\}', ctx.guild.owner.avatar_url),
        (r'\{ *server\.(icon|icon[_-]url) *\}', ctx.guild.icon_url),
        (r'\{ *server(\.name)? *\}', ctx.guild.name),
        (r'\{ *server\.region *\}', ctx.guild.region),
        (r'\{ *(member|user)\.name *\}', ctx.author.name),
        (r'\{ *(member|user)\.mention *\}', ctx.author.mention),
        (r'\{ *(member|user)\.id *\}', ctx.author.id),
        (r'\{ *(member|user)\.((nick|display)([_-]?name)?) *\}', escape_mentions(ctx.author.display_name)),
        (r'\{ *(member|user)\.avatar([_-]?url)? *\}', ctx.author.avatar_url),
        (r'\{ *(member|user) *\}', ctx.author),
        (r'\{ *channel(\.name)? *\}', ctx.channel.name),
        (r'\{ *channel\.id *\}', ctx.channel.id),
        (r'\{ *channel\.mention *\}', ctx.channel.mention)
    )
    for tupl in reg:
        text = re_sub(tupl[0], f'{tupl[1]}', text)
    return text


custom_cmd_formatters = (
    "{server}", "{server.name}", "{server.id}", "{server.owner}",
    "{server.owner}", "{server.owner.id}", "{server.owner.nick}", "{server.owner.mention}", "{server.owner.avatar_url}",
    "{server.members}", "{server.member_count}", "{server.icon}",
    "{user}", "{user.name}", "{user.mention}", "{user.id}", "{user.nick}", "{user.avatar_url}",
    "{channel}", "{channel.name}", "{channel.mention}", "{channel.id}",
)
spaces, rows = len(max(custom_cmd_formatters, key=lambda x: len(x))) + 1, ''
for value in custom_cmd_formatters:
    rows+=f'{value.ljust(spaces)}'
custom_cmd_formatters = rows

join_leave_formatters = (
    "{server}", "{server.name}", "{server.id}", "{server.owner}",
    "{server.owner}", "{server.owner.id}", "{server.owner.nick}", "{server.owner.mention}", "{server.owner.avatar_url}",
    "{server.members}", "{server.member_count}", "{server.icon}",
    "{user}", "{user.name}", "{user.mention}", "{user.id}", "{user.nick}", "{user.avatar_url}",
)
spaces, rows = len(max(join_leave_formatters, key=lambda x: len(x))) + 1, ''
for value in join_leave_formatters:
    rows+=f'{value.ljust(spaces)}'
join_leave_formatters = rows

def svCmds(ID, returnCmds=False):
    svCmds, svFind = 0, customCmdsDB.find_one({f'{ID}': {'$exists': True}}, {'_id': False, 'guildName': False})
    if svFind:
        for x in svFind.values(): svCmds = len(tuple(x.keys())) if not returnCmds else tuple(x.keys())
    return () if not svFind and returnCmds else svCmds

custom_cmd_helper = lambda ctx: (Embed(color=colrs[1], title="<:Command:691849893274452010> Custom Commands", description=f"This server has {'no'if(svCmds(ctx.guild.id)==0)else(svCmds(ctx.guild.id))} custom {'command'if(svCmds(ctx.guild.id)==1)else('commands')}. You can add, edit, or delete a custom command by using the following commands.\n\n> {ctx.prefix}cmd add <command name> <response>\n> {ctx.prefix}cmd del <command name>\n> {ctx.prefix}cmd edit <command name> <new response>\n\nCustom commands only work in the server they're created in. You can use the formatters below in command responses and they'll be replaced with the appropriate text i.e. {{server.name}} will be replaced with the server name ({ctx.guild.name}) when command is called.```c\n{custom_cmd_formatters}\n```\n`{{user.nick}}` changes to the person's nickname, but changes to the name instead if no nickname. If you want bot to display an image too, upload it together with the 'cmd add' or 'cmd edit' command. And if you want random responses, put all your responses inside opening and closing brackets seperated by a comma, example:\n`[ Hello {{user.nick}}, What's up {{user.nick}}?, Yo {{user.nick}} ]`").set_footer(text=f"Want a certain option added? Send me feedback {ctx.prefix}feedback <message>"))
#  --- Custom CMDs ---

def opts(text, dictionary = {}):
    try:
        for lst in re_findall(r'-\w+ +(?!\\)".+(?!\\)"?(?=-\w+ +)|-\w+ +(?!\\)".+(?!\\)"|-\w+ +\S+?(?=-\w+ +)|-\w+ +\S+', text):
            splitted = re_sub(r'((?<=^-\w)\w*) ', '\\1<>split<>', lst).split('<>split<>')
            key, value = splitted[0][1:], re_sub(r'^"(.+)"$', '\\1', splitted[1].strip())
            dictionary[key], text = value, re_sub(fr" ?--?{key} ?|{value}", '', text, 2)
    except: print(format_exc())
    dictionary['text'] = text
    return dictionary