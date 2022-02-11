from imports import aiohttp_request, loading_msg
from youtube_dl import YoutubeDL
from discord import Embed, Color, FFmpegPCMAudio
from discord.utils import get
from traceback import format_exc
from asyncio import run_coroutine_threadsafe
from discord.ext.commands import command, Cog


class Music(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = []
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    @Cog.listener()
    async def on_ready(self):
        print("Module: Music loaded")

    def parse_duration(self, duration):
        result = []
        seconds = duration%60
        minutes = duration//60
        hour = minutes//60
        day = hour//24
        
        if day != 0: result.append(f"{day}d ")
        if hour != 0: result.append(f"{hour}h ")
        if minutes != 0: result.append(f"{minutes}m ")
        result.append(f"{seconds}s ")
        return "".join(result)
    
    async def search(self, ctx, arg):
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': False,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
        }
        try: await (aiohttp_request("".join(arg[:])))
        except:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch:{' '.join(arg[:])}", download=False)
                title = info['entries'][0]['title']
                url = info['entries'][0]['webpage_url']
                source = info['entries'][0]['formats'][0]['url']
                uploader = info['entries'][0]['uploader']
                uploader_url = info['entries'][0]['channel_url']
                duration = self.parse_duration(info['entries'][0]['duration'])
                thumbnail = info['entries'][0]['thumbnail']
                views = info['entries'][0]['view_count']
                likes = info['entries'][0]['like_count']
                dislikes = info['entries'][0]['dislike_count']
        else:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(''.join(arg[:]), download=False)
                title = info['title']
                url = info['webpage_url']
                source = info['formats'][0]['url']
                uploader = info['uploader']
                uploader_url = info['channel_url']
                duration = self.parse_duration(info['duration'])
                thumbnail = info['thumbnail']
                views = info['view_count']
                likes = info['like_count']
                dislikes = info['dislike_count']
            
        return {
            'uploader': uploader,
            'uploader_url': uploader_url,
            'views': views,
            'likes': likes,
            'dislikes': dislikes,
            'thumbnail': thumbnail,
            'duration': duration,
            'url': url,
            'source': source,
            'title': title,
            'embed': (Embed(url=url, title=title, color=Color.blue())
                        .add_field(name='Duration', value=duration, inline=True)
                        .add_field(name='Requested by', value=ctx.author.display_name, inline=True)
                        .add_field(name='Uploader', value=f'[{uploader}]({uploader_url})', inline=True)
                        .add_field(name="Views", value=f"{views:,}", inline=True)
                        .add_field(name='\\👍', value=f"{likes:,}", inline=True)
                        .add_field(name='\\👎', value=f"{dislikes:,}", inline=True)
                        .set_author(name="Now Playing:", url=url, icon_url="https://icons-for-free.com/iconfiles/png/512/composition+editor+music+playlist+songs+sound+icon-1320183046878963700.png")
                        .set_thumbnail(url=thumbnail))
        }

    @command(aliases=('p',), description='Plays the desired song')
    async def play(self, ctx, *keyword_or_ytlink):
        try:
            try: channel = ctx.author.voice.channel
            except AttributeError: return await ctx.send(f"No channel to join. Please join a channel and then try again")
            if not channel.permissions_for(ctx.guild.me).connect or not channel.permissions_for(ctx.guild.me).speak: return await ctx.send(f"I don't have permission to either connect or speak in '{channel.name}'")

            voice = get(self.bot.voice_clients, guild=ctx.guild)
            if voice and voice.is_connected(): await voice.move_to(channel)
            else: voice = await channel.connect()
            searching = await ctx.send(loading_msg('Searching best match...' if not keyword_or_ytlink[0].startswith('http') else 'Searching...'))
            def play_next(ctx):
                try: del self.song_queue[0]
                except IndexError: pass

                if len(self.song_queue) < 1: return
                voice = get(self.bot.voice_clients, guild=ctx.guild)
                voice.play(FFmpegPCMAudio(self.song_queue[0]['source'], **self.FFMPEG_OPTIONS), after=lambda: play_next(ctx))
                run_coroutine_threadsafe(ctx.send(embed=self.song_queue[0]['embed']), self.bot.loop).result()

            song = await self.search(ctx, keyword_or_ytlink)
            if not voice.is_playing():
                self.song_queue.append(song)
                voice.play(FFmpegPCMAudio(song['source'], **self.FFMPEG_OPTIONS), after=lambda: play_next(ctx))
                await ctx.send(embed=song['embed'])
                voice.is_playing()
            else:
                self.song_queue.append(song)
                await ctx.send(embed=Embed(description=f"[{song['title']}]({song['url']})", url=song['url'], color=Color.blue())
                    .add_field(name='Duration', value=song['duration'], inline=True)
                    .add_field(name='Requested by', value=ctx.author.display_name, inline=True)
                    .add_field(name='Uploader', value=f"[{song['uploader']}]({song['uploader_url']})", inline=True)
                    .add_field(name="Views", value=f"{song['views']:,}", inline=True)
                    .add_field(name='\\👍', value=f"{song['likes']:,}", inline=True)
                    .add_field(name='\\👎', value=f"{song['dislikes']:,}", inline=True)
                    .set_author(name=f"Added to queue ({len(self.song_queue)-1} to go)", url=song['url'], icon_url="https://icons-for-free.com/iconfiles/png/512/composition+editor+music+playlist+songs+sound+icon-1320183046878963700.png")
                    .set_thumbnail(url=song['thumbnail']))
        except Exception as err: await ctx.send(f"Looks like I fell into an error... {err}"); print(format_exc())
        finally: await searching.delete()

        

    @command(aliases=('q',), description="Returns the current queue")
    async def queue(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        embed = Embed(color=Color.blue(), title="Here's the current queue:")
        if voice and voice.is_playing():
            for i in self.song_queue:
                if self.song_queue.index(i) == 0: embed.add_field(name=f'💿 Currently plaing:', value=f"[{i['title']}]({i['url']}) • {i['duration']}", inline=False)
                else: embed.add_field(name=f'Track {self.song_queue.index(i)+1}:', value=f"[{i['title']}]({i['url']}) • {i['duration']}", inline=False)
            embed.set_thumbnail(url="https://icons-for-free.com/iconfiles/png/512/composition+editor+music+playlist+songs+sound+icon-1320183046878963700.png")
            await ctx.send(embed=embed)
        else: return await ctx.send("I'm not playing any song at the moment")
    
    @command(description="Returns the currently playing music if any")
    async def playing(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if not voice or not voice.is_playing(): return await ctx.send("I'm not playing any song at the moment")

        for i in self.song_queue:
            if self.song_queue.index(i) == 0:
                embed = i['embed'].to_dict()
                del embed['fields'][3:]; embed['author']['name'], embed['author']['icon_url'] = "Currently Playing", "https://media.giphy.com/media/Tey00n9z1ueS3BEhNk/giphy.gif"
                embed = Embed.from_dict(embed)
                embed.add_field(name="----------", value="**Playing next:** " + (f"[{self.song_queue[1]['title']}]({self.song_queue[1]['url']})" if len(self.song_queue) >1 else  '_Nothing added_'), inline=False)
                return await ctx.send(embed=embed)

    @command(description='Plays or resumes the current song')
    async def pause(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if not voice or not voice.is_connected(): return await ctx.send("It doest look like I'm connected to any voice channel")

        if voice.is_playing():
            try:
                voice.pause()
                return await ctx.send(f'Music paused as requested by {ctx.author}')
            except Exception as e: return await ctx.send(f"Oops, looks like I fell into an error: {e}")
        else:
            try:
                voice.resume()
                return await ctx.send(f'Music resumed as requested by {ctx.author}')
            except Exception as e: return await ctx.send(f"Oops, looks like I fell into an error: {e}")
    
    @command(description='Plays or resumes the current song')
    async def resume(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if not voice or not voice.is_connected(): return await ctx.send("It doest look like I'm connected to any voice channel")

        if voice.is_playing():
            try:
                voice.pause()
                return await ctx.send("Looks like the music was already playing, I've now paused it")
            except Exception as e: return await ctx.send("Looks like the music is already playing")
        else:
            try:
                voice.resume()
                return await ctx.send(f'Music resumed as requested by {ctx.author}')
            except Exception as e: return await ctx.send(f"Oops, looks like I fell into an error: {e}")

    @command(description='Skips the current song')
    async def skip(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_playing():
            await ctx.send(f'Music skipped as requested by {ctx.author}')
            voice.stop()
        else: await ctx.send("I'm not playing any song at the moment")

    @command(aliases=('s',), description="Disconnects the bot from a voice channel")
    async def stop(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if not voice or not voice.is_connected(): return await ctx.send("It doesn't look like I'm playing anything")

        if not ctx.author.voice:
            if not ctx.author.guild_permissions.move_members: return await ctx.send("You must join the voice channel first or have 'Move Members' permission")
            channel = voice.channel
        else: channel = ctx.author.voice.channel
        self.song_queue = []
        try:
            await voice.disconnect()
            await ctx.send(f"I've disconnected from the {channel} voice channel")
        except Exception as e:
            await ctx.send(f"Looks like I fell into some error: {e}")
            return print(e)

def setup(bot):
    bot.add_cog(Music(bot))