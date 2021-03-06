import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
import json
import typing
import asyncio

from .utils import checks

class modCog(commands.Cog):
    """Mod commands"""

    def __init__(self, bot):
        self.bot = bot
        self.db_conn = bot.db_conn
        self.colour = 0xff9300
        self.footer = 'Bot developed by DevilJamJar#0001\nWith a lot of help from ♿nizcomix#7532'
        self.thumb = 'https://styles.redditmedia.com/t5_3el0q/styles/communityIcon_iag4ayvh1eq41.jpg'
        self.autodeletions = {}

    @commands.Cog.listener('on_message')
    async def on_message(self, message: discord.Message):
        if message.author.id in self.autodeletions:
            await asyncio.sleep(self.autodeletions.get(message.author.id))
            try:
                await message.delete()
            except discord.NotFound:
                pass

    @commands.command()
    @checks.check_mod_or_owner()
    @commands.bot_has_permissions(manage_channels=True)
    @commands.max_concurrency(1, BucketType.channel)
    async def lockdown(self, ctx, minutes: float= 30):
        """Locks down all channels in the guild and makes them untalkable"""
        seconds = minutes * 60
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(
                send_messages=False
            )
        }
        await ctx.send(f"Are you sure you want to lock down this guild for {minutes}m? Type 'yes' or 'no'.")
        def check(m):
            return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond, try again.")
        else:
            if msg.content.lower() in ['yes', 'y',]:
                channels = []

                for channel in ctx.guild.text_channels:
                    if channel.overwrites_for(ctx.guild.default_role).read_messages != False:
                        if channel.overwrites_for(ctx.guild.default_role).send_messages != False:
                            await channel.edit(overwrites=overwrites)
                            channels.append(channel)

                await ctx.send(f'Alright, I removed everyone\'s perms for the next {minutes}m.')
                await asyncio.sleep(seconds)
                overwrites_revert = {
                    ctx.guild.default_role: discord.PermissionOverwrite(
                        send_messages=True
                    )
                }
                for channel in channels:
                    await channel.edit(overwrites=overwrites_revert)
                return await ctx.send(f'{ctx.author.mention}, this guild is no longer in lockdown.')
            elif msg.content.lower() in ['no', 'n']:
                return await ctx.send('Alright, lockdown sequence cancelled.')
            else:
                return await ctx.send('That\'s not a valid option, try again.')

    @commands.command()
    @checks.check_mod_or_owner()
    async def autodelete(self, ctx, member: discord.Member, *, delay: int = 120):
        """Requires manage messages permissions. Autodeletes messages sent by a specified user after a specific delay in seconds. The default is 120, or 2 minutes. Also, keep in mind that autodeleted member reset every time the bot restarts. Use unautodelete to stop autodeleting user messages."""
        self.autodeletions[member.id] = delay
        await ctx.send(f'{ctx.author.mention}, I added {member} to my autodeletions list. Use {ctx.prefix}help autodelete to see the consequences of this. This message may be sent twice, it is nothing to worry about, please ignore it.')

    @commands.command()
    @checks.check_mod_or_owner()
    async def unautodelete(self, ctx, member:discord.Member):
        """Requires manage messages permissions. Removes someone from the autodeletion register."""
        try:
            self.autodeletions.pop(member.id)
        except:
            return await ctx.send(f'{member} not found in user list of autodeletions.')
        await ctx.send(f'Done, {member} removed from register.')

    @commands.command()
    @checks.check_mod_or_owner()
    async def ban(self, ctx, member:typing.Union[discord.Member, int], *, reason:str='None Provided'):
        """Bans a member"""
        if not member:
            return await ctx.send('`Member` is a required argument that is missing.')
        if type(member) == int:
            member = self.bot.get_user(member) or await self.bot.fetch_user(member)
        else:
            if member.top_role > ctx.guild.me.top_role:
                return await ctx.send('I am not permitted to `ban` this member.')
        if not ctx.guild.permissions_for(ctx.guild.me).ban_members:
            return await ctx.send('I am not permitted to `ban` in this guild.')
        embed = discord.Embed(title=f'You have been banned from {ctx.guild.name}', colour=self.colour,
                              description=f'By:\n`{ctx.author.name}`\nBecause:\n`{reason}`')
        try:
            await member.send(embed=embed)
        except:
            await ctx.send(f'Attempt to `message` {member.mention} failed.')
        await ctx.guild.ban(user=member, reason=reason)
        await ctx.send(f'Successfully `banned` {member.mention} from the guild.')

    @commands.command(aliases=['yeet'])
    @checks.check_mod_or_owner()
    async def kick(self, ctx, member:discord.Member=None, *, reason:str='None Provided'):
        """Kicks a member"""
        if not member:
            return await ctx.send('`Member` is a required argument that is missing.')
        if member.top_role > ctx.guild.me.top_role:
            return await ctx.send('I am not permitted to `kick` this member.')
        if not ctx.guild.permissions_for(ctx.guild.me).kick_members:
            return await ctx.send('I am not permitted to `kick` in this guild.')
        embed = discord.Embed(title=f'You have been kicked from {ctx.guild.name}', colour=self.colour,
                              description=f'By:\n`{ctx.author.name}`\nBecause:\n`{reason}`')
        try:
            await member.send(embed=embed)
        except:
            await ctx.send(f'Attempt to `message` {member.mention} failed.')
        await member.kick(reason=reason)
        await ctx.send(f'Successfully `kicked` {member.mention} from the guild.')

    @commands.command(aliases=['ud'])
    @checks.check_mod_or_owner()
    async def snipe(self, ctx):
        """Returns last deleted message in this channel"""
        with open('deleted.json', 'r') as f:
            deleted = json.load(f)
        try:
            a = deleted[str(ctx.channel.id)]
            a = a
        except:
            raise commands.BadArgument('This channel has no stored deletions!')
        embed = discord.Embed(
            title = f'Last deleted message in #{ctx.channel.name}',
            colour = self.colour,
            description = f'**Author:**\n{deleted[str(ctx.channel.id)]["author"]}\n**Message:**\n{deleted[str(ctx.channel.id)]["message"]}\n**Created At:**\n{deleted[str(ctx.channel.id)]["created"]}'
        )
        embed.set_author(name=f'Requested by {ctx.author}', icon_url=ctx.message.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=['devclean', 'botpurge'])
    @checks.check_mod_or_owner()
    async def dev_clean(self, ctx, limit: int = 50):
        """
        Cleans up the bots messages.
        """

        prefix = ctx.prefix

        async with ctx.typing():

            if ctx.channel.permissions_for(ctx.me).manage_messages:
                messages = await ctx.channel.purge(check=lambda m: m.author == ctx.me or m.content.startswith(prefix),
                                                bulk=True, limit=limit)
            else:
                messages = await ctx.channel.purge(check=lambda m: m.author == ctx.me, bulk=False, limit=limit)

            return await ctx.send(f'I found and deleted `{len(messages)}` of my '
                                f'message(s) out of the last `{limit}` message(s).', delete_after=3)

def setup(bot):
    bot.add_cog(modCog(bot))
