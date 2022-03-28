from discord.utils import escape_mentions
from imports import hangmanDB, position_number
from discord import Embed
from discord.ext.commands import command, Cog, group, CommandInvokeError
from re import compile as re_compile
from random import choice as randchoice, randint
from asyncio import TimeoutError as AsyncioTimeoutError
from datetime import datetime
from traceback import format_exc
from difflib import get_close_matches

class Games(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.playing_hangman, self.playing_guess = [], []

    @Cog.listener()
    async def on_ready(self):
        print("Module: Games loaded")

    @command()
    async def rps(self, ctx, choice):
        botchoice, chosen = randchoice(('rock', 'paper', 'scissors')), get_close_matches(choice.lower(), ("rock", "r", "paper", "p", "scissors", "s"))
        
        if chosen:
            chosen = 'rock' if chosen[0] == 'r' else 'paper' if chosen[0] == 'p' else 'scissors' if chosen[0] == 's' else chosen[0]
            return await ctx.send(
                f"You win! You chose {chosen} and I chose {botchoice}"
                    if botchoice == 'rock'
                    and chosen == 'paper'
                    or botchoice == 'paper'
                    and chosen == 'scissors'
                    or botchoice == 'scissors'
                    and chosen == 'rock'
                else f"It's a draw. We both chose {botchoice}"
                if botchoice == 'rock'
                    and chosen == 'rock'
                    or botchoice == 'paper'
                    and chosen == 'paper'
                    or botchoice == 'scissors'
                    and chosen == 'scissors'
                else f"You lose. You chose {chosen} and I chose {botchoice}"
            )

        await ctx.send(escape_mentions(f"Your choice '{choice}' is not right, you must choose from rock, paper, and scissors or just r, p and s"))


    @command(name='8ball', description="Ask a yes or no question and the magical 8ball will answere.")
    async def ball8(self, ctx, *, question=''):
        if not question: return await ctx.send(f"You need to ask a yes or no question alongside the command, eg. `{ctx.prefix}8ball is this a question?`")
        reply = randchoice(
            (
                ":8ball: Definately................................not",
                ':8ball: Possibly',
                ':8ball: Too hard to tell',
                ':8ball: As I see it, yes',
                ':8ball: Yes',
                ':8ball: No',
                ':8ball: Nope',
                ':8ball: Figure it out yourself',
                ':8ball: As i see it, no',
                ":8ball: I'm not responding",
                ":8ball: My sources say no",
                ":8ball: I would say yes, but no",
                ":8ball: I'm pretty sure that's a no",
                ":8ball: It doesn't look likely",
                ":8ball: looks likely",
                ":8ball: Hell NO!",
                ":8ball: Hell YES",
                ":8ball: What do you think?",
                ":8ball: The answer to this is so obvious",
                ":8ball: Honestly I don't care",
                ":8ball: Think about it, is it yes or no?",
                ":8ball: Maybe",
                ":8ball: Yeah",
                ":8ball: It is certain",
                ":8ball: Without a doubt",
                ":8ball: That's true",
                ":8ball: My reply is no ",
                ":8ball: Very doubtful",
                ":8ball: Very right",
                "I don't answer easy questions",
                ":8ball: True",
                ":8ball: Negative",
                ":8ball: That's so true!",
                "Do you think?",
                ":8ball: Google it.",
                f":8ball: I don't know, maybe ask {randchoice(ctx.guild.members)}",
                "Sorry, say that again.",
            )
        )

        await (ctx.send(embed=Embed(description=f"Asked by {ctx.author}", colour=0x202225)
            .set_thumbnail(url='https://i.imgur.com/YBfinaU.gif')
            .add_field(name=":question:Question:", value=f'{question}', inline=False)
            .add_field(name="✓ Answer", value=reply, inline=True))
            if len(question) < 1024 else ctx.send(reply))


    @command()
    async def guess(self, ctx):
        if ctx.author.id in self.playing_guess: return
        attempts, nums = 3, randint(1, 10)
        try:
            await ctx.send(f"I'm thinking of a number between 1 and 10. What number do you think it is? You have {attempts} attempts (No hints, `{ctx.prefix}{ctx.command}` to end the game).")
            self.playing_guess.append(ctx.author.id)
            while True:
                num = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
                try:
                    if num.content.lower() == f'{ctx.prefix}guess'.lower(): return await ctx.send(f"Game stopped, the number was {nums}")
                    elif int(num.content) != nums:
                        attempts-=1
                        if attempts == 0: return await ctx.send(f"Out of attempts, the number was {nums}")
                        await ctx.send(f"Good try but {num.content} isn't the number. You've got {attempts} {'attempt' if attempts == 1 else 'attempts'} left!")
                    else: return await ctx.send(f"You guessed the number. It was {num.content}\n" + ("And this was your last attempt, lucky!" if attempts == 1 else f"You had {attempts} attempts left."))
                except ValueError: return await ctx.send(f"\"{num.content}\" isn't right, you can only say a number between 1 and 10. Game ended")
        except AsyncioTimeoutError: return await ctx.send(f"{ctx.author.mention} Time's up! You took long to answer, I can only wait for a minute")
        finally: ctx.author.id in self.playing_guess and self.playing_guess.remove(ctx.author.id)

    @group(invoke_without_command=True, aliases=('hm',), description="Play a hangman game.")
    async def hangman(self, ctx):
        if ctx.author.id in self.playing_hangman: return
        async def get_input(ctx, data_type):
            while True:
                try:
                    message = await self.bot.wait_for('message', check=lambda message: message.author is ctx.author and message.channel is ctx.channel, timeout=60.0)
                    message = data_type(message.content)
                    return message
                except CommandInvokeError: return await ctx.send(f"Stopping the game as there hasn't been any response from {ctx.author} in a minute.")
        try:
            async def won():
                get_data = hangmanDB.find_one({f"leaderboard": {'$exists': True}})
                if get_data:
                    if get_data["leaderboard"].get(f'{ctx.author.id}'):
                        get_data['leaderboard'][f'{ctx.author.id}']['points'] = get_data['leaderboard'][f'{ctx.author.id}']['points']+1
                        get_data['leaderboard'][f'{ctx.author.id}']['date'] = datetime.now().strftime("%d %B, %Y")
                        hangmanDB.find_one_and_update({f"leaderboard": {'$exists': True}}, {"$set": get_data})
                    else: 
                        get_data["leaderboard"][f'{ctx.author.id}'] = {"user": str(ctx.author), "points": 1, "date": datetime.now().strftime("%d %B, %Y")}
                        hangmanDB.find_one_and_update({f"leaderboard": {'$exists': True}}, {"$set": get_data}, upsert=True)
                else: hangmanDB.insert_one({f"leaderboard": { f'{ctx.author.id}': { "user": str(ctx.author), "points": 1, "date": datetime.now().strftime("%d %B, %Y")}}})
                
                data = sorted(get_data['leaderboard'].items(), key=lambda x: x[1]["points"], reverse=True)
                for index, key in enumerate(data):
                    if key[0] == f'{ctx.author.id}': return await ctx.send(embed=Embed(color=0x4aae4d, title='Success! You guessed the word:', description=f"`{hangman_word}`\nYou're {position_number(index+1)} on the leaderboard. Say `{ctx.prefix}hangman board` to see it").set_footer(text=f"It took you {12 - tries} tries{'! (what?!)'if(12 - tries<=1)else'.'} You had {tries} tries remaining.").set_thumbnail(url="https://4.bp.blogspot.com/-b1BtoF2dCes/WEjrekT0OCI/AAAAAAAEORE/75qPzUneCJISa8_2DdZdxlx-q584ebpQQCLcB/s1600/AW337697_00.gif"))
            
            with open('assets/hangman.txt', 'r') as hangman_word:
                hangman_word_hidden, hangman_word = '', randchoice(hangman_word.read().splitlines())
                for letter in hangman_word:
                    if letter != ' ': hangman_word_hidden += '*'
                    else: hangman_word_hidden += ' '
                tries = 12
                self.playing_hangman.append(ctx.author.id)
                await ctx.send(embed=Embed(title='Hangman game has started!', description=f'You have {tries} tries remaining.\nGuess the word: `{hangman_word_hidden}`').set_footer(text=f"Put a hash(#) infront of text to ignore it | '{ctx.prefix}hangman' to stop").set_thumbnail(url="https://pngimage.net/wp-content/uploads/2018/06/impiccato-png-8.png"))
                print(f"{ctx.author} is guessing a word in {ctx.guild}({ctx.guild.id}), the word is: {hangman_word}")
                while True:
                    if tries == 0:
                        get_data = hangmanDB.find_one({f"leaderboard": {'$exists': True}})
                        if get_data:
                            data = sorted(get_data['leaderboard'].items(), key=lambda x: x[1]["points"], reverse=True)
                            for index, key in enumerate(data):
                                if key[0]==f'{ctx.author.id}': return await ctx.send(embed=Embed(color=0xfa682c, title='You ran out of tries.', description=f"The word was `{hangman_word}`\nYou're {position_number(index+1)} on the leaderboard. Say `{ctx.prefix}hangman board` to see it").set_thumbnail(url="https://www.shareicon.net/data/512x512/2015/11/19/674342_man_512x512.png"))
                        return await ctx.send(embed=Embed(color=0xfa682c, title='You ran out of tries.', description=f"The word was ``{hangman_word}``\nYou're not on the leaderboard, win games to get there. Say `{ctx.prefix}hangman board` to see it").set_thumbnail(url="https://www.shareicon.net/data/512x512/2015/11/19/674342_man_512x512.png"))
                    # elif hangman_word_hidden == hangman_word: return await won()
                    guess = await get_input(ctx, str)
                    if guess.startswith('#') or (guess.startswith('.') and not guess.startswith('...')) or guess.startswith('?'): pass
                    elif guess.lower() == hangman_word.lower(): return await won()
                    else:
                        if guess.lower().startswith(f'{ctx.prefix}hangman') or guess.lower().startswith(f'{ctx.prefix}hm'): return await ctx.send(f'Hangman game ended. The word was ``{hangman_word}``')
                        cmp_guess = re_compile(guess.lower())
                        spans, matches = [], cmp_guess.finditer(hangman_word.lower())
                        for match in matches:
                            span = match.span()
                            # We only need the first points
                            spans.append(span[0])
                        if len(spans) == 0:
                            print(hangman_word_hidden)
                            await ctx.send(f"There is no letter '{guess.upper()}' in the word.\nYou have {tries} tries remaining.\n`{hangman_word_hidden}`")
                            tries -= 1
                        else:
                            for letter_pos in spans:
                                thing_str = ''
                                listed = list(hangman_word_hidden)
                                listed[letter_pos] = hangman_word[letter_pos]
                                for thing in listed:
                                    thing_str += thing
                                hangman_word_hidden = thing_str
                            await ctx.send(f"There {'are'if(len(spans)>=2)else('is')} {len(spans)} letter '{guess.upper()}'")
                            if hangman_word_hidden != hangman_word:  # If the hangman word is fully completed
                                await ctx.send(f'You have {tries} tries remaining.\n`{hangman_word_hidden}`')
        except AsyncioTimeoutError: return await ctx.send(f"Hangman game has ended as there hasn't been a response from {ctx.author} in a minute.\nThe word was `{hangman_word}`")
        except Exception as e:
            print(format_exc())
            await ctx.send(f"I fell into a little error; {e}")
        finally:
            if ctx.author.id in self.playing_hangman: self.playing_hangman.remove(ctx.author.id)
    
    @hangman.command(aliases=("board", 'l'), description="See the hangman leaderboard.")
    async def leaderboard(self, ctx):
        get_data = hangmanDB.find_one({"leaderboard":{'$exists': True}}, {'_id':False})
        if not get_data: return await ctx.send(f"Database is currently empty, quick play! `{ctx.prefix}hangman`")

        data = sorted(get_data['leaderboard'].items(), key=lambda x: x[1]["points"], reverse=True)
        embed = (Embed(title=f"Top 10 best hangman players", color=0xFFCC4D)
                 .set_footer(text=f"You're not on the leaderboard. Say '{ctx.prefix}hangman' to play")
                 .set_thumbnail(url="https://www.pngkit.com/png/full/11-114878_king-crown-clipart-no-background-free-download-king.png"))
        for index, key in enumerate(data):
            user = self.bot.get_user(int(key[0])) or key[1]['user'].title()
            if key[0] == f'{ctx.author.id}': embed.set_footer(text=f"You're {position_number(index+1)} on the leaderboard")
            if index <=  9:
                if index == 0: embed.add_field(name=f"👑\t{user} • {key[1]['points']} gam{'es' if key[1]['points']!=1 else 'e'} won", value=f"Last played: {key[1]['date']}", inline=False)
                elif index == 1: embed.add_field(name=f"🥈\t{user} • {key[1]['points']} gam{'es' if key[1]['points']!=1 else 'e'} won", value=f"Last played: {key[1]['date']}", inline=False)
                elif index == 2: embed.add_field(name=f"🥉\t{user} • {key[1]['points']} gam{'es' if key[1]['points']!=1 else 'e'} won", value=f"Last played: {key[1]['date']}", inline=False)
                else: embed.add_field(name=f"`{position_number(index+1)}` {user} • {key[1]['points']} gam{'es' if key[1]['points']!=1 else 'e'} won", value=f"Last played: {key[1]['date']}", inline=False)
            elif index+1 == len(data): embed.add_field(name=f"...\n**Last place goes to**\n`{position_number(index+1)}`\t{user} • {key[1]['points']} gam{'es' if key[1]['points']!=1 else 'e'} won", value=f"Last played: {key[1]['date']}", inline=False)
        return await ctx.send(embed=embed)
    

def setup(bot):
    bot.add_cog(Games(bot))