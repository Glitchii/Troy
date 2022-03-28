from datetime import datetime
from typing import Union
from urllib.parse import quote
from json import loads as json_loads
from json.decoder import JSONDecodeError
from random import randint, choice as randchoice
from io import StringIO as IoStringIO, BytesIO as IoBytesIO
from re import sub as re_sub, compile as re_compile, search as re_search, findall as re_findall
from time import time as time_time
from traceback import format_exc
from ast import literal_eval
from platform import system, machine
from sys import version_info
from asyncio import TimeoutError as AsyncioTimeoutError, sleep as asyncio_sleep

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from discord import Embed, Member, User, Colour, File, TextChannel, Forbidden, HTTPException
from discord.utils import escape_mentions
from discord.ext import commands
from googletrans import Translator

from imports import (
    colrs, access_ids, aiohttp_request, bot, bot_owner,
    customCmdsDB, loading_msg, msg_formated, send_me, sendingTo, successful, tryInt, unsuccessful,
    fson, custom_cmd_helper, get_fun_fact, wolframID
)

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Module: Misc loaded")

    @commands.command(aliases=("info", "stats",), description="Shows Some information about the bot")
    async def about(self, ctx):
        try:
            loading = await ctx.send(loading_msg())
            seconds = time_time() - time_time()
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            d, h = divmod(h, 24)
            w, d = divmod(d, 7)

            await ctx.send(embed = Embed(color=colrs[1], description=f"[Bot Invite Link](https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=1479928959)", url=f"https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=1479928959")
                .set_thumbnail(url="https://i.imgur.com/CNYbdaV.png")
                .set_author(name=F"Owned by: {bot_owner()}", icon_url=bot_owner().avatar_url)
                .add_field(name="Library:", value=f"[Discord.py](https://github.com/Rapptz/discord.py) (Python {version_info[0]}.{version_info[1]}.{version_info[2]}")
                .add_field(name="System", value=f"{system()} ({machine()})")
                .add_field(name="Up-time:", value=f"{int(w)}w : {int(d)}d : {int(h)}h : {int(m)}m : {int(s)}s")
                .add_field(name="Latency (ping):", value=f"{round(bot.latency, 3)} ms")
                .add_field(name="Servers:", value=len(self.bot.guilds))
                .add_field(name="Users:", value=len(self.bot.users))
                .add_field(name="Website:", value="https://troybot.xyz")
                .add_field(name="Top.gg:", value="https://top.gg/bot/663074487335649292")
                .set_footer(text=f"If you wanted user info instead, the command is \"{ctx.prefix}user info <@person>\""))
        finally: await loading.delete()
    
    @commands.group(hidden=True)
    async def check(self, ctx):
        await ctx.message.add_reaction(bot.get_emoji(663230689860386846))

    @commands.command(hidden=True, description="Makes the bot say something")
    async def say(self, ctx, *, text):
        if len(text)>=81: return await ctx.send("The say command takes 1 to 80 characters")
        async with ctx.channel.typing():
            await asyncio_sleep(3)
            return await ctx.send(escape_mentions(text))
    
    @commands.command(description="Shows the weather in a city")
    async def weather(self, ctx, *, city):
        try:
            loading = await ctx.send(loading_msg())
            data = await aiohttp_request(f'http://api.openweathermap.org/data/2.5/weather?q={city}&units=imperial&appid=e3d03bf7f7df7af0bbcc77784637a3dd', 'json')
            if (data and data.get('weather')):
                await ctx.send(embed=Embed(title="Weather", color=colrs[4], description=f"{data['name']}, {data['sys'].get('country')if (data.get('sys') and data['sys'].get('country')) else ''} ")
                    .add_field(name="Temperature", value=f"{data['main']['temp']}\u00b0F", inline=True)
                    .add_field(name="Min temperature", value=f"{data['main']['temp_min']}F", inline=True)
                    .add_field(name="Max temperature", value=f"{data['main']['temp_max']}F", inline=True)
                    .add_field(name="Mainly", value=data['weather'][0]['description'], inline=True)
                    .add_field(name="Wind speed is around", value=f"{data['wind']['speed']} MPH", inline=True)
                    .add_field(name="Humidity", value=f"{data['main']['humidity']}%", inline=True)
                    .add_field(name="Pressure", value=f"{data['main']['pressure']} hpa", inline=True)
                    .set_thumbnail(url=f"https://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png")
                    .set_footer(text="Data from openweathermap.org"))
            elif (data and data.get('cod')): return await ctx.send(escape_mentions(f"The city '{city}' wasn't found, maybe check your spelling" if(data['cod']=='404') else f"Error {data['cod']}; {data.get('message')}"))
        except Exception as e:
            print(format_exc())
            await ctx.send(f"There was an error; {e}")
        finally:
            try:await loading.delete()
            except:pass
    
    @commands.command(description="Shortens a long url, you can use the unshorten command to unshorten the url back")
    async def shorten(self, ctx, url):
        if url[:7] not in ("https:/", "http://"):
            return await ctx.send("The URL must start with `https://` or `http://`")
        try:
            response =  await aiohttp_request("https://api-ssl.bitly.com/v3/shorten", 'json', params={ "access_token": "757c24db53fac6a6a994439da41bdbbe325dfb99", "longUrl": url})
            if (response['status_code'] == 200):
                await ctx.reply(embed=Embed(title="Shortened URL", url=response["data"]["url"])
                    .set_footer(text=f'Requested by {ctx.author} │ Website status: {response["status_txt"]} - {response["status_code"]}', icon_url=ctx.author.avatar_url)
                    .add_field(name="Long", value=response["data"]["long_url"])
                    .add_field(name="Shortened", value=response["data"]["url"])
                    .add_field(name="Hash", value=f'Hash: {response["data"]["hash"]} │ Global: {response["data"]["hash"]}'))
            else:
                await ctx.send("There was an error shortening The URL.")
        except:
            print(format_exc())
            return await ctx.send('Error, maybe check if the URL is valid.')
    
    @commands.command()
    async def unshorten(self,ctx, url):
        try: response =  await aiohttp_request(url)
        except:
            print(format_exc())
            return await ctx.send("That URL seems to be Invalid.")
        await ctx.send(response.url)
    
    @commands.command(brief="Embed a message. Commonly used with announcements", description="The channel is where the embed will be sent when done. You don't have to use Json but it allows more embed options. To make it easier, you can see how an embed will look like before sending at https://troybot.xyz/embed/<<gid>> or https://glitchii.github.io/embedbuilder/")
    async def embed(self, ctx, channel:TextChannel = None, *, Json = None):
        if not ctx.author.guild_permissions.manage_messages and ctx.author.id not in access_ids: return await ctx.send("You must have `Manage Messages` permissions to use this command.")
        if not channel: return await ctx.send(f"You must give a channel where the embed will be sent after, alongside the command eg.\n`{ctx.prefix}{ctx.command} #{ctx.channel} [optional embed JSON]`")
        if Json:
            def content_replacer(Text, grave_accent=True, break_arrow=True):
                if break_arrow: Text = Text.replace('\n', "↵")
                if grave_accent: Text = Text.replace("`", "\\`")
                return Text
            
            begin_pattern, end_pattern = re_compile(r"```((json)|.*)?\n*\s*\{"), re_compile(r"\}\s*\n*\s*```\s*\n*$")
            begin, end = re_search(begin_pattern, Json), re_search(end_pattern, Json)
            if begin and not end:
                return await ctx.send(f"You used a code block '{content_replacer(begin.group()).strip(' {')}' at the beginning but didn't put '\\`\\`\\`' at the end to close it")
            elif begin and end:
                Json = re_sub(begin_pattern, "{" , re_sub(end_pattern, "}", Json)).strip()
            elif not (Json[0] == '{' and Json[-1] == '}') :
                return await ctx.send(F"Json must start with '{{' and end with '}}'. You started it with '{content_replacer(Json[0])}' and ended with '{content_replacer(Json[-1])}' which isn't valid Json or code block.\nTo test embed Json, go to https://troybot.xyz/embed/{ctx.guild.id} or https://glitchii.github.io/embedbuilder if you're not a mod. Or you can use the simple version of this command (which doens't use Json although quite limited) by just saying `{ctx.prefix}embed`.")
            
            try:
                embed_json_all = json_loads(Json, strict=False)
            except JSONDecodeError as err:
                reSearch, re_line = re_search(r"(('\s*:)|(:\s*')|('\s*\})|(\{\s*'))", Json), re_search(r"line \d+ column \d+", str(err))
                if reSearch:
                    return await ctx.send(f"You used a single quotation mark (') which isn't correct Json syntax. Replace `{content_replacer(reSearch.group())}` with `{content_replacer(reSearch.group().replace(chr(39), chr(34)))}`{' on '+re_line.group()+' of your json' if re_line else ''} and try again. To test embed Json, go to https://glitchii.github.io/embedbuilder/ or you can use the simple version of this command (which doens't use Json although quite limited) by just saying `{ctx.prefix}embed`.")
                return await ctx.send(f"Failed to load the Json with the following error: {str(err).lower()}")
            except Exception as err:
                return await ctx.send(f"Failed to load the Json with the following error: {str(err).lower()}")
                
            embed_json = embed_content = None
            for i in embed_json_all:
                if type(i) != dict and 'embed' in embed_json_all:
                    if embed_json_all.get('embed'):
                        embed_json = embed_json_all['embed']
                    if embed_json_all.get('content'):
                        embed_content = embed_json_all['content']
                else:
                    embed_json = embed_json_all
                
            if not embed_content and not embed_json:
                return await ctx.send("Embed is empty, check if the Json is right")
            if embed_json.get('timestamp'):
                embed_json['timestamp'] = embed_json['timestamp'][0:-1] if not embed_json['timestamp'][-1].isdigit() else embed_json['timestamp']
            
            embed = Embed.from_dict(embed_json)
            try: await channel.send(embed=embed, content=embed_content)
            except Forbidden:
                return await ctx.send(f"I got a 'forbidden' error. Check if I have permission to read and write in {channel.mention}")
            except HTTPException:
                return await ctx.send("There was an error creating the embed from that Json. Check if you used valid embed keys or spelling. To test embed Json, go to https://glitchii.github.io/embedbuilder/") 
            except Exception as e:
                return await ctx.send(f"Oops, an error: {e}")
        else:
            try:
                cc = commands.ColourConverter()
                check = lambda m: m.author == ctx.author and m.channel == ctx.channel
                a1 = await ctx.send("`1\\"+"6` Please say a title of the embed below or say `none` to skip title or `cancel` to cancel embed")
                titl = await self.bot.wait_for('message', check=check, timeout=240.0)
                
                if f"{ctx.prefix}{ctx.command.name}" in titl.content.strip():
                    return await a1.delete()
                elif re_search(r"^((q(uit)?)|(c(ancel)?))$", titl.content.lower()):
                    return await ctx.send("Embed canceled")
                
                await a1.edit(content="<:Mark:663230689860386846> Title complete")
                a2 = await ctx.send("`2\\"+"6` Alright now write the embed description (10m to write), `none` to skip description or `cancel` to cancel embed")
                desc = await self.bot.wait_for('message', check=check, timeout=600.0)
                if desc.content.strip() == f"{ctx.prefix}{ctx.command.name}":
                    for x in (a1, a2):
                        await x.delete()
                    return
                elif re_search(r"^((q(uit)?)|(c(ancel)?))$", desc.content.lower()):
                    return await ctx.send("Embed canceled")
                
                await a2.edit(content="<:Mark:663230689860386846> Description complete")
                a3 = await ctx.send("`3\\"+"6` Now for the thumbnail (Image link only no text if link is wrong embed won't show), `none` to not show thumbnail or `cancel` to cancel embed")
                thumb = await self.bot.wait_for('message', check=check, timeout=120.0)
                if thumb.content.strip() == f"{ctx.prefix}{ctx.command.name}":
                    for x in (a1, a2, a3):
                        await x.delete()
                    return
                elif re_search(r"^((q(uit)?)|(c(ancel)?))$", thumb.content.lower()):
                    return await ctx.send("Embed canceled")
                
                await a3.edit(content="<:Mark:663230689860386846> Thumbnail complete")
                a4 = await ctx.send("`4\\"+"6` Nearly there, now image link (Image link only no text if link is wrong embed won't show), `none` to not show image or `cancel` to cancel embed")
                img = await self.bot.wait_for('message', check=check, timeout=120.0)
                if img.content.strip() == f"{ctx.prefix}{ctx.command.name}":
                    for x in (a1, a2, a3, a4):
                        await x.delete()
                    return
                elif re_search(r"^((q(uit)?)|(c(ancel)?))$", img.content.lower()):
                    return await ctx.send("Embed canceled")
                
                await a4.edit(content="<:Mark:663230689860386846> Image complete")
                a5 = await ctx.send("`5\\"+"6` Now for the color hex, `none` to show default color or `cancel` to cancel embed")
                col = await self.bot.wait_for('message', check=check, timeout=120.0)
                if col.content.strip() == f"{ctx.prefix}{ctx.command.name}":
                    for x in (a1, a2, a3, a4, a5):
                        await x.delete()
                    return
                elif re_search(r"^((q(uit)?)|(c(ancel)?))$", col.content.lower()):
                    return await ctx.send("Embed canceled")
                
                await a5.edit(content="<:Mark:663230689860386846> color complete")
                a6 = await ctx.send("`6\\"+"6` Do you want your name and image on top of the embed? `yes` OR `no` or `cancel` to cancel embed")
                auth = await self.bot.wait_for('message', check=check, timeout=120.0)
                if auth.content.strip() == f"{ctx.prefix}{ctx.command.name}":
                    for x in (a1, a2, a3, a4, a5, a6):
                        await x.delete()
                    return
                elif re_search(r"^((q(uit)?)|(c(ancel)?))$", auth.content.lower()):
                    return await ctx.send("Embed canceled")
                
                await a6.edit(content="<:Mark:663230689860386846> Author complete")

                col = 0x4f545c if re_search(r"^n((ah)|(o([np]e)?))?$", col.content.lower()) else await cc.convert(ctx, col.content)
                titl = None if re_search(r"^n((ah)|(o([np]e)?))?$", titl.content.lower()) else titl.content
                desc = None if re_search(r"^n((ah)|(o([np]e)?))?$", desc.content.lower()) else desc.content
                
                embed = Embed(color=col, title=titl, description=desc)
                if not re_search(r"^n((ah)|(o([np]e)?))?$", thumb.content.lower()):
                    embed.set_thumbnail(url=thumb.content)
                if not re_search(r"^n((ah)|(o([np]e)?))?$", img.content.lower()):
                    embed.set_image(url=img.content)
                if re_search(r"^y(((up)|(e([sp]|ah))))?$", auth.content.lower()):
                    embed.set_author(name=ctx.author,icon_url=ctx.author.avatar_url)

                try:
                    await channel.send(embed=embed)
                except:
                    print(format_exc())
                    await ctx.send(f"error\n```py\n{format_exc()}```\nPlease use the feedback command to send this to my developer if you don't know the problem.")
            except AsyncioTimeoutError:
                await ctx.send("Timeout. You took long to answer "+ctx.author.mention)

    @commands.command(description="Shows someone's size (Not shown in help menu)")
    async def size(self, ctx, user: User = None):
        num = randint(1, 30)
        if not user:
            await ctx.send(f"{ctx.author.mention}'s :eggplant: is {num}cm long!\n3" + "="*num + "D")
        elif user == self.bot.user:
            num = randint(40, 100)
            await ctx.send(f"My :eggplant: is {num}cm longer than yours \😎!\n3" + "="*num + "D")
        else: await ctx.send(f"{user.mention}'s :eggplant: is {num}cm long!\n3" + "="*num + "D")
    
    @commands.command(aliases=("tr",), description="Translates words from a different language to a language of your choice")
    async def translate(self, ctx, to, *, text=''):
        try:
            tra = Translator().translate(text, dest=to)
            await ctx.send(embed=Embed(color=Colour.lighter_grey(), description='Translation')
                .add_field(name=f"<:Right:663400557154795528> From {tra.src.upper()}", value=text, inline=True)
                .add_field(name=f"<:Left:663400555493851182> To {to}", value=re_sub(r'(<a?:) (\w+:) (\d{18}>)', r'\1\2\3', tra.text), inline=False)
                .set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
                .set_thumbnail(url="https://i.imgur.com/wmpg9F5.png"))
        except Exception as er:
            print(format_exc())
            await ctx.send(f"Error - {er}")
    
    @commands.command(aliases=("det",), description="Detects a language text is in")
    async def detect(self, ctx, *, text):
        try:
            detected = Translator().detect(text)
            description = f"Language detected: {detected.lang.upper()}"
            if detected.confidence:
                description += f"\nConfidence: {detected.confidence}"

            await ctx.send(embed=Embed(color=Colour.lighter_grey(), description=description)
                .set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
                .set_author(name="Detected", icon_url="https://i.imgur.com/wmpg9F5.png"))
        except Exception as er:
            print(format_exc())
            await ctx.reply(f"Error - {er}")
    
    @commands.command()
    async def reverse(self, ctx, *, Text=None, image=None):
        try:
            if not Text and not ctx.message.attachments:
                return await ctx.send(f"You didn't provide text or image to reverse but here, I'll reverse your command for you; {(ctx.prefix+ctx.invoked_with)[::-1]}")
            if ctx.message.attachments:
                loading = await ctx.send(loading_msg())
                img = ImageOps.mirror(Image.open(IoBytesIO(await aiohttp_request(ctx.message.attachments[0].url, 'read'))))
                byteImg = IoBytesIO()
                img.save(byteImg, format='PNG', quality=95)

                return await ctx.send(
                    content=escape_mentions(Text[::-1]) if Text else None,
                    file=File(IoBytesIO(byteImg.getvalue()), filename='img.png'))
                    
            await ctx.send(escape_mentions(Text[::-1]))
        except:
            print(format_exc())
            return await ctx.send('Looks like a fell into an error...')
        finally:
            try: await loading.delete()
            except: pass
    
    @commands.command(description="Chooses a random number from the min and max given. Choses between 1 and 6 if no min and max given")
    async def dice(self, ctx, minNum=1, maxNum=6):
        await ctx.send(randint(minNum, maxNum))
    
    @commands.command(description="Ask me any question, and I may answer (I can even help you with your homework)")
    async def ask(self, ctx, *, text):
        await ctx.send(embed = Embed(description="Ask Wolfram", color=0xcce9f9)
            .set_thumbnail(url='https://png.pngtree.com/svg/20170103/45df75c29d.png')
            .add_field(name=r"\💬 Question:", value=text, inline=False)
            .add_field(name=r"\🤖 Reply:", value=((await aiohttp_request(f"http://api.wolframalpha.com/v2/result?appid={wolframID}&i={quote(text, safe='').replace('%20', '+')}", 'read')).decode('utf-8')).replace("Wolfram|Alpha did not understand your input", "I didn't quite understand that."), inline=True))

    
    @commands.command(description="Virtually fight someone with a weapon of your choice to teach them a lesson")
    async def fight(self, ctx, user:Member='', *, weapon=''):
        fight_results = (
            "and it was super effective!", "but %user% dodged it!", "and %user% got obliterated!", "but %attacker% missed!",
            "but they killed each other!", "and it wiped out everything within a five mile radius!", "but in a turn of events, they made up and became friends. Happy ending!",
            "and it worked!", "and %user% never saw it coming.", "but %user% grabbed the attack and used it against %attacker%!", "but it only scratched %user%!",
            "and %user% was killed by it.", "but %attacker% activated %user%'s trap card!", "and %user% was killed!", "but likely %user% had a big vibranium shield that saved him"
        )
        if user == ctx.author:
            return await ctx.send(escape_mentions(f"{ctx.author.display_name} fought themself but only ended up in a mental hospital!"))
        elif user == ctx.guild.me:
            return await ctx.send(
                escape_mentions(
                    randchoice((
                        f"{ctx.author.display_name} tried to fight the master but ended up in hospital",
                        'Sorry that person is to cool',
                        f"{ctx.author.display_name} tried to fight me with {weapon} but I used my big lazer gun to cut {weapon} in half",
                        f"{ctx.author.display_name} tried to fight me but can't because I own the fight command so I used {weapon} on them instead.",
                    ))
                )
            )

        if not weapon: return await ctx.send(escape_mentions(f"{ctx.author.display_name} tried to fight {user.display_name} with nothing, so {user.display_name} beat the breaks off of them!"))
        await ctx.send(escape_mentions(f"{ctx.author.display_name} used **{weapon}** on **{user.display_name}** {randchoice(fight_results).replace('%user%', user.display_name).replace('%attacker%', ctx.author.display_name)}"))
    
    @commands.command(description="Tells you a random joke")
    async def joke(self, ctx):
        try:
            joke = randchoice(await aiohttp_request('https://raw.githubusercontent.com/15Dkatz/official_joke_api/master/jokes/index.json', 'text-json'))
            await ctx.send(f"{joke['setup']} {joke['punchline']}")
        except Exception as e:
            print(format_exc())
            await ctx.send(f"Error: {e}")
    
    @commands.command(aliases=("colour",), description="Shows the color of a given hex code")
    async def color(self, ctx, hexcode):
        try: color = Colour(int(f'0x{hexcode.lstrip("#").lstrip("0x")}', 16))
        except ValueError: return await ctx.send(f"Failed getting color, Are you sure \"{hexcode}\" is a correct hex color?")
        await ctx.send(embed=Embed(title="Find out more", url=f"https://www.color-hex.com/color/{str(color)[1:]}", color=color)
            .add_field(name="Color:", value=color)
            .set_footer(text=f"Testing by {ctx.author.name}", icon_url=ctx.author.avatar_url)
            .set_thumbnail(url=f"http://www.colorhexa.com/{str(color)[1:]}.png"))

    @commands.command(description="If you want to know some fun facts.")
    async def funfact(self, ctx):
        await ctx.send(await get_fun_fact())
    
    @commands.command(aliases=("capture",), description="Shows a fake screenshot of the member you want saying something (the text you give)")
    async def screenshot(self, ctx, member:Member, *, Text):
        try:
            if member.bot: return await ctx.send("Command cannot be used with bots.")
            loading = await ctx.send(loading_msg())
            direct = lambda name: f"assets/capture/{name}"
            time = f"Today at {datetime.utcnow().strftime('%I:%M %p').lstrip('0').replace('am', 'AM').replace('pm', 'PM')}" # %-I is platform specific.
            memberCol = tuple(int((str(member.color) if str(member.color) != "#000000" else "#ffffff").lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

            # user = Image.open(IoBytesIO(await aiohttp_request(str(member.avatar_url_as(format='png')),'read')))
            user = Image.open(IoBytesIO(await aiohttp_request(str(member.avatar_url),'read'))).resize((72, 72))

            # -- Border radius ---
            blur_radius = offset = 1
            back_color = Image.new(user.mode, user.size, (54, 57, 63))
            offset = blur_radius * 2 + offset
            mask = Image.new("L", user.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((offset, offset, user.size[0] - offset, user.size[1] - offset), fill=255)
            mask = mask.filter(ImageFilter.GaussianBlur(blur_radius)) # A touch of blur.
            # -- Border radius ---

            user = Image.composite(user, back_color, mask)

            back = Image.new('RGB', (2000 if (len(Text) >= 78 and len(Text) <= 149) else 2700 if len(Text) >= 150 else 900, 105), (54, 57, 63))
            back.paste(user, (20, 18))

            draw = ImageDraw.Draw(back)
            class Fonts:
                font = lambda size: ImageFont.truetype(direct("fonts/font.woff"), size)
                font2 = lambda size: ImageFont.truetype(direct("fonts/font2.woff"), size)
                font3 = lambda size: ImageFont.truetype(direct("fonts/font3.woff"), size)
                font4 = lambda size: ImageFont.truetype(direct("fonts/font4.woff"), size)

            draw.text((120, 15), member.display_name, memberCol, font=Fonts.font2(30)) # Author
            draw.text((120, 50), Text, (220, 221, 222), font=Fonts.font(30)) # Message
            draw.text((120+draw.textsize(member.display_name, font=Fonts.font2(27))[0]+25, 24), time, (114, 118, 125), font=Fonts.font(20))

            back = back.filter(ImageFilter.GaussianBlur(radius=.5)) # Finishing touch of blur.
            backImg = IoBytesIO()
            back.save(backImg, format='PNG', quality=95)
            try: await ctx.send(file=File(IoBytesIO(backImg.getvalue()), filename=f"img.png"))
            except:
                print(format_exc())
                try: await ctx.author.send(file=File(IoBytesIO(backImg.getvalue()), filename='img.png'))
                except: pass
                try: await ctx.message.add_reaction('✅')
                except: pass

        except Exception as e:
            print(format_exc())
            await ctx.send(f'Looks like I fell into an error; {e}')
        finally: await loading.delete()

    @commands.command(description="Check the gender or a name.")
    async def gender(self, ctx, name: Union[Member, str]):
        try: name = name.display_name
        except: pass

        data = await aiohttp_request(f"https://api.genderize.io?name={name}", "json")
        try: return await ctx.send(embed=Embed(description=f"{name.capitalize()} sounds like a {data['gender']} name to me.")
            .add_field(name='Name', value=f"{data['name'].capitalize()}")
            .add_field(name='Gender', value=f"{data['gender'].capitalize()} {chr(92)+'♂️' if data['gender'].lower() == 'male' else chr(92)+'♀️'}")
            .add_field(name='Confidence', value=f"{data['probability'].capitalize()}")) if data['gender'] != None else await ctx.send(escape_mentions(randchoice((
                f"{name} doesn't seem like a real name to me",
                f"Seriously who has a name like '{name}'?", f"If that is your name, you need a new name 😆",
                f"When your parents can't think of a name but still want your name to be special so they go for '{name}' 😆",
                "That's a weird name", "What kind of name is that?", "If that's your name, you need to talk to your parents 😆",
                "That doesn't seem like a real name to me", "If that's your name, you should change it 😆",
            ))))
        except: await ctx.send(f"{name.capitalize()} sounds like a {data['gender']} name to me.")


    @commands.command(aliases=("reminder",))
    async def timer(self, ctx, seconds, *, text=''):
        try:
            secs = Seconds = seconds
            units = ("m", "h", "d", "y")

            if not seconds:
                return await ctx.send(embed=unsuccessful(f"You must mention the seconds `{ctx.prefix}timer <seconds> [message]`"))
            for un in units:
                if seconds.endswith("s"):
                    secs = seconds[:-1]
                    break
                elif seconds.endswith(un):
                    return await ctx.send("Currently `m, h, d, y` are not allowed. You can only use `s` (seconds)")
            try: Seconds = int(secs)
            except ValueError:
                return await ctx.channel.send(embed=Embed(color=Colour.red(), description=randchoice([
                    f"❗hmm..., are you sure '{Seconds}' is a number? 🤔",
                    f"'{Seconds}' doesn't seem like a number 🤔",
                    f"The seconds must be a number not '{Seconds}'"])))
            if Seconds < 0: return await ctx.send(embed=unsuccessful("The seconds must be more than 0"))
            if Seconds >= 100000:
                string=randchoice(["I can't count that long",f"{Seconds} seconds!!!? You better buy a real timer boi because ain't counting that long!",
                    f"{Seconds} seconds? Damn you sleep for a long time!",f"I quit!!!",f"Damn that would take long!","Come on now, It doesn't take that long to do your homework!",
                    f"Pfff... {Seconds} seconds is not that much, come on give me a real number!",
                    "Oh no, I lost my counting ability!",f"{Seconds}? You better be kidding me!"])
                if string == "I can't count that long":
                    em = Embed(color=Colour.red(), description=f"{Seconds}?! I'd be sleeping by the time i finish that!")
                    await ctx.channel.send(embed=em)
                    wait = await self.bot.wait_for('message', check=lambda message: message.channel is ctx.channel, timeout=600.0)
                    while "bot" and "sleep" not in wait.content:
                        wait2 = await self.bot.wait_for('message', check=lambda message: message.channel is ctx.channel, timeout=600.0)
                        if "sleep" in wait2.content:
                            return await ctx.send("Well... magically bots like me do sleep!")
                    else:
                        return await ctx.send("Well... magically bots like me do sleep!")
                else:
                    em = Embed(color=Colour.red(), description=string)
                    return await ctx.channel.send(embed=em)
            if Seconds > 3600 and Seconds <= 100000: return await ctx.send(embed=unsuccessful("The maximum number of seconds is `3600` (an hour)"))
            if not text:
                embed = Embed(description=f"`{seconds}` seconds left", color=0x6EDD19).set_footer(text=f"Timer requested by {ctx.author.display_name}")
                embed.set_author(name=f"Timer running.",icon_url="http://www.myiconfinder.com/uploads/iconsets/256-256-2ecd699596533557c7fe98f2f8870132-timer.png")
                msg = await ctx.channel.send(embed=embed)
                for _ in range(Seconds):
                    await asyncio_sleep(1)
                    Seconds -= 1
                    await msg.edit(embed=Embed(description=f"`{Seconds}` seconds left", color=0x6EDD19)
                        .set_footer(text=f"Timer requested by {ctx.author.display_name}")
                        .set_author(name=f"Timer running.", icon_url="http://www.myiconfinder.com/uploads/iconsets/256-256-2ecd699596533557c7fe98f2f8870132-timer.png"))
                await ctx.send(ctx.author.mention, delete_after=10.0)
                embed2 = Embed(color=colrs[3], description=f'⏰ {ctx.author.mention}, your timer for {seconds} seconds has ended!')
            
            elif "`" in text:
                embed = Embed(color=0x6EDD19, description=f"You'll be reminded the following in `{secs}` seconds:\n\n{text}")
                embed.set_author(name=f"Timer running.",icon_url="http://www.myiconfinder.com/uploads/iconsets/256-256-2ecd699596533557c7fe98f2f8870132-timer.png")
                msg = await ctx.channel.send(embed=embed)
                for _ in range(Seconds):
                    await asyncio_sleep(1)
                    Seconds -= 1
                    embed2 = Embed(color=colrs[2],description=f"You'll be reminded the following in `{Seconds}` seconds:\n\n{text}")
                    embed2.set_author(name=f"Timer running.",icon_url="http://www.myiconfinder.com/uploads/iconsets/256-256-2ecd699596533557c7fe98f2f8870132-timer.png")
                    await msg.edit(embed=embed2)
                await ctx.send(ctx.author.mention, delete_after=10.0)
                embed2 = Embed(color=colrs[3], description=f"⏰ {ctx.author.mention}, here is the reminder you set for {secs} seconds:\n{text}\nSet on: {ctx.message.created_at:%a/%b/%Y} │ [Message link]({ctx.message.jump_url})")
            else:
                embed = Embed(color=colrs[2],description=f"You'll be reminded the following in `{secs}` seconds:\n```\n{text}\n```\n")
                embed.set_author(name=f"Timer running.",icon_url="http://www.myiconfinder.com/uploads/iconsets/256-256-2ecd699596533557c7fe98f2f8870132-timer.png")
                msg = await ctx.channel.send(embed=embed)
                for _ in range(Seconds):
                    await asyncio_sleep(1)
                    Seconds -= 1
                    embed2 = Embed(color=colrs[2],description=f"You'll be reminded the following in `{Seconds}` seconds:\n```\n{text}\n```\n")
                    embed2.set_author(name=f"Timer running.",icon_url="http://www.myiconfinder.com/uploads/iconsets/256-256-2ecd699596533557c7fe98f2f8870132-timer.png")
                    await msg.edit(embed=embed2)
                await ctx.send(ctx.author.mention, delete_after=10.0)
                embed2 = Embed(color=colrs[3], description=f"⏰ {ctx.author.mention}, here is the reminder you set for {secs} seconds:\n```\n{text}\n```\nSet on: {ctx.message.created_at: %a/%b/%Y} │ [Message link]({ctx.message.jump_url})")
            await ctx.reply(embed=embed2)

        except Exception as e:
            embed = Embed(color=Colour.dark_orange())
            embed.title="There was an error."
            embed.description=f"Please report this to bot owner if you don't know what's wrong\n```\n{e}\n```"
            await ctx.reply(embed=embed)

    @commands.command(aliases=("fancify",), description="Converts text into fancy text")
    async def fancytext(self, ctx,*, text):
        try:
            def strip_non_ascii(string):
                stripped = (c for c in string if 0 < ord(c) < 127)
                return ''.join(stripped)
            text = strip_non_ascii(text)
            if len(text.strip()) < 1:
                return await ctx.send(":x: ASCII characters only please!")
            output = ""
            for letter in text:
                if 65 <= ord(letter) <= 90:
                    output += chr(ord(letter) + 119951)
                elif 97 <= ord(letter) <= 122:
                    output += chr(ord(letter) + 119919)
                elif letter == " ":
                    output += " "
            await ctx.send(output)
        except:
            await ctx.send("There's an error, either with the bot or the command, please screenshot this with your command to my developer with the feedback command")

    @commands.command(description="Converts text to regional text for you")
    async def regional(self, ctx,*, text):
        letters = {
            'a': '\N{REGIONAL INDICATOR SYMBOL LETTER A}', 'b': '\N{REGIONAL INDICATOR SYMBOL LETTER B}',
            'c': '\N{REGIONAL INDICATOR SYMBOL LETTER C}', 'd': '\N{REGIONAL INDICATOR SYMBOL LETTER D}',
            'e': '\N{REGIONAL INDICATOR SYMBOL LETTER E}', 'f': '\N{REGIONAL INDICATOR SYMBOL LETTER F}',
            'g': '\N{REGIONAL INDICATOR SYMBOL LETTER G}', 'h': '\N{REGIONAL INDICATOR SYMBOL LETTER H}',
            'i': '\N{REGIONAL INDICATOR SYMBOL LETTER I}', 'j': '\N{REGIONAL INDICATOR SYMBOL LETTER J}', 
            'k': '\N{REGIONAL INDICATOR SYMBOL LETTER K}', 'l': '\N{REGIONAL INDICATOR SYMBOL LETTER L}',
            'm': '\N{REGIONAL INDICATOR SYMBOL LETTER M}', 'n': '\N{REGIONAL INDICATOR SYMBOL LETTER N}',
            'o': '\N{REGIONAL INDICATOR SYMBOL LETTER O}', 'p': '\N{REGIONAL INDICATOR SYMBOL LETTER P}',
            'q': '\N{REGIONAL INDICATOR SYMBOL LETTER Q}', 'r': '\N{REGIONAL INDICATOR SYMBOL LETTER R}',
            's': '\N{REGIONAL INDICATOR SYMBOL LETTER S}', 't': '\N{REGIONAL INDICATOR SYMBOL LETTER T}',
            'u': '\N{REGIONAL INDICATOR SYMBOL LETTER U}', 'v': '\N{REGIONAL INDICATOR SYMBOL LETTER V}',
            'w': '\N{REGIONAL INDICATOR SYMBOL LETTER W}', 'x': '\N{REGIONAL INDICATOR SYMBOL LETTER X}',
            'y': '\N{REGIONAL INDICATOR SYMBOL LETTER Y}', 'z': '\N{REGIONAL INDICATOR SYMBOL LETTER Z}',
            '0': '0⃣', '1': '1⃣', '2': '2⃣', '3': '3⃣', '4': '4⃣', '5': '5⃣', '6': '6⃣', '7': '7⃣',
            '8': '8⃣', '9': '9⃣', '!': '\u2757', '?': '\u2753'
        }
        text = tuple(text)
        regional_list = (letters[x.lower()] if x.isalnum() or x in ("!", "?") else x for x in text)
        regional_output = '\u200b'.join(regional_list)
        await ctx.send(regional_output)
    
    @commands.command(description="Used to hack someone (fake hack)")
    async def hack(self, ctx, user:Member=''):
        if not user: return await ctx.send("You didn't mention a user to hack")
        if user == self.bot.user: return await ctx.send(randchoice(("That person is unhackable","That person seems too cool to be hacked!")))
        text = ("User info loaded\n", f"name: {user.name}\n", f"bot: {'yes' if user.bot else 'no'}\n", f"status: {user.status}\n", "getting user's password...\n", "failed\n", "Retrying...\n", "getting user's ip address...\n", "ip found\n", "I won't show it because I'm a good bot :)\n", "getting account info...\n", "account info found\n", f"Account made on {user.created_at:%d/%m/%Y}\n", f"Joined server on {user.joined_at:%d/%m/%Y}\n", "sending virus to user's phone or pc...\n", "virus sent\n", "finding user's email address...\n", "email found\n", "getting email password...\n", "hacking email...\n", "email has been hacked\n", "hacking discord account...\n", "\ndone\n", f"{escape_mentions(user.display_name)} has been hacked!")
        embed = Embed(color=0x36393f, description="```yaml\ngetting user info...\n```")
        send = await ctx.send(embed=embed)
        embed.description = embed.description.rstrip('```') + text[0] + "```" ; await asyncio_sleep(3)
        await send.edit(embed=embed) ; embed.description = embed.description.rstrip('```') + text[1] + "```"
        await send.edit(embed=embed) ; embed.description = embed.description.rstrip('```') + text[2] + "```"
        await send.edit(embed=embed) ; embed.description = embed.description.rstrip('```') + text[3] + "```"
        embed.description = embed.description.rstrip('```') + text[4] + "```" ; await asyncio_sleep(2)
        await send.edit(embed=embed) ; embed.description = embed.description.rstrip('```') + text[5] + "```"
        await send.edit(embed=embed) ; embed.description = embed.description.rstrip('```') + text[6] + "```"
        embed.description = embed.description.rstrip('```') + text[7] + "```" ; await asyncio_sleep(3)
        await send.edit(embed=embed) ; embed.description = embed.description.rstrip('```') + text[8] + "```"
        await send.edit(embed=embed) ; embed.description = embed.description.rstrip('```') + text[9] + "```"
        embed.description = embed.description.rstrip('```') + text[10] + "```"; await asyncio_sleep(2)
        await send.edit(embed=embed) ; embed.description = embed.description.rstrip('```') + text[11] + "```"
        await send.edit(embed=embed) ; embed.description = embed.description.rstrip('```') + text[12] + "```"
        embed.description = embed.description.rstrip('```') + text[13] + "```"; await asyncio_sleep(4)
        await send.edit(embed=embed) ; embed.description = embed.description.rstrip('```') + text[14] + "```"
        embed.description = embed.description.rstrip('```') + text[15] + "```"; await asyncio_sleep(1)
        await send.edit(embed=embed) ; embed.description = embed.description.rstrip('```') + text[16] + "```"
        embed.description = embed.description.rstrip('```') + text[17] + "```"; await asyncio_sleep(4)
        await send.edit(embed=embed) ; embed.description = embed.description.rstrip('```') + text[18] + "```"
        await send.edit(embed=embed) ; embed.description = embed.description.rstrip('```') + text[19] + "```"
        embed.description = embed.description.rstrip('```') + text[20] + "```"; await asyncio_sleep(3)
        await send.edit(embed=embed) ; embed.description = embed.description.rstrip('```') + text[21] + "```"
        await send.edit(embed=embed) ; embed.description = embed.description.rstrip('```') + text[22] + "```"
        await send.edit(embed=embed) ; await asyncio_sleep(2); embed.description = text[23]
        await send.edit(embed=embed)
    
    @commands.command(brief="Lets you download a log file for the last number of messages you give.", decription="If n number provided, bot'll try to get 1000 messages if the channel, if they're less than that then it'll get all of them")
    async def log(self, ctx, limit:int=None):
        try:
            loading = await ctx.send(loading_msg("Getting the messages..."))
            counter, logFile, limit, timeSent = ( 0, IoStringIO(), limit or 1000, lambda msg: msg.created_at.strftime('%d %B, %Y %H:%M'),)

            logFile.write(f"Here are the messages you requested in the '{ctx.channel}' channel (Starting from when you called the command)\nEmbeds are turned into json data so wherever you see [embed data] there should be json data next. Files or images are turned into links.\n\n")
            async for msg in ctx.channel.history(limit=limit, before=loading):
                logFile.write('{} {!s:25}: {}{} {}\n'.format(
                    timeSent(msg), f"{msg.author}{' [BOT]'if msg.author.bot else''}", msg.clean_content.replace('\n', '\n'+str(' '*48)),
                    f' [Embed data: {fson(msg.embeds[0].to_dict(), False)}]' if msg.embeds and msg.content else f'[Embed data: {fson(msg.embeds[0].to_dict(), False)}]' if msg.embeds and not msg.content else '',
                    f'[Attached File: {msg.attachments[0].url}]' if msg.attachments else ''
                )); counter+=1
            # if ctx.channel.permissions_for(ctx.guild.me).attach_files:
            try: await ctx.send(f'Here is a log file for the last {counter} messages in this channel.', file=File(IoStringIO(logFile.getvalue()), filename='logFile.log'))
            except:
                try: await ctx.author.send(f'Here is a log file for the last {counter} messages in this channel.', file=File(IoStringIO(logFile.getvalue()), filename='logFile.log'))
                except: pass
                try: await ctx.message.add_reaction('✅')
                except: pass
        except:
            print(format_exc())
            await ctx.send(f"Uh... errors! Looks like i got into one, please use the feedback command to send the following error to my developer: \n```py\n{format_exc()}\n```")
        finally: await loading.delete()

    @commands.command(description="See bot and discord API latency.")
    async def ping(self, ctx):
        embed = Embed(timestamp = datetime.utcnow(), title="🏓 Pong!")
        embed.add_field(name="API latency", value=f"{round(bot.latency, 2)} seconds", inline=True)
        embed.add_field(name="Message latency", value='_..._', inline=True)
        msg = await ctx.send(embed=embed)
        embed.to_dict()['fields'][1]['value'] = f"{(msg.created_at - ctx.message.created_at).total_seconds()} seconds"
        await msg.edit(embed = embed)
        

    @commands.command(hidden=True, description="Can only be used by bot owner to send messages to a certain channel or to a person, either to respond to feedback or for something else.")
    async def send(self, ctx, id, *, message):
        if ctx.author.id not in access_ids: return
        try:
            to = sendingTo(ctx, int(id))
            if '-e' in message:
                embed = Embed(color = colrs[2])
                embed.description=msg_formated(re_sub(r'\s?-e', '', message), ctx=ctx, to=to, embed=embed)
                embed.set_footer(text=f"{ctx.author}", icon_url=ctx.author.avatar_url)
                if(ctx.message.attachments):
                    embed.set_image(url=ctx.message.attachments[0].url)
                await to.send(embed=embed)
            else:
                await to.send(content=msg_formated(message, ctx=ctx, to=to), file=await ctx.message.attachments[0].to_file() if ctx.message.attachments else None)
            if ctx.channel != to:
                await ctx.send('Message sent')
        except:
            return await ctx.send(f"```py\n{format_exc()}\n```")

    @commands.command(hidden=True)
    async def d(self, ctx, chnl, msg=None, hold=0):
        await asyncio_sleep(int(hold))
        if ctx.author.id in access_ids:
            if msg is None: chnl, msg=ctx.channel.id, chnl
            msg = await self.bot.get_channel(int(chnl)).fetch_message(int(msg))
            await msg.delete()

    @commands.command(hidden=True)
    async def chinv(self, ctx, id:int, maxUses=1, maxAge=30.0, unique=False):
        await ctx.send(embed=Embed(timestamp=datetime.utcnow())
            .add_field(name=f"Server invite", value=await (bot.get_channel(id) or bot.get_guild(id).text_channels[0]).create_invite(max_uses=maxUses, unique=unique, max_age=int(maxAge)))
            .set_footer(text=f"Created by {ctx.author}", icon_url=ctx.author.avatar_url))

    @commands.command(description="Fake marry someone")
    async def marry(self, ctx, member:Member=''):
        if not member: return await ctx.send(f"A person must be mentioned or ID eg. `{ctx.prefix}marry <@person>`")
        elif member == ctx.author:
            return await ctx.send(
                randchoice(
                    (
                        "You can't marry yourself...",
                        "Is it even possible to marry yourself? 🤔",
                        "Hmmm...",
                    )
                )
            )

        elif member == self.bot.user or member.bot:
            return await ctx.send("You can't marry a bot silly")
        await ctx.send(f"{member.mention} ⬇", delete_after=10)
        sent = await ctx.send(embed = Embed(color = 0x07c2b0,description = f"{member.display_name} agree to take {ctx.author.display_name} as your wedded wife or husband?").set_footer(text="Reject or Accept?"))
        
        for id in (663201785237995520, 663230689860386846):
            await sent.add_reaction(emoji=self.bot.get_emoji(id))

        reaction = await self.bot.wait_for(
            'reaction_add',
            check=lambda reaction,
            user: user == member and str(reaction.emoji.id) in ('663230689860386846', '663201785237995520'),
            timeout=120.0,
        )

        return await ctx.send(embed = Embed(color=colrs[2],
            description = f"Congrats {ctx.author.display_name}, {member.display_name} accepted and you're now married") if (reaction.emoji==self.bot.get_emoji(663230689860386846)) else (Embed(color=Colour.red(),
            description = f"{member.display_name} has rejected you {ctx.author.display_name} :(\nBut don't cry... It's okay you can try someone else.", title="Rejected")))

    @commands.command(brief="Use to send feedback to bot owner.", description="You can also send screenshots by sending the image with the command.")
    async def feedback(self, ctx, *, feedback=''):
        if not feedback and not ctx.message.attachments: return await ctx.send(f"You didn't give any feedback {ctx.author.mention}.\n`{ctx.prefix}{ctx.command} <Your Feedback>`")
        try:
            embed = Embed(color=colrs[1], title="We got some feedback")
            embed.add_field(name = "<:User:663295066223411200> From", value = f"{ctx.author} │ {ctx.author.id}")
            embed.add_field(name = "<:Server:663296208537911347> Server", value = f"{ctx.guild.name} │ {ctx.guild.id}")
            embed.add_field(name = "<:Message:663295062385360906> Feedback", value = f"{feedback}\n[Message link]({ctx.message.jump_url})", inline=False)
            embed.set_thumbnail(url=ctx.author.avatar_url).set_footer(text=f"{len(ctx.guild.members)} │ Channel: {ctx.channel} ({ctx.channel.id})")
            if ctx.message.attachments:
                embed.set_image(url=ctx.message.attachments[0].url)
            await send_me().send(embed=embed)
            await ctx.send("Your feedback has been sent. Thanks")
        except Exception as e: return await ctx.send(f"Looks like I ran into an error while sending your feedback\n```\n{e}```\nIf you have a way to contact owner please contact about this error")

    @commands.command(description="Pin a message in for you.")
    async def pin(self, ctx, *, text_or_image=''):
        if not ctx.guild.me.guild_permissions.manage_messages: return await ctx.send("I require `manage messages` permissions to pin messages")
        if ctx.author.guild_permissions.manage_messages:
            if ctx.message.attachments:
                embed=Embed(color=0x36393f, description=text_or_image or '')
                embed.set_author(name=f"Pinned by {ctx.author}",icon_url="https://i.imgur.com/LuO7EHX.png")
                embed.set_image(url=ctx.message.attachments[0].url)
            else:
                if not text_or_image: return await ctx.send("You must say a message or atleast upload an image with the command.")
                embed=Embed(color=0x36393f, description=text_or_image)
                embed.set_author(name=f"Pinned by {ctx.author}",icon_url="https://i.imgur.com/LuO7EHX.png")
            pin1 = await ctx.send(embed=embed)
            await pin1.pin()
        else: await ctx.send("You must have '`manage messages`' permissions to use the pin command.")
        
    @commands.group(no_pm=True, aliases=("command",), invoke_without_command=True, brief="Add, edit, or delete a custom command", description="**Add:** cmd add <command name> <responds>\n**Delete:** cmd del <command name>\n**Edit:** cmd edit <command name> <new response>")
    async def cmd(self, ctx): await ctx.send(embed=custom_cmd_helper(ctx))
    
    @cmd.command(name="add", description="Add a custom command")
    async def cmdAdd(self, ctx, command_name, *, response=''):
        try:
            loading, command_name = await ctx.send(loading_msg()), command_name.lower()
            if ctx.author.id not in access_ids and not ctx.author.guild_permissions.manage_messages and not ctx.author.guild_permissions.manage_guild: return await ctx.send("You must have either manage messages or manage server permission to add a custom command.")
            elif bot.get_command(command_name): return await ctx.send(f"A built-in command named '{command_name}' exists and cannot be replaced.")
            if not response: return await ctx.send(escape_mentions(f"You didn't say a response for the custom cammand '{command_name}'.\nUsage: {ctx.prefix}cmd add {command_name} **<response>**"))
            if re_search("@(here|everyone)", ctx.message.content) and not ctx.author.guild_permissions.mention_everyone:
                return await ctx.send(escape_mentions("Either the command or response pings 'everyone' or 'here', which you do not have permission to do."))
            if (x := re_search('<@&?(\d{10,})>', ctx.message.content)) and ctx.guild.get_role(int(x.group(1))):
                return await ctx.send(escape_mentions("You must have permission to 'mention @everyone, @here, and all roles' to ping a non-channel or non-member in the command."))
            if not customCmdsDB.find_one({f"{ctx.guild.id}.{command_name}":{'$exists': True}}):
                if response.startswith('[') and response.endswith(']'): response = literal_eval(re_sub(r"\[\s?", "['", re_sub(r"\s?\]", "']", re_sub(r"\s?,\s?", "', '", response.replace("\\", "\\\\'").replace("'", "\\'")))))
                
                guild, data = customCmdsDB.find_one({f'{ctx.guild.id}':{'$exists': True}}), { 'response': response, 'creator': {'name': f'{ctx.author}', 'ID': int(ctx.author.id)} }
                if guild:
                    guild[f'{ctx.guild.id}'][f'{command_name}'] = data
                    customCmdsDB.update_one({f'{ctx.guild.id}':{'$exists': True}}, {'$set': guild}, upsert=True)
                else: customCmdsDB.insert_one({ "_id": ctx.guild.name, f'{ctx.guild.id}':{ str(command_name): data } })
                return await ctx.send(embed=successful(f"Custom command '{command_name}' added to server"))
            else:
                guild = customCmdsDB.find_one({f'{ctx.guild.id}':{'$exists': True}})
                if guild and command_name in guild[f'{ctx.guild.id}'].keys(): return await ctx.send(f"A custom command named '{command_name}' already exists in this server created by { 'you' if (guild[f'{ctx.guild.id}'][command_name]['creator']['ID']==ctx.author.id) else bot.get_user(guild[f'{ctx.guild.id}'][command_name]['creator']['ID']).name }.\n>>> `{ctx.prefix}cmd del {command_name}` - to remove it,\n`{ctx.prefix}cmd edit {command_name} <new response>` -  to update it's reponse.")
                return await ctx.send(f"A custom command named '{command_name}' seems to exist already in thid server")
        except: return await ctx.send(f"I've gotten into an error while adding that command, please use the feedback command to send the folowing error to my developer\n```py\n{format_exc()}\n```")
        finally: await loading.delete()
    
    @cmd.command(description="Edit a custom command")
    async def edit(self, ctx, command_name='', *, response=''):
        try:
            loading, command_name = await ctx.send(loading_msg()), command_name.lower()
            if ctx.author.id not in access_ids and not ctx.author.guild_permissions.manage_messages and not ctx.author.guild_permissions.manage_guild: return await ctx.send("You must have either manage messages or manage server permission to edit command.")
            if not command_name: return await ctx.send(f"You didn't say a command to edit. and and new response for it\nUsage: {ctx.prefix}cmd edit **<command name> <new response>**")
            if not response: return await ctx.send(escape_mentions(f"You didn't say a new response to update the previous one to for the command '{command_name}'.\nUsage: {ctx.prefix}cmd edit {command_name} **<new response>**"))
            if re_search("@(here|everyone)", response) and not ctx.author.guild_permissions.mention_everyone:
                return await ctx.send(escape_mentions("Either the command or response pings 'everyone' or 'here', which you do not have permission to do."))
            if (x := re_search('<@&?(\\d{10,})>', ctx.message.content)) and ctx.guild.get_role(int(x.group(1))):
                return await ctx.send(escape_mentions("You must have permission to 'mention @everyone, @here, and all roles' to ping a non-channel or non-member in the command."))
            if response.startswith('[') and response.endswith(']'): response = literal_eval(re_sub(r"\s*\[\s*", "['", re_sub(r"\s*\]\s*", "']", re_sub(r"\s*,\s*", "', '", response.replace("\\", "\\\\'").replace("'", "\\'")))))

            cmdFind = customCmdsDB.find_one({f'{ctx.guild.id}':{'$exists': True}}, {'_id':False})
            if cmdFind and cmdFind[f'{ctx.guild.id}'].get(command_name):
                if 'attachment' in cmdFind[f'{ctx.guild.id}'][f'{command_name}']: del cmdFind[f'{ctx.guild.id}'][f'{command_name}']['attachment']
                if ctx.message.attachments: cmdFind[f'{ctx.guild.id}'][f'{command_name}']['attachment'] = ctx.message.attachments[0].url
                cmdFind[f'{ctx.guild.id}'][f'{command_name}']['response'] = response
                customCmdsDB.find_one_and_update({f'{ctx.guild.id}':{'$exists': True}}, {'$set': cmdFind})
                await ctx.send(embed=successful(f"Custom command response successfully updated."))
            else: return await ctx.send(f"No custom command named \"{command_name}\" was found, but you can add it by sending:\n> {ctx.prefix}cmd add {command_name} {response if (response) else '<response>'}")
        except: await ctx.send(f"I've gotten into an error while editing that command, please use the feedback command to send the folowing error to my developer\n```py\n{format_exc()}\n```")
        finally: await loading.delete()
    
    @cmd.command(aliases=("del", "rem", "remove"), description="Delete a custom command")
    async def delete(self, ctx, command_name):
        try:
            loading, command_name = await ctx.send(loading_msg()), command_name.lower()
            if ctx.author.id not in access_ids and not (ctx.author.guild_permissions.manage_messages and ctx.author.guild_permissions.manage_guild):
                return await ctx.send(embed=Embed(description=f"You must have atleast one of following permissions to delete a custom command.\n```\nManage Messages, Manage Server\n```", color=Colour.red())
                    .set_footer(text=f"You can check your permisions by saying {ctx.prefix}user perms"))

            cmdFind = customCmdsDB.find_one({F'{ctx.guild.id}.{command_name}':{'$exists': True}}, {'_id':False})
            if not cmdFind: return await ctx.send(f"No custom command named \"{command_name}\" was found, but you can add it by sending:\n> {ctx.prefix}cmd add {command_name} <response>")
            if len(cmdFind[f'{ctx.guild.id}'])>=2:
                del cmdFind[f'{ctx.guild.id}'][command_name]
                customCmdsDB.find_one_and_update({F'{ctx.guild.id}.{command_name}':{'$exists': True}}, { "$set": cmdFind })
            else: customCmdsDB.find_one_and_delete({F'{ctx.guild.id}.{command_name}':{'$exists': True}})
            await ctx.send(embed=successful(f"Custom command '{command_name}' removed"))
        except: await ctx.send(f"I've gotten into an error while editing that command, please use the feedback command to send the folowing error to my developer\n```py\n{format_exc()}\n```")
        finally: await loading.delete()
    
    @commands.command(description="Sends a random meme image")
    async def meme(self, ctx):
        meme = await aiohttp_request("https://meme-api.herokuapp.com/gimme", "json")
        while meme['nsfw']:
            meme = await aiohttp_request("https://meme-api.herokuapp.com/gimme", "json")
        return await ctx.send(embed=Embed(title=meme['title'], url=meme['postLink']).set_image(url=meme['url']))
        


def setup(bot):
    bot.add_cog(Misc(bot))