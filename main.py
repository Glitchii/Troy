#!/usr/bin/python3
from traceback import format_exc
from datetime import datetime
from io import StringIO as IoStringIO, BytesIO as IoBytesIO
from re import match as re_match, sub as re_sub, search as re_search, findall as re_findall, compile as re_compile
from random import choice as randchoice
from asyncio import TimeoutError as AsyncioTimeoutError
# from difflib import get_close_matches

from discord import Activity, ActivityType, Embed, File, Forbidden, Status
from discord.errors import HTTPException
from discord.ext.commands.errors import NoPrivateMessage, BadArgument, MissingRequiredArgument
from discord.ext.commands import CommandError, CommandNotFound, BotMissingPermissions, MissingPermissions, DisabledCommand
from discord.utils import get, escape_mentions

from imports import (
    custom_cmd_helper, fson, svCmds, bot, botPrefixDB, colrs,
    Cmds, access_ids, tkn, send_me, get_fun_fact, lineNum,
    guildPrefix, loading_msg, greetings, tryInt, customCmdsDB, paginate,
    custom_cmd_format, modLogsDB, aiohttp_request, join_leave_formatters,
    successful, ExitRequest
)

bot.remove_command('help')
bot_ping = None
extentions = "cogs.misc", "cogs.games", "cogs.mod", "cogs.server", "cogs.modlogs", "cogs.music"


@bot.event
async def on_ready():
    global bot_ping
    bot_ping = re_compile(fr"^<@!?{bot.user.id}>$")
    print(f"{bot.user} online.")
    await bot.change_presence(activity=Activity(type=ActivityType.watching, name=f"pings for prefix"), status=Status.idle)


async def custom_cmd_output(msg, prefix, guildFinder):
    try:
        for cmd in guildFinder.keys():
            if msg.content.lower() == prefix + cmd:
                if guildFinder[cmd].get('attachment'):
                    loading, link = await msg.channel.send(loading_msg()), guildFinder[cmd]['attachment']
                    response = guildFinder[cmd]['response']
                    await msg.channel.send(custom_cmd_format(msg, randchoice(response) if type(response) == list else response),
                        file=File(IoBytesIO(await aiohttp_request(str(link), 'read')), filename=f"Image.{link.split('/')[-1].split('.')[1]}"))
                else:
                    response = guildFinder[cmd]['response']
                    await msg.channel.send(custom_cmd_format(msg, randchoice(response) if type(response) == list else response))
    except: print(format_exc())
    finally:
        try: await loading.delete()
        except: pass


@bot.listen()
async def on_message(msg):
    try:
        if msg.guild and not msg.author.bot:
            if bot_ping.match(msg.content):
                try:
                    async with msg.channel.typing():
                        if not botPrefixDB.find_one({'_id': f'{msg.guild.id}'}):
                            return await msg.channel.send(embed=Embed(title=f"{greetings(msg.author.display_name)}.", color=colrs[4], description=f"\nCustom prefix: _Not set_ │ Default prefix is ...\nTo set a custom prefix for this server, go to my settings in help menu.").add_field(name="Also here's a fun fact for you:", value=await get_fun_fact()).set_footer(text=f"You can get more of these facts by saying {guildPrefix(msg.guild.id)}funfact"))
                        elif botPrefixDB.find_one({'_id': f'{msg.guild.id}'}):
                            pref = botPrefixDB.find_one({'_id': f'{msg.guild.id}'})
                            return await msg.channel.send(embed=Embed(title=f"{greetings(msg.author.display_name.capitalize())}", color=colrs[4], description=f"\nMy prefix in this server is {pref['prefix']}\nDefault prefix is ... │ The default prefix won't work in this server.").add_field(name="Also here's a fun fact for you:", value=await get_fun_fact()).set_footer(text=f"You can get more of these facts by saying {pref['prefix']}funfact"))
                except Forbidden:
                    if not msg.guild.me.guild_permissions.embed_links:
                        await msg.channel.send(f"```\nMy default prefix is ...\nNote: For me to function better, atleast allow me permissions to embed links.\n```")
                    else:
                        await msg.channel.send(f"```\nThere was an error. My default prefixs is ...\n```")
            else:
                prefics = bot.command_prefix(bot, msg)
                if msg.content.startswith(prefics):
                    guild = customCmdsDB.find_one({f'{msg.guild.id}': {'$exists': True}}, {'_id': False})
                    if guild:
                        await custom_cmd_output(msg, prefics, guild[f'{msg.guild.id}'])
    except AttributeError:
        pass
    except:
        print(format_exc())
    # finally:
    #     await bot.process_commands(msg)


@bot.listen()
async def on_command_error(ctx, error):
    # pylint: disable=unused-variable
    if hasattr(ctx.command, 'on_error'):
        return
    error = getattr(error, 'original', error)

    class EmbedError(CommandError):
        pass

    if isinstance(error, CommandNotFound):
        # if ctx.invoked_with not in svCmds(ctx.guild.id, True):
        #     cmds = set()
        #     for x in bot.commands:
        #         if x.enabled and not x.hidden:
        #             cmds.add(x.qualified_name)
        #             try:
        #                 for y in x.walk_commands(): cmds.add(str(y))
        #             except: pass
        #     if svCmds(ctx.guild.id): cmds.update(svCmds(ctx.guild.id, True))

        #     from difflib import get_close_matches
        #     matches = get_close_matches(ctx.invoked_with, cmds)
        #     if matches: await ctx.send(f'A command named "{ctx.invoked_with}" wasn\'t found, but the ' + ('command \'' if len(matches) == 1 else 'commands \'') + (f'{matches[0]}\' looks a little similar.' if len(matches) == 1 else  "' and '".join(["', '".join(matches[:-1]), matches[-1]]) + f'\' look a little similar.'))
        return
    elif isinstance(error, (MissingRequiredArgument,)):
        missing, params = re_sub(' is a re.+', '', error.args[0]), {x: ctx.command.params[x] for x in ctx.command.params if x not in ('ctx', 'self')}
        var = f"{ctx.prefix}{ctx.command} {' '.join(f'<{p}>' if not re_search(' *= *None', str(params[p])) else f'[{p}]' for p in params.keys())}"
        return await ctx.send(f"A required parameter '{missing.replace('_', ' ')}' is missing\n```\n{var}\n{' '*var.rfind(missing)}{re_sub('..?', '﹋', missing)}\n```")
    elif isinstance(error, (BadArgument,)):
        return await ctx.send(f"Error: {error.args[0]}")
    elif isinstance(error, EmbedError):
        return await ctx.channel.send("Error: This command requires the `Embed Links` permission to execute")
    elif isinstance(error, BotMissingPermissions):
        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_perms]
        fmt = f'{"**, **".join(missing[:-1])}, and {missing[-1]}' if len(missing) > 2 else ' and '.join(missing)
        return await ctx.send(f'I need the `{fmt}` permission(s) to run this command.')
    elif isinstance(error, DisabledCommand):
        return await ctx.send('This command has been disabled.')
    elif isinstance(error, MissingPermissions):
        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_perms]
        fmt = f'{"**, **".join(missing[:-1])}, and {missing[-1]}' if len(missing) > 2 else ' and '.join(missing)
        return await ctx.send(f'I need the `{fmt}` permission(s) to run this command.')
    elif isinstance(error, NoPrivateMessage):
        return await ctx.author.send('This command cannot be used in direct messages.')


@bot.event
async def on_guild_join(guild):
    await send_me().send(embed=Embed(color=colrs[2], title=f"<:Right:663400557154795528> Troy joined '{guild}'", timestamp=datetime.utcnow()).add_field(name="<:ID:663403744314261504> Guild ID", value=guild.id, inline=True).add_field(name="<:Mod_admin:663199332299964458> Owner", value=guild.owner, inline=True).add_field(name="<:IDcard:663295056911925281> Owner ID", value=guild.owner.id, inline=True).add_field(name="<:Users:663295067280244776> Members", value=f"{guild.member_count} | Humans: {sum(not x.bot for x in guild.members)}, Bots: {sum(x.bot for x in guild.members)}", inline=True).set_thumbnail(url=guild.icon_url))


@bot.event
async def on_guild_remove(guild):
    try:
        for database in (botPrefixDB, customCmdsDB, modLogsDB):
            database.find_one_and_delete({str(guild.id): {'$exists': True}})
    except:
        print(f"Error deleting guild prefix from Database in the guild: {guild}\nGuild id: {guild.id}\nError: \n```py\n{format_exc()}\n```")
    await send_me().send(embed=Embed(color=colrs[3], title=f"<:Left:663400555493851182> Troy removed from '{guild}'", timestamp=datetime.utcnow()).add_field(name="<:ID:663403744314261504> Guild ID", value=guild.id, inline=True).add_field(name="<:Mod_admin:663199332299964458> Owner", value=guild.owner, inline=True).add_field(name="<:IDcard:663295056911925281> Owner ID", value=guild.owner.id, inline=True).add_field(name="<:Users:663295067280244776> Members", value=f"{guild.member_count} | Humans: {sum(not x.bot for x in guild.members)}, Bots: {sum(x.bot for x in guild.members)}", inline=True).set_thumbnail(url=guild.icon_url))


@bot.command(aliases=('reload',))
async def restart(ctx):
    if ctx.author.id in access_ids:
        for extension in extentions:
            bot.reload_extension(extension)
        await ctx.channel.send("Commands have been reloaded.")


@bot.command(aliases=('safe?',))
async def safe(ctx):
    if bot.voice_clients:
        return await ctx.send(f"""Not safe to restart... Bot is in some voice channels:\n```json\n{fson([{
            f'{x.guild.name} ({x.guild.id})': {
                "Channel": f'{x.channel.name} ({x.channel.id})',
                "Playing": x.is_playing() and 'Yes' or 'No'
            }} for x in bot.voice_clients][0])}\n```""")
    await ctx.message.add_reaction(bot.get_emoji(663230689860386846))


@bot.command(aliases=('shutdown',))
async def logout(ctx):
    if ctx.author.id in access_ids:
        await ctx.send('Shutting down..')
        await bot.close()
        exit()


emojis = "0⃣", "1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣"
@bot.command(aliases=('help',), brief="See the help menu", description="Or get help with a certain command.")
async def h(ctx, *, command_name=None):
    if not command_name:
        if not ctx.guild:
            return await ctx.author.send(f"Hi, here's my help menu https://troybot.xyz/commands/")
        elif ctx.guild.me.guild_permissions.add_reactions and ctx.guild.me.guild_permissions.external_emojis and ctx.guild.me.guild_permissions.embed_links:
            try:
                server_emoji_full, server_emoji = '<:Server:663296208537911347>', bot.get_emoji(663296208537911347)
                main_emojis = (663181316921098271, 663199332299964458, 663200014704574486, 663163816477196358, 663203080443134011, 691849893274452010, 700368409174474774, 663201785237995520)
                music_emojis, mod_emojis, games_emoji, tools_emoji, back_emoji, custom_cmd_emoji, info_emoji, cross_emoji, fun_emoji = tuple(bot.get_emoji(id=id) for id in main_emojis) + ('🔆',)
                emojiIDs, to_react_with_main = main_emojis + (server_emoji.id,), (music_emojis, mod_emojis, games_emoji, fun_emoji, server_emoji, tools_emoji, custom_cmd_emoji, info_emoji, cross_emoji)
                func_embed = Embed(title=f"🔆 Fun commands │ Prefix: {ctx.prefix}", color=colrs[1]).set_footer(text=f"For help with a certain command say '{ctx.prefix}help <command name>'").add_field(name="Everything in square brackets '[]' is optional", value='\n'.join(ctx.prefix + x for x in Cmds.misc), inline=True).set_thumbnail(url="https://i.imgur.com/MjqPDrX.png")
                info_embed = Embed(title=f"<:info:700368409174474774> Informations commands │ Prefix: {ctx.prefix}", colour=colrs[1]).set_footer(text=f"For help with a certain command say '{ctx.prefix}help <command name>'").add_field(name="Everything in square brackets '[]' is optional", value='\n'.join(ctx.prefix + x for x in Cmds.info), inline=True).set_thumbnail(url=info_emoji.url)
                music_embed = Embed(title=f"<:Music:663181316921098271> Music commands │ Prefix: {ctx.prefix}", colour=colrs[1]).set_footer(text=f"For help with a certain command say '{ctx.prefix}help <command name>'").add_field(name="Everything in square brackets '[]' is optional", value='\n'.join(ctx.prefix + x for x in Cmds.music), inline=True).set_thumbnail(url=music_emojis.url)
                mod_embed = Embed(title=f"<:Mod_admin:663199332299964458> Admin/Mod commands │ Prefix: {ctx.prefix}", colour=colrs[1]).set_footer(text=f"For help with a certain command say '{ctx.prefix}help <command name>'").add_field(name="Everything in square brackets '[]' is optional", value='\n'.join(ctx.prefix + x for x in Cmds.mod), inline=True).set_thumbnail(url=mod_emojis.url)
                server_embed = Embed(title=f"{server_emoji_full} Server commands │ Prefix: {ctx.prefix}", colour=colrs[1]).set_footer(text=f"For help with a certain command say '{ctx.prefix}help <command name>'").add_field(name="Everything in square brackets '[]' is optional", value='\n'.join(ctx.prefix + x for x in Cmds.server), inline=True).set_thumbnail(url=server_emoji.url)
                games_embed = Embed(title=f"<:gameController:663200014704574486> Games │ Prefix: {ctx.prefix}", colour=colrs[1]).set_footer(text=f"For help with a certain command say '{ctx.prefix}help <command name>'").add_field(name="Everything in square brackets '[]' is optional", value='\n'.join(ctx.prefix + x for x in Cmds.games), inline=True).set_thumbnail(url=games_emoji.url)
                if svCmds(ctx.guild.id) == 0:
                    custom_cmd_embed = Embed(color=colrs[1], description=f"This server has no custom commands, so nothing to show here.\nTo see how you can add a custom command, type `{ctx.prefix}cmd`.").set_thumbnail(url=custom_cmd_emoji.url).set_footer(text=f"Custom commands will be shown here when added.")
                else:
                    custom_cmd_embed = Embed(color=colrs[1], title=f"<:Command:691849893274452010> Custom commands │ Prefix: {ctx.prefix}").add_field(name=f"This server has {svCmds(ctx.guild.id)} custom {'commands'if(svCmds(ctx.guild.id)>1)else 'command'}.", value='\n'.join(ctx.prefix + cmd for cmd in svCmds(ctx.guild.id, True))).set_thumbnail(url=custom_cmd_emoji.url).set_footer(text=f"For more information, please say {ctx.prefix}cmd")

                main_embed = Embed(colour=colrs[1], description="<:Troy_T:663195739861811210> <:Troy_R:663195741300326411> <:Troy_O:663195738809040928> <:Troy_Y:663195740822044753>\n\n").add_field(name="\n<:Music:663181316921098271> Music", value=f"{len(Cmds.music)} Music commands", inline=True).add_field(name=f"{server_emoji_full} Server", value=f"{len(Cmds.server)} Server commands", inline=True).add_field(name="<:Mod:663199332299964458> Moderation", value=f"{len(Cmds.mod)} Mod commands", inline=True).add_field(name="<:Tools:663163816477196358> Settings", value=f"5 Settings commands", inline=True).add_field(name="<:Command:691849893274452010> Custom cmds", value="1 custom command" if svCmds(ctx.guild.id) == 1 else f"{svCmds(ctx.guild.id)} custom commands", inline=True).add_field(name="<:gameController:663200014704574486> Games", value=f"{len(Cmds.games)-1} Games", inline=True).add_field(name="🔆 Fun", value=f"{len(Cmds.misc)} Fun commands", inline=True).add_field(name="<:info:700368409174474774> Information", value=f"{len(Cmds.info)} Info commands", inline=True).add_field(name="­", value=f"­", inline=True).add_field(name=randchoice((f"You can also check https://troybot.xyz/commands/{ctx.guild.id}", "You get more control from the website, https://troybot.xyz/", f"`For info about a command, say '{ctx.prefix}help <command>'`", f"`For feedback, please use the feadback command.`")), value=f"```\nClick any emoji below to control the menu.\n```", inline=False).set_thumbnail(url=bot.user.avatar_url).set_footer(text=f"Emojis will only respond to the person that requested the help menu")
                send = await ctx.send(embed=main_embed)

                async def try_edit(toEdit=send, embed=main_embed, required=False, theEnd=False):
                    if theEnd and embed == main_embed:
                        try:
                            last_embed = main_embed.to_dict()
                            del last_embed['footer']
                            last_embed['fields'][9] = {'name': randchoice(("You get more control from the website, https://troybot.xyz/", f"`For info about a command, say '{ctx.prefix}help <command>'`", f"`For feedback, please use the feadback command.`")), 'value': f'```\nSession ended, please say "{ctx.prefix}{ctx.invoked_with}" again.\n```', 'inline': True}
                            last_embed = Embed.from_dict(last_embed)
                        except:
                            print(format_exc())
                    else:
                        last_embed = main_embed
                    try:
                        await toEdit.edit(embed=last_embed)
                    except:
                        if required:
                            raise Exception(format_exc())

                async def end_help(clear_required=True, send_msg=False, send_embed=False, delete_after=None):
                    try:
                        if send_msg or send_embed:
                            if delete_after:
                                await ctx.send(send_msg, delete_after=delete_after) if send_msg else await ctx.send(embed=send_embed, delete_after=delete_after)
                            else:
                                await ctx.send(send_msg) if send_msg else await ctx.send(embed=send_embed)
                        await try_edit(theEnd=True)
                        try:
                            await send.clear_reactions()
                        except:
                            if clear_required:
                                for reaction in send.reactions:
                                    if reaction.message.author == ctx.guild.me:
                                        await send.remove_reaction(reaction, ctx.guild.me)
                    except:
                        print(f"Failed to exit properly:\n{format_exc()}")
                    raise ExitRequest

                for emoji in to_react_with_main:
                    await send.add_reaction(emoji=emoji)

                # pylint: disable=unused-variable
                check, check2, reaction_filter = (lambda reaction, user: (user == ctx.author or user.id in access_ids) and reaction.message.channel == ctx.message.channel and int(reaction.message.id) == int(send.id), lambda reaction, user: reaction.message.channel == ctx.message.channel and user != ctx.guild.me and str(reaction.message.id) == str(send.id), to_react_with_main + (back_emoji, fun_emoji))

                async def mainFunc():
                    reaction, user = await bot.wait_for('reaction_add', check=check2, timeout=120.0)

                    async def rem_reaction(emoji=None, user=user, clear=False, required=False):
                        try:
                            await send.remove_reaction(emoji, user) if not clear and emoji else await send.clear_reactions()
                        except:
                            if required:
                                raise Exception(format_exc())

                    if reaction.emoji not in reaction_filter:
                        await rem_reaction(reaction.emoji, user)
                    else:
                        if user != ctx.author and user.id not in access_ids:
                            await rem_reaction(reaction.emoji, user)
                        else:
                            if reaction.emoji == music_emojis:
                                await send.edit(embed=music_embed)
                                await send.add_reaction(emoji=back_emoji)
                                await rem_reaction(music_emojis, user)
                            elif reaction.emoji == mod_emojis:
                                await send.edit(embed=mod_embed)
                                await send.add_reaction(emoji=back_emoji)
                                await rem_reaction(mod_emojis, user)
                            elif reaction.emoji == games_emoji:
                                await send.edit(embed=games_embed)
                                await send.add_reaction(emoji=back_emoji)
                                await rem_reaction(games_emoji, user)
                            elif reaction.emoji == server_emoji:
                                await send.edit(embed=server_embed)
                                await send.add_reaction(emoji=back_emoji)
                                await rem_reaction(server_emoji, user)
                            elif reaction.emoji == fun_emoji:
                                await send.edit(embed=func_embed)
                                await send.add_reaction(emoji=back_emoji)
                                await rem_reaction(fun_emoji, user)
                            elif reaction.emoji == info_emoji:
                                await send.edit(embed=info_embed)
                                await send.add_reaction(emoji=back_emoji)
                                await rem_reaction(info_emoji, user)
                            elif reaction.emoji == tools_emoji:
                                await send.edit(embed=Embed(title="<:Tools:663163816477196358> Settings - Choose a number", color=colrs[1]).set_thumbnail(url=tools_emoji.url).add_field(name="Modlog settings", value="\n".join(map(str, ['`1`│ Set message edit/delete log channel', f'`2`│ Manage what to do when one leaves or joins'])), inline=False).add_field(name="Other settings", value="\n".join(map(str, ['`3`│ Customize the commands prefix', '`4`│ Manage custom commands', '`5`│ Disable any settings'])), inline=False))
                                try:
                                    await send.clear_reactions()
                                except:
                                    for emoji in emojiIDs:
                                        await rem_reaction(bot.get_emoji(emoji), ctx.guild.me)
                                to_react_with = (back_emoji, emojis[1], emojis[2], emojis[3], emojis[4], emojis[5], cross_emoji)
                                for emoj in to_react_with:
                                    await send.add_reaction(emoji=emoj)

                                async def toComBack():
                                    reaction, user = await bot.wait_for('reaction_add', check=check2, timeout=120.0)
                                    if reaction.emoji not in to_react_with:
                                        await rem_reaction(reaction.emoji, user)
                                    else:
                                        if user != ctx.author and user.id not in access_ids:
                                            await rem_reaction(reaction.emoji, user)
                                        else:
                                            if reaction.emoji == back_emoji:
                                                await try_edit(required=True)
                                                try:
                                                    await send.clear_reactions()
                                                except:
                                                    for reaction in reaction.message.reactions:
                                                        if reaction.message.author == ctx.guild.me:
                                                            await rem_reaction(reaction, ctx.guild.me)
                                                for emoj in to_react_with_main:
                                                    await send.add_reaction(emoji=emoj)
                                                await mainFunc()

                                            elif reaction.emoji == emojis[1]:
                                                if user.id not in access_ids and not user.guild_permissions.manage_guild and not user.guild_permissions.manage_channels and not user.guild_permissions.manage_messages:
                                                    await ctx.send("You must have either manage messages, manage server, or manage channels permission to set the channel.", delete_after=10.0)
                                                    await rem_reaction(reaction.emoji, user)
                                                else:
                                                    await rem_reaction(clear=True)
                                                    await send.edit(embed=Embed(description="<:Hash:663295056060481556> Ping or say ID of the channel for message edit/delete logs.", color=colrs[1]))
                                                    wait = await bot.wait_for('message', check=lambda message: message.channel is ctx.channel and message.author is ctx.author, timeout=120.0)
                                                    getChannel = bot.get_channel(int(wait.content) if tryInt(wait.content) else int(''.join([i for i in wait.content if i.isdigit()])) if str(wait.content).startswith('<#') and str(wait.content).endswith('>') else None)

                                                    if not getChannel:
                                                        await ctx.send(escape_mentions(f"Couldn't find the channel '{wait.content}' in this server, try to run the command again but say ID instead this time." if not tryInt(wait.content) else f"Couldn't find a channel with the ID '{wait.content}' in this server, try to run the command again but mention the channel instead this time."))
                                                        return await try_edit()
                                                    if not getChannel.permissions_for(ctx.guild.me).send_messages:
                                                        return await end_help(send_msg=f"I don't have permission to send mesages in {getChannel.mention}. Please allow me '`Send Messages`' permissions and try again")

                                                    find_guild = modLogsDB.find_one({f'{ctx.guild.id}': {'$exists': True}}, {'_id': False}) or {}
                                                    if find_guild and find_guild.get(f'{ctx.guild.id}'):
                                                        find_guild[f'{ctx.guild.id}']['editDelete'] = {'ID': int(getChannel.id)}
                                                        modLogsDB.find_one_and_update({f'{ctx.guild.id}': {'$exists': True}}, {'$set': find_guild})
                                                    else:
                                                        find_guild["_id"], find_guild[f'{ctx.guild.id}'] = ctx.guild.name, {'editDelete': {'ID': int(getChannel.id)}}
                                                        modLogsDB.insert_one(find_guild)
                                                    return await end_help(send_embed=successful(f"Set 'message edit/delete' channel to {'this channel' if getChannel==ctx.channel else getChannel.mention}."))

                                            elif reaction.emoji == emojis[2]:
                                                await rem_reaction(emojis[2])
                                                await send.edit(embed=Embed(color=0xE4AA69, title="<:Tools:663163816477196358> Settings - When one levaes or joins", description="\n".join(map(str, ["`1`│ Set member join log channel", f"`2`│ └─ With custom message", "`3`│ Set member leave log channel", f"`4`│ └─ With custom message", "`5`│ Send private message on join", "`6`│ Give them certain roles"]))).set_thumbnail(url=tools_emoji.url))
                                                await send.remove_reaction(cross_emoji, ctx.guild.me)

                                                for emoj in (emojis[6], cross_emoji):
                                                    await send.add_reaction(emoj)

                                                to_react_with2 = emojis[1:7] + (back_emoji, cross_emoji)
                                                reaction, user = await bot.wait_for('reaction_add', check=check2, timeout=120.0)
                                                if reaction.emoji not in to_react_with2:
                                                    await rem_reaction(reaction.emoji, user)
                                                else:
                                                    if user != ctx.author and user.id not in access_ids:
                                                        await rem_reaction(reaction.emoji, user)
                                                    else:
                                                        if reaction.emoji == back_emoji:
                                                            await try_edit(required=True)
                                                            await send.clear_reactions()
                                                            for emoj in to_react_with_main:
                                                                await send.add_reaction(emoji=emoj)
                                                            await mainFunc()
                                                        
                                                        elif reaction.emoji == emojis[1]:
                                                            await rem_reaction(clear=True)
                                                            await send.edit(embed=Embed(description="<:Hash:663295056060481556> Ping or say ID of the channel to use for 'join' logs.", color=colrs[1]))
                                                            wait = await bot.wait_for('message', check=lambda message: message.channel is ctx.channel and message.author is ctx.author, timeout=120.0)
                                                            getChannel = bot.get_channel(int(wait.content) if tryInt(wait.content) else int(''.join([i for i in wait.content if i.isdigit()])) if str(wait.content).startswith('<#') and str(wait.content).endswith('>') else None)
                                                            if not getChannel:
                                                                return await ctx.send(escape_mentions(f"Couldn't see the channel '{wait.content}' in this server, try to run the command again but say ID instead this time." if not tryInt(wait.content) else f"Couldn't find a channel with the ID '{wait.content}' in this server, try to run the command again but mention the channel instead this time."))
                                                            if not getChannel.permissions_for(ctx.guild.me).send_messages:
                                                                return await end_help(send_msg=f"I don't have permission to send mesages in {getChannel.mention}. Please allow me '`Send Messages`' permissions and try again")
                                                            find_guild = modLogsDB.find_one({f'{ctx.guild.id}': {'$exists': True}}, {'_id': False}) or {}
                                                            if find_guild and find_guild.get(f'{ctx.guild.id}'):
                                                                if find_guild[f'{ctx.guild.id}'].get('joinMessage'):
                                                                    find_guild[f'{ctx.guild.id}']['joinMessage']['channel'] = {'ID': int(getChannel.id)}
                                                                else:
                                                                    find_guild[f'{ctx.guild.id}']['joinMessage'] = {'channel': {'ID': int(getChannel.id)}}
                                                                modLogsDB.find_one_and_update({f'{ctx.guild.id}': {'$exists': True}}, {'$set': find_guild})
                                                            else:
                                                                find_guild["_id"], find_guild[f'{ctx.guild.id}'] = ctx.guild.name, {"joinMessage": {'channel': {'ID': int(getChannel.id)}}}
                                                                modLogsDB.insert_one(find_guild)
                                                            return await end_help(send_embed=successful(f"Set welcome channel to {'this channel' if getChannel==ctx.channel else getChannel.mention} with default message"))
                                                        
                                                        elif reaction.emoji == emojis[2]:
                                                            await rem_reaction(clear=True)
                                                            await send.edit(embed=Embed(description="<:Hash:663295056060481556> Ping or say ID of the channel 'join' messages should be sent", color=colrs[1]))
                                                            
                                                            wait = await bot.wait_for('message', check=lambda message: message.channel is ctx.channel and message.author is ctx.author, timeout=120.0)
                                                            getChannel = bot.get_channel(int(wait.content) if tryInt(wait.content) else int(''.join([i for i in wait.content if i.isdigit()])) if str(wait.content).startswith('<#') and str(wait.content).endswith('>') else None)
                                                            if not getChannel:
                                                                return await end_help(send_msg=f"Couldn't see the channel '{wait.content}' in this server, try to run the command again but say ID instead this time." if (not tryInt(wait.content)) else f"Couldn't find a channel with the ID '{wait.content}' in this server, try to run the command again but mention the channel instead this time.", delete_after=10.0)
                                                            if not getChannel.permissions_for(ctx.guild.me).send_messages:
                                                                return await end_help(send_msg=f"I don't have permission to send mesages in {getChannel.mention}. Please allow me '`Send Messages`' permissions and try again")
                                                            await send.edit(embed=Embed(title="Now say the welcome message", color=colrs[1], description=f"You can use the formatters below in the message and they'll be replaced with the appropriate text i.e. {{user.mention}} will be replaced with {ctx.author.mention} when sent.\n```c\n{join_leave_formatters}\n```").set_footer(text="If you want bot to display an image too, upload it with the message."))
                                                            
                                                            wait = await bot.wait_for('message', check=lambda message: message.channel is ctx.channel and message.author is ctx.author, timeout=120.0)
                                                            find_guild = modLogsDB.find_one({f'{ctx.guild.id}': {'$exists': True}}, {'_id': False}) or {}
                                                            data = {'ID': int(getChannel.id), 'message': {'text': str(wait.content)}}
                                                            if wait.attachments:
                                                                data['message']['attachment'] = str(wait.attachments[0].url)
                                                            if find_guild and find_guild.get(f'{ctx.guild.id}'):
                                                                if find_guild[f'{ctx.guild.id}'].get('joinMessage'):
                                                                    find_guild[f'{ctx.guild.id}']['joinMessage']['channel'] = data
                                                                else:
                                                                    find_guild[f'{ctx.guild.id}']['joinMessage'] = {'channel': data}
                                                                modLogsDB.find_one_and_update({f'{ctx.guild.id}': {'$exists': True}}, {'$set': find_guild})
                                                            else:
                                                                find_guild["_id"], find_guild[f'{ctx.guild.id}'] = ctx.guild.name, {"joinMessage": {'channel': data}}
                                                                modLogsDB.insert_one(find_guild)
                                                            return await end_help(send_embed=successful(f"Set welcome channel to {getChannel.mention} with that message."))
                                                        
                                                        elif reaction.emoji == emojis[3]:
                                                            await rem_reaction(clear=True)
                                                            await send.edit(embed=Embed(description="<:Hash:663295056060481556> Ping or say ID of the channel to use for 'leave' logs.", color=colrs[1]))
                                                            
                                                            wait = await bot.wait_for('message', check=lambda message: message.channel is ctx.channel and message.author is ctx.author, timeout=120.0)
                                                            getChannel = bot.get_channel(int(wait.content) if tryInt(wait.content) else int(''.join([i for i in wait.content if i.isdigit()])) if str(wait.content).startswith('<#') and str(wait.content).endswith('>') else None)
                                                            if not getChannel:
                                                                await ctx.send(escape_mentions(f"Couldn't see the channel '{wait.content}' in this server, try to run the command again but say ID instead this time." if (not tryInt(wait.content)) else f"Couldn't find a channel with the ID '{wait.content}' in this server, try to run the command again but mention the channel instead this time."))
                                                                return await try_edit()
                                                            if not getChannel.permissions_for(ctx.guild.me).send_messages:
                                                                return await end_help(send_msg=f"I don't have permission to send mesages in {getChannel.mention}. Please allow me '`Send Messages`' permissions and try again")
                                                            find_guild = modLogsDB.find_one({f'{ctx.guild.id}': {'$exists': True}}, {'_id': False}) or {}
                                                            if find_guild and find_guild.get(f'{ctx.guild.id}'):
                                                                if find_guild[f'{ctx.guild.id}'].get('leaveMessage'):
                                                                    find_guild[f'{ctx.guild.id}']['leaveMessage']['channel'] = {'ID': int(getChannel.id)}
                                                                else:
                                                                    find_guild[f'{ctx.guild.id}']['leaveMessage'] = {'channel': {'ID': int(getChannel.id)}}
                                                                modLogsDB.find_one_and_update({f'{ctx.guild.id}': {'$exists': True}}, {'$set': find_guild})
                                                            else:
                                                                find_guild["_id"], find_guild[f'{ctx.guild.id}'] = ctx.guild.name, {"leaveMessage": {'channel': {'ID': int(getChannel.id)}}}
                                                                modLogsDB.insert_one(find_guild)
                                                            return await end_help(send_embed=successful(f"Set 'leave' channel to {getChannel.mention} with default message"))
                                                        
                                                        elif reaction.emoji == emojis[4]:
                                                            try:
                                                                await rem_reaction(clear=True)
                                                            except:
                                                                for reaction in reaction.message.reactions:
                                                                    if reaction.message.author == ctx.guild.me:
                                                                        await rem_reaction(reaction, ctx.guild.me)
                                                            await send.edit(embed=Embed(description="<:Hash:663295056060481556> Ping or say ID of the channel 'leave' messages should be sent", color=colrs[1]))
                                                            wait = await bot.wait_for('message', check=lambda message: message.channel is ctx.channel and message.author is ctx.author, timeout=120.0)
                                                            getChannel = bot.get_channel(int(wait.content) if tryInt(wait.content) else int(''.join([i for i in wait.content if i.isdigit()])) if str(wait.content).startswith('<#') and str(wait.content).endswith('>') else None)
                                                            if not getChannel:
                                                                await ctx.send(escape_mentions(f"Couldn't see the channel '{wait.content}' in this server, try to run the command again but say ID instead this time." if not tryInt(wait.content) else f"Couldn't find a channel with the ID '{wait.content}' in this server, try to run the command again but mention the channel instead this time."))
                                                                return await try_edit()
                                                            if not getChannel.permissions_for(ctx.guild.me).send_messages:
                                                                return await end_help(send_msg=f"I don't have permission to send mesages in {getChannel.mention}. Please allow me '`Send Messages`' permissions and try again")

                                                            await send.edit(embed=Embed(title="Now say the good-bye message", color=colrs[1], description=f"You can use the formatters below in the message and they'll be replaced with the appropriate text i.e. {{user.mention}} will be replaced with {ctx.author.mention} when sent.\n```c\n{join_leave_formatters}\n```").set_footer(text="If you want bot to display an image too, upload it with the message."))

                                                            wait = await bot.wait_for('message', check=lambda message: message.channel is ctx.channel and message.author is ctx.author, timeout=120.0)
                                                            find_guild = modLogsDB.find_one({f'{ctx.guild.id}': {'$exists': True}}, {'_id': False}) or {}
                                                            data = {'ID': int(getChannel.id), 'message': {'text': str(wait.content)}}
                                                            if wait.attachments:
                                                                data['message']['attachment'] = str(wait.attachments[0].url)
                                                            if find_guild and find_guild.get(f'{ctx.guild.id}'):
                                                                if find_guild[f'{ctx.guild.id}'].get('leaveMessage'):
                                                                    find_guild[f'{ctx.guild.id}']['leaveMessage']['channel'] = data
                                                                else:
                                                                    find_guild[f'{ctx.guild.id}']['leaveMessage'] = {'channel': data}
                                                                modLogsDB.find_one_and_update({f'{ctx.guild.id}': {'$exists': True}}, {'$set': find_guild})
                                                            else:
                                                                find_guild["_id"], find_guild[f'{ctx.guild.id}'] = ctx.guild.name, {"leaveMessage": {'channel': data}}
                                                                modLogsDB.insert_one(find_guild)
                                                            return await end_help(send_embed=successful(f"Set 'leave' channel to {getChannel.mention} with that message."))
                                                        
                                                        elif reaction.emoji == emojis[5]:
                                                            await rem_reaction(clear=True)
                                                            await send.edit(embed=Embed(title="Say the message to PM them", color=colrs[1], description=f"You can use the formatters below in the message and they'll be replaced with the appropriate text i.e. {{user.mention}} will be replaced with {ctx.author.mention} when sent.\n```c\n{join_leave_formatters}\n```").set_footer(text="If you want bot to display an image too, upload it with the message."))

                                                            wait = await bot.wait_for('message', check=lambda message: message.channel is ctx.channel and message.author is ctx.author, timeout=120.0)
                                                            find_guild = modLogsDB.find_one({f'{ctx.guild.id}': {'$exists': True}}, {'_id': False}) or {}
                                                            data = {'message': {'text': str(wait.content)}}
                                                            if wait.attachments:
                                                                data['message']['attachment'] = str(wait.attachments[0].url)
                                                            if find_guild and find_guild.get(f'{ctx.guild.id}'):
                                                                if find_guild[f'{ctx.guild.id}'].get('joinMessage'):
                                                                    if find_guild[f'{ctx.guild.id}']['joinMessage'].get('user'):
                                                                        find_guild[f'{ctx.guild.id}']['joinMessage']['user']['message'] = data['message']
                                                                    else:
                                                                        find_guild[f'{ctx.guild.id}']['joinMessage']['user'] = data
                                                                else:
                                                                    find_guild[f'{ctx.guild.id}']['joinMessage'] = {'user': data}
                                                                modLogsDB.find_one_and_update({f'{ctx.guild.id}': {'$exists': True}}, {'$set': find_guild})
                                                            else:
                                                                find_guild["_id"], find_guild[f'{ctx.guild.id}'] = ctx.guild.name, {'joinMessage': {'user': data}}
                                                                modLogsDB.insert_one(find_guild)
                                                            return await end_help(send_embed=successful(f"New members will now be PM'd that message"))
                                                        
                                                        elif reaction.emoji == emojis[6]:

                                                            async def pingRole():
                                                                try:
                                                                    if len(await ctx.guild.fetch_roles()) < 4:
                                                                        return 'role1, role2, role3'
                                                                    lst = []
                                                                    for pos in range(3):
                                                                        lst.append([x.mention for x in await ctx.guild.fetch_roles() if x != ctx.guild.default_role][pos] if (pos == 0) else [x.name for x in await ctx.guild.fetch_roles() if x != ctx.guild.default_role][pos] if (pos == 1) else [x.id for x in await ctx.guild.fetch_roles() if x != ctx.guild.default_role][pos])
                                                                    return ', '.join(map(str, lst))
                                                                except:
                                                                    return 'role1, role2, role3'

                                                            if not ctx.guild.me.guild_permissions.manage_roles:
                                                                return await end_help(send_msg=f"I'm missing `manage roles` permission which is required to give roles.", delete_after=10.0)
                                                            text = f"Ping the role (or say it's name or ID) that should be given to members when they join. If you want multiple roles to be given then ping them (or say their names or IDs) joined with a comma inside square brackets\nExample: [{await pingRole()}]\nThis is case sensitive so role name and case must be written as it is."
                                                            await send.edit(embed=Embed(title=f"Waiting {loading_msg(alone=True)}", color=colrs[1], description=text).set_footer(text="If I can't find one of the given roles, I'll ignore it and continue to look for others."))
                                                            await rem_reaction(clear=True)
                                                            try:
                                                                wait = await bot.wait_for('message', check=lambda message: message.channel is ctx.channel and message.author is ctx.author, timeout=120.0)
                                                            except AsyncioTimeoutError:
                                                                return

                                                            def findTheRoles(text):
                                                                from ast import literal_eval

                                                                role_ids = []
                                                                if re_search(r"\s*\[.*\]\s*", text):
                                                                    toList = re_sub(r"\[\s?", "['", re_sub(r"\s?\]", "']", re_sub(r"\s?,\s?", "', '", text.replace("\\", "\\\\'").replace("'", "\\'"))))
                                                                    rolesList = literal_eval(toList)
                                                                    for role in rolesList:
                                                                        if role.strip():
                                                                            if re_search(r"<@&([0-9]+)>", role):
                                                                                get_the_role = get(ctx.guild.roles, id=int(role.strip(' <@&> ')))
                                                                            elif re_search(r"([0-9]+)", role):
                                                                                get_the_role = get(ctx.guild.roles, id=int(role))
                                                                            else:
                                                                                get_the_role = get(ctx.guild.roles, name=role)
                                                                            if get_the_role:
                                                                                role_ids.append(get_the_role.id)
                                                                
                                                                elif text.strip():
                                                                    if re_search(r"<@&([0-9]+)>", text.strip()):
                                                                        get_the_role = get(ctx.guild.roles, id=int(text.strip(' <@&> ')))
                                                                    elif re_search(r"([0-9]+)", text.strip()):
                                                                        get_the_role = get(ctx.guild.roles, id=int(text.strip()))
                                                                    else:
                                                                        get_the_role = get(ctx.guild.roles, name=text.strip())
                                                                    if get_the_role:
                                                                        role_ids.append(get_the_role.id)
                                                                del literal_eval
                                                                return [ctx.guild.get_role(iD) for iD in role_ids]

                                                            findTheRoles = findTheRoles(wait.content)
                                                            if not findTheRoles:
                                                                if "[" and "]" in wait.content:
                                                                    return await end_help(send_msg="Couldn't find any role from '{}', if you used a name, check if it is the exact name or the exact case and try again{}".format(wait.content.strip('[]'), " and I didn't see any commas, if you gave more than one role make sure they were seperated by a comma." if "," not in wait.content else "."))
                                                                else:
                                                                    return await end_help(send_msg=f"I couldn't find the role %s" % (f"with the ID '{wait.content}', check if the ID is right or run the command again but this time ping the role or say it's name" if tryInt(wait.content) else f"'{wait.content}'"))
                                                            rolesList = ', '.join(map(str, [role.name for role in findTheRoles]))

                                                            roles = []
                                                            for role in findTheRoles:
                                                                if role.position > ctx.guild.me.top_role.position:
                                                                    roles.append(role.name)
                                                            if roles:
                                                                return await ctx.send(f"I can't give one or more of the roles you chose. If you have the permissions, put my role over the role(s) in settings then try again")

                                                            find_guild = modLogsDB.find_one({f'{ctx.guild.id}': {'$exists': True}}, {'_id': False}) or {}
                                                            data = {'roles': list(role.id for role in findTheRoles)}
                                                            if find_guild and find_guild.get(f'{ctx.guild.id}'):
                                                                if find_guild[f'{ctx.guild.id}'].get('joinMessage'):
                                                                    if find_guild[f'{ctx.guild.id}']['joinMessage'].get('user'):
                                                                        find_guild[f'{ctx.guild.id}']['joinMessage']['user']['roles'] = list(role.id for role in findTheRoles)
                                                                    else:
                                                                        find_guild[f'{ctx.guild.id}']['joinMessage']['user'] = data
                                                                else:
                                                                    find_guild[f'{ctx.guild.id}']['joinMessage'] = {'user': data}
                                                                modLogsDB.find_one_and_update({f'{ctx.guild.id}': {'$exists': True}}, {'$set': find_guild})
                                                            else:
                                                                find_guild["_id"], find_guild[f'{ctx.guild.id}'] = ctx.guild.name, {'joinMessage': {'user': data}}
                                                                modLogsDB.insert_one(find_guild)
                                                            return await end_help(send_embed=successful(f"New members'll be given {'the role' if len(findTheRoles)==1 else 'these roles'} '{rolesList}'"))
                                                        
                                                        elif reaction.emoji == cross_emoji:
                                                            return await end_help()
                                            
                                            elif reaction.emoji == emojis[3]:
                                                try:
                                                    await send.clear_reactions()
                                                except:
                                                    for emoji in emojiIDs:
                                                        await rem_reaction(bot.get_emoji(emoji), ctx.guild.me)
                                                await send.edit(embed=Embed(title="<:Command:691849893274452010> New commands prefix", description="Say a new prefix to use for commands or `cancel` to cancel", color=colrs[1]).set_footer(text="To return to the default prefix, just say ..."))
                                                prefix = await bot.wait_for('message', check=lambda message: message.channel is ctx.channel and message.author is ctx.author, timeout=120.0)
                                                if prefix.content.lower() in ("cancel", "cancle"):
                                                    return await end_help(send_msg="Canceled")
                                                try:
                                                    if prefix.content == '...' or not prefix.content:
                                                        try:
                                                            if botPrefixDB.find_one({'_id': f'{ctx.guild.id}'}):
                                                                botPrefixDB.find_one_and_delete({'_id': f'{ctx.guild.id}'})
                                                                return await ctx.send(f"Prefix reset to the default which is `...`")
                                                            else:
                                                                return await ctx.send('That is the current prefix')
                                                        except:
                                                            print(format_exc())
                                                    elif re_match("­|\u200b", prefix.content):
                                                        return await ctx.send("Please use a prefix that has no zero width characters so that everyone can be able to use it.")
                                                    elif len(prefix.content) > 25:
                                                        return await ctx.send("That prefix is quite long, limit is 25 characters.")
                                                    elif " " in prefix.content:
                                                        return await ctx.send("Prefix cannot include spaces")
                                                    else:
                                                        try:
                                                            botPrefixDB.find_one_and_update({'_id': f'{ctx.guild.id}'}, {'$set': {'prefix': prefix.content, 'guildName': ctx.guild.name}}, upsert=True)
                                                        except Exception as e:
                                                            return await ctx.send(f"There was a a little problem while changing the prefix, please use the feedback command to send the error blow to my developer.\n```\n{e}\n```")

                                                        return await ctx.send(embed=Embed(color=colrs[2], title="<:Mark:663230689860386846> Custom prefix created:", description=f"New Prefix: {botPrefixDB.find_one({'_id': f'{ctx.guild.id}'})['prefix']}\n**NOTE:** Bot'll nolonger respond to the default prefix in this server which is ...").set_footer(text="So don't forget the prefix you set 👀. But if you do forget, ping me."))
                                                except Exception as e:
                                                    print(format_exc())
                                                    return await ctx(f"There was an error: {e}\nIf you don't know the problem please screenshot this together with your command and say `{ctx.prefix}feedback <upload your screenshot, or say what you want to say>` send the error to the bot owner.")
                                            
                                            elif reaction.emoji == emojis[4]:
                                                await send.edit(embed=custom_cmd_helper(ctx).set_footer(text="Go to custom commands in help menu to see the custom cmds if any."))
                                                await rem_reaction(emojis[4], user)
                                                await toComBack()
                                            
                                            elif reaction.emoji == emojis[5]:
                                                await send.edit(embed=Embed(color=0xE4AA69, title="<:Tools:663163816477196358> Settings - Choose a feature to disable", description="\n".join(map(str, ["`1`│ Disable member join channel logging", "`2`│ Reset bot prefix to default", "`3`│ Disable logging deleted or edited messages", f"`4`│ Disable private messaging on member join", "`5`│ Disable member leave channel logging", f"`6`│ Don't give a role to new members"]))).set_thumbnail(url=tools_emoji.url).set_footer(text=f"Say '{ctx.prefix}cmd del <command>' for custom cmds"))
                                                await rem_reaction(emojis[5], user)
                                                
                                                # for emoj in (emojis[5], emojis[4]):
                                                #     try: await send.clear_reaction(emoj)
                                                #     except: await rem_reaction(emoj, ctx.guild.me)
                                                
                                                await rem_reaction(cross_emoji, ctx.guild.me)
                                                for emoj in (emojis[6], cross_emoji):
                                                    await send.add_reaction(emoj)
                                                reaction, user = await bot.wait_for('reaction_add', check=check)
                                                if reaction.emoji == back_emoji:
                                                    await try_edit(required=True)
                                                    try:
                                                        await send.clear_reactions()
                                                    except:
                                                        for reaction in send.reactions:
                                                            if reaction.message.author == ctx.guild.me:
                                                                await rem_reaction(reaction, ctx.guild.me)
                                                    for emoj in to_react_with_main:
                                                        await send.add_reaction(emoji=emoj)
                                                    await mainFunc()
                                                
                                                elif reaction.emoji == emojis[1]:
                                                    chanFind, channel_id = modLogsDB.find_one({f"{ctx.guild.id}.joinMessage.channel": {'$exists': True}}, {'_id': False}), 0
                                                    if chanFind:
                                                        if len(chanFind[f'{ctx.guild.id}']) == 1 and len(chanFind[f'{ctx.guild.id}']['joinMessage']) == 1:
                                                            channel_id = chanFind[f'{ctx.guild.id}']['joinMessage']['channel']['ID']
                                                            modLogsDB.find_one_and_delete({f'{ctx.guild.id}': {'$exists': True}})
                                                        elif len(chanFind[f'{ctx.guild.id}']['joinMessage']) > 1:
                                                            channel_id = chanFind[f'{ctx.guild.id}']['joinMessage']['channel']['ID']
                                                            del chanFind[f'{ctx.guild.id}']['joinMessage']['channel']
                                                            modLogsDB.find_one_and_update({f'{ctx.guild.id}': {'$exists': True}}, {'$set': chanFind})
                                                        else:
                                                            channel_id = chanFind[f'{ctx.guild.id}']['joinMessage']['channel']['ID']
                                                            del chanFind[f'{ctx.guild.id}']['joinMessage']
                                                            modLogsDB.find_one_and_update({f'{ctx.guild.id}': {'$exists': True}}, {'$set': chanFind})
                                                        return await end_help(send_embed=successful(f"Bot'll nolonger log to {ctx.guild.get_channel(channel_id).mention if ctx.guild.get_channel(channel_id) else 'the channel'} when new members join."), delete_after=10.0)
                                                    else:
                                                        return await end_help(send_msg="Bot wasn't already logging to any channel")
                                                
                                                elif reaction.emoji == emojis[2]:
                                                    await rem_reaction(emojis[3])
                                                    if botPrefixDB.find_one({f'{ctx.guild.id}': {'$exists': True}}) == None:
                                                        return await ctx.channel.send("Bot doesn't have a custom prefix to disable")
                                                    else:
                                                        try:
                                                            botPrefixDB.find_one_and_delete({f'{ctx.guild.id}': {'$exists': True}})
                                                            return await end_help(send_embed=Embed(color=colrs[2], title="<:Mark:663230689860386846> Success!", description=f"Prefix successfully reset to default which is `{ctx.prefix}`"))
                                                        except Exception as e:
                                                            return await end_help(send_msg=f"Error disabling prefix\n```\n{e}\n```\n")
                                                
                                                elif reaction.emoji == emojis[3]:
                                                    await rem_reaction(emojis[2])
                                                    find_guild, channel_id = modLogsDB.find_one({f'{ctx.guild.id}.editDelete': {'$exists': True}}, {'_id': False}), 0
                                                    if find_guild and find_guild.get(f'{ctx.guild.id}'):
                                                        if len(find_guild[f'{ctx.guild.id}']) > 1:
                                                            channel_id = find_guild[f'{ctx.guild.id}']['editDelete']['ID']
                                                            del find_guild[f'{ctx.guild.id}']['editDelete']
                                                            modLogsDB.find_one_and_update({f'{ctx.guild.id}': {'$exists': True}}, {'$set': find_guild})
                                                        else:
                                                            channel_id = find_guild[f'{ctx.guild.id}']['editDelete']['ID']
                                                            modLogsDB.find_one_and_delete({f'{ctx.guild.id}': {'$exists': True}})
                                                        return await end_help(send_embed=successful(f"Edited/deleted messages'll nolonger be logged{' in'+str(ctx.guild.get_channel(channel_id).mention) if ctx.guild.get_channel(channel_id) else '.'}"), delete_after=10.0)
                                                    else:
                                                        return await end_help(send_msg="No message edit or delete logging channel was set.", delete_after=10.0)
                                                
                                                elif reaction.emoji == emojis[4]:
                                                    userFind = modLogsDB.find_one({f"{ctx.guild.id}.joinMessage.user.message": {'$exists': True}}, {'_id': False})
                                                    if userFind:
                                                        if len(userFind[f'{ctx.guild.id}']) == 1 and len(userFind[f'{ctx.guild.id}']['joinMessage']) == 1 and len(userFind[f'{ctx.guild.id}']['joinMessage']['user']) == 1:
                                                            modLogsDB.find_one_and_delete({f'{ctx.guild.id}': {'$exists': True}})
                                                        else:
                                                            if len(userFind[f'{ctx.guild.id}']['joinMessage']['user']) > 1:
                                                                del userFind[f'{ctx.guild.id}']['joinMessage']['user']['message']
                                                                modLogsDB.find_one_and_update({f'{ctx.guild.id}': {'$exists': True}}, {'$set': userFind})
                                                            else:
                                                                del userFind[f'{ctx.guild.id}']['joinMessage']['user']
                                                                modLogsDB.find_one_and_update({f'{ctx.guild.id}': {'$exists': True}}, {'$set': userFind})
                                                        return await end_help(send_embed=successful(f"New member'll nolonger be private messaged on join."), delete_after=10.0)
                                                    else:
                                                        return await end_help(send_msg="Bot wasn't set to private message new members before.")
                                                
                                                elif reaction.emoji == emojis[5]:
                                                    chanFind, channel_id = modLogsDB.find_one({f"{ctx.guild.id}.leaveMessage.channel": {'$exists': True}}, {'_id': False}), 0
                                                    if chanFind:
                                                        if len(chanFind[f'{ctx.guild.id}']) == 1 and len(chanFind[f'{ctx.guild.id}']['leaveMessage']) == 1:
                                                            channel_id = chanFind[f'{ctx.guild.id}']['leaveMessage']['channel']['ID']
                                                            modLogsDB.find_one_and_delete({f'{ctx.guild.id}': {'$exists': True}})
                                                        elif len(chanFind[f'{ctx.guild.id}']['leaveMessage']) > 1:
                                                            channel_id = chanFind[f'{ctx.guild.id}']['leaveMessage']['channel']['ID']
                                                            del chanFind[f'{ctx.guild.id}']['leaveMessage']['channel']
                                                            modLogsDB.find_one_and_update({f'{ctx.guild.id}': {'$exists': True}}, {'$set': chanFind})
                                                        else:
                                                            channel_id = chanFind[f'{ctx.guild.id}']['leaveMessage']['channel']['ID']
                                                            del chanFind[f'{ctx.guild.id}']['leaveMessage']
                                                            modLogsDB.find_one_and_update({f'{ctx.guild.id}': {'$exists': True}}, {'$set': chanFind})
                                                        return await end_help(send_embed=successful(f"Bot'll nolonger log to {ctx.guild.get_channel(channel_id).mention if ctx.guild.get_channel(channel_id) else 'the channel'} when members leave."), delete_after=10.0)
                                                    else:
                                                        return await end_help(send_msg="Bot wasn't already logging to any channel")
                                                
                                                elif reaction.emoji == emojis[6]:
                                                    roleFind, roles = modLogsDB.find_one({f"{ctx.guild.id}.joinMessage.user.roles": {'$exists': True}}, {'_id': False}), []
                                                    if roleFind:
                                                        if len(roleFind[f'{ctx.guild.id}']) == 1 and len(roleFind[f'{ctx.guild.id}']['joinMessage']) == 1 and len(roleFind[f'{ctx.guild.id}']['joinMessage']['user']) == 1:
                                                            roles = roleFind[f'{ctx.guild.id}']['joinMessage']['user']['roles']
                                                            modLogsDB.find_one_and_delete({f'{ctx.guild.id}': {'$exists': True}})
                                                        else:
                                                            if len(roleFind[f'{ctx.guild.id}']['joinMessage']['user']) > 1:
                                                                roles = roleFind[f'{ctx.guild.id}']['joinMessage']['user']['roles']
                                                                del roleFind[f'{ctx.guild.id}']['joinMessage']['user']['roles']
                                                                modLogsDB.find_one_and_update({f'{ctx.guild.id}': {'$exists': True}}, {'$set': roleFind})
                                                            else:
                                                                roles = roleFind[f'{ctx.guild.id}']['joinMessage']['user']['roles']
                                                                del roleFind[f'{ctx.guild.id}']['joinMessage']
                                                                modLogsDB.find_one_and_update({f'{ctx.guild.id}': {'$exists': True}}, {'$set': roleFind})
                                                        roles = [ctx.guild.get_role(x) for x in roles]
                                                        return await end_help(send_embed=successful(f"New member'll nolonger be given {'these roles '+', '.join(x.mention for x in roles) if roles and len(roles)>1 else 'this role '+', '.join(x.mention for x in roles) if roles else 'the role(s).'}"), delete_after=10.0)
                                                    else:
                                                        return await end_help(send_msg="Bot wasn't set to give any roles to new members.")
                                                
                                                elif reaction.emoji == cross_emoji:
                                                    return await end_help()
                                            
                                            elif reaction.emoji == cross_emoji:
                                                return await end_help()
                                            
                                            # else: await mainFunc()

                                await toComBack()
                            elif reaction.emoji == back_emoji:
                                await try_edit(required=True)
                                for who in (bot.user, user):
                                    await rem_reaction(back_emoji, who)
                            
                            elif reaction.emoji == custom_cmd_emoji:
                                await send.edit(embed=custom_cmd_embed)
                                await send.add_reaction(emoji=back_emoji)
                                await rem_reaction(custom_cmd_emoji, user)
                            
                            elif reaction.emoji == cross_emoji:
                                return await end_help()

                while True:
                    await mainFunc()
            except AsyncioTimeoutError: return
            except ExitRequest: return
            except HTTPException: return print(format_exc())
            except: pass
            finally:
                try: await end_help()
                except ExitRequest: return
        else:
            return await ctx.author.send(f"Hi, here's my help menu https://troybot.xyz/commands/{ctx.guild.id}/")
    else:
        if cmd := bot.get_command(command_name):
            params = {x: cmd.params[x] for x in cmd.params if x not in ('ctx', 'self')}
            try:
                return await ctx.send(embed=(Embed(color=0x2F3136).add_field(name=cmd.brief or cmd.description or 'No description provided.', value=f"{cmd.description+chr(10) if cmd.brief else '​'}\n{ctx.prefix}{cmd}{'|'+'|'.join(cmd.aliases) if cmd.aliases else ''} {' '.join(f'*<{p}>*' if not re_search(' *= *None', str(params[p])) else f'*[{p}]*' for p in params.keys())}".replace('_', ' ').replace('<<prefix>>', ctx.prefix).replace('<<gid>>', ctx.guild.id).replace('<<cmd>>', ctx.kwargs['command_name']))))
            except:
                await ctx.send(f'''{'**'+cmd.brief+'**'+chr(10) if cmd.brief else ''}{cmd.description or 'No description provided.'}\n\n{ctx.prefix}{cmd}{'|'+'|'.join(cmd.aliases) if cmd.aliases else ''} {' '.join(f'<{p}>' if not re_search(' *= *None', str(params[p])) else f'[{p}]' for p in params.keys())}'''.replace('_', ' ').replace('<<prefix>>', ctx.prefix).replace('<<cmd>>', ctx.kwargs['command_name']))
                return print('Error in help menu\n', format_exc())
        await ctx.send(escape_mentions(f"Command \"{command_name}\" does not seem to exist."))


from textwrap import indent
from contextlib import redirect_stdout


@bot.command(aliases=('eval',), brief="Run code in a chosen langauge from code-block", description="**Example:**\n<<prefix>><<cmd>>\n```py\nprint(\"Hello world\")\n```")
async def run(ctx, *, code=None):
    error, output, mark = False, False, True
    if ctx.author.id in access_ids and ctx.invoked_with == 'eval':
        stdout, env = IoStringIO(), {'ctx': ctx, 'bot': bot}
        env.update(globals())

        try:
            exec(f'''async def func():\n{indent(chr(10).join(code.split(chr(10))[1:-1]) if code.startswith('```') and code.endswith('```') else code, "  ")}''', env)
        except Exception as e:
            error = await ctx.send(f'```autohotkey\n{e.__class__.__name__}: ' + str(e).replace("`", "\\`") + '\n```')
            return await ctx.message.add_reaction('\u2049')
        func = env['func']

        try:
            with redirect_stdout(stdout):
                ret = await func()
        except:
            error = await ctx.send(f'```autohotkey\n{stdout.getvalue()}{format_exc()}\n```')
        else:
            value = stdout.getvalue()
            if ret is None:
                if value:
                    try:
                        output = await ctx.send(value)
                    except:
                        paginated_text = paginate(value)
                        for page in paginated_text:
                            if page == paginated_text[-1]:
                                output = await ctx.send(page)
                                break
                            await ctx.send(page)
            else:
                try:
                    output = await ctx.send(f'{value}{ret}')
                except:
                    paginated_text = paginate(f"{value}{ret}")
                    for page in paginated_text:
                        if page == paginated_text[-1]:
                            output = await ctx.send(page)
                            break
                        await ctx.send(page)
    else:
        try:
            plang = re_search(r'^```(\w+)', code)
            if not plang:
                return await ctx.send("Code must be in a code block which includes the programming language name or extension eg. \\`\\`\\`py")

            plang = plang.groups()[0].lower()
            compilers = ("cpython-head", "cpython-2.7-head", "gcc-head-pp", "gcc-head-c", "mono-head", "nodejs-head", "coffeescript-head", "openjdk-head", "ghc-8.4.2", "cmake-head", "crystal-head", "elixir-head", "erlang-head", "dmd-head", "ruby-head", "rust-head", "sqlite-head", "clisp-2.49", "go-head", "fsharp-head", "scala-2.13.x", "swift-head", "typescript-3.9.5", "vim-head", "lua-5.4.0", "nim-head", "php-head", "perl-head", "rill-head", "r-head", "fpc-head", "ocaml-head", "julia-head", "nim-head", "lazyk", "ghc-head", "groovy-3.0.7", "openssl-head", "pony-head")
            lang = re_sub(r"^py(thon)?3?$", "cpython-head", re_sub(r"^py(thon)?2$", "cpython-2.7-head", re_sub(r"^c(pp|\+\+)$", "gcc-head-pp", re_sub(r"^c$", "gcc-head-c", re_sub(r"^c([s#]|sharp)$", "mono-head", re_sub(r"^j(s|avascript)$", "nodejs-head", re_sub(r"^coffee(script)?$", "coffeescript-head", re_sub(r"^java$", "openjdk-head", re_sub(r"^h(sc|askell)$", "ghc-8.4.2", re_sub(r"^cmake$", "cmake-head", re_sub(r"^cr(ystal)?$", "crystal-head", re_sub(r"^e(xs|lixir)$", "elixir-head", re_sub(r"^[he]rl(ang)?$", "erlang-head", re_sub(r"^d$", "dmd-head", re_sub(r"^r(b|uby)$", "ruby-head", re_sub(r"^r(s|ust)$", "rust-head", re_sub(r"^(db|sql(ite3?)?)$", "sqlite-head", re_sub(r"^li?sp$", "clisp-2.49", re_sub(r"^go$", "go-head", re_sub(r"^(f[#s]|fsharp)$", "fsharp-head", re_sub(r"^(sc[ab]|scala)$", "scala-2.13.x", re_sub(r"^swift$", "swift-head", re_sub(r"^t(ypescript|s)$", "typescript-3.9.5", re_sub(r"^vim$", "vim-head", re_sub(r"^lua$", "lua-5.4.0", re_sub(r"^nim$", "nim-head", re_sub(r"^php$", "php-head", re_sub(r"^p(er)?l$", "perl-head", re_sub(r"^rill$", "rill-head", re_sub(r"^r$", "r-head", re_sub(r"^(rpc|pascal)$", "fpc-head", re_sub(r"^(ocaml|ml)$", "ocaml-head", re_sub(r"^(jl|julia)$", "julia-head", re_sub(r"^nim$", "nim-head", re_sub(r"^lazyk$", "lazyk", re_sub(r"^h(sc|askell)$", "ghc-head", re_sub(r"^g(roo)?vy$", "groovy-3.0.7", re_sub(r"^(crl|csr|open(ssl)?)$", "openssl-head", re_sub(r"^pony$", "pony-head", plang)))))))))))))))))))))))))))))))))))))))

            if lang not in compilers:
                langs = sorted(('bash', 'c', 'c++', 'c#', 'cmake', 'coffeescript', 'crystal', 'd', 'elixir', 'erlang', 'f#', 'go', 'groovy', 'haskell', 'java', 'javascript', 'julia', 'lazyk', 'lisp', 'lua', 'nim', 'ocaml', 'openssl', 'pascal', 'perl', 'php', 'pony', 'python', 'python2', 'r', 'rill', 'ruby', 'rust', 'scala', 'sql', 'swift', 'typescript', 'vim'))
                rows = f'{langs[0]:15}'.capitalize()
                for lang in langs[1:]:
                    rows += f'{lang:15}'.capitalize()

                rows = rows.replace('Sql', 'SQL').replace('Php', 'PHP').replace('Openssl', 'OpenSSL').replace('script', 'Script')
                return await ctx.reply(f"`{plang}` is either an anvalid extension/language, or not a supported one. Here are the supported languages:\n\n```\n{rows}\n```")

            async with ctx.channel.typing():
                code = '\n'.join(code.splitlines()[1:-1])
                data = await aiohttp_request("https://wandbox.org/api/compile.json", 'json', data={"code": code, "compiler": lang}, get=False, timeout=10, headers={"Content-type": "application/json"})
                output = data.get('program_message', data.get('program_error', '')).strip()
                if not output:
                    if data.get('signal') == 'Killed':
                        return await ctx.reply(f"_Process killed._")
                    return await ctx.reply("_No output._")

            for re in re_findall(r'<@!?\d{15,}>', output):
                output = output.replace(re, f"@{m.name}" if (m := ctx.guild.get_member(int(re.strip('<@!>')))) else re)
            for re in re_findall(r'<@&\d{15,}>', output):
                output = output.replace(re, f"@{m.name}" if (m := ctx.guild.get_role(int(re.strip('<@&>')))) else re)
            await ctx.reply(output if data['status'] == '0' else f"```autohotkey\n{output}\n```")

        except AsyncioTimeoutError:
            await ctx.reply('Timeout: Your code took long to return an output.')
        except HTTPException as er:
            if er.code == 50035:
                await ctx.reply("Unknown error in body—perhaps the output has more than 2000 characters?")
            else:
                await ctx.reply("There was an internal error while running your code.")
        except:
            await ctx.reply("There was an internal error while running your code.")
            print(format_exc())


if __name__ != '__main__':
    exit(f"'{__name__}.py' isn't the main file as it's being imported by the file {__import__('__main__').__file__}. Exiting...")

for extension in extentions:
    try:
        bot.load_extension(extension)
    except:
        exit(f'Failed loadng extension {extension}\n' + format_exc())

bot.run(tkn)
