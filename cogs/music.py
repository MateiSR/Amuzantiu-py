import asyncio
import itertools
import re

import discord
import lavalink
from discord.ext import commands

url_rx = re.compile(r'https?://(?:www\.)?.+')


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # guild id -> text channel id
        self.preferred_channels = {}

        # This ensures the client isn't overwritten during cog reloads.
        if not hasattr(bot, 'lavalink'):
            bot.lavalink = lavalink.Client(bot.user.id)
            # Host, Port, Password, Region, Name
            # Free node
            bot.lavalink.add_node("lava.link", 80, "1234",
                                  "eu", "lava-dot-link")
            # Self-hosted node
            bot.lavalink.add_node("64.112.126.84", 2333,
                                  "ysnp123", "us", "self-hosted-1")
            bot.add_listener(bot.lavalink.voice_update_handler,
                             'on_socket_response')

        lavalink.add_event_hook(self.track_hook)

    def cog_unload(self):
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.bot.lavalink._event_hooks.clear()

    def reply_embed(self, message: str):
        """ Returns embed with no title as fancier way of replying. """
        embed = discord.Embed(color=discord.Color.blurple())
        embed.title = ""
        embed.description = message
        return embed

    def error_embed(self, message: str):
        """ Same as reply embed, but red. """
        embed = discord.Embed(color=discord.Color.red())
        embed.title = ""
        embed.description = message
        return embed

    def parse_duration(self, duration: int):
        """Parses ms to human readable format."""
        live_duration = [0, 9223372036854775807]
        if duration > 0 and duration not in live_duration:
            x = duration / 1000
            seconds = int(x % 60)
            x /= 60
            minutes = int(x % 60)
            x /= 60
            hours = int(x % 24)
            x /= 24
            days = int(x)

            duration = []
            if days > 0:
                if len(str(days)) == 1:
                    days = "0" + str(days)
                duration.append('{}'.format(days))
            if hours > 0:
                if len(str(hours)) == 1:
                    hours = "0" + str(hours)
                duration.append('{}'.format(hours))
            if minutes >= 0:
                if len(str(hours)) <= 1:
                    hours = "0" + str(hours)
                duration.append('{}'.format(minutes))
            if seconds > 0:
                if len(str(seconds)) == 1:
                    seconds = "0" + str(seconds)
                elif len(str(seconds)) == 0:
                    seconds = "00"
                duration.append('{}'.format(seconds))

            value = ':'.join(duration)

        elif duration in live_duration:
            value = "LIVE"

        return value

    def parse_duration_str(self, duration):
        """Parses human readable duration to ms."""
        try:
            dl = duration.split(":")
        except Exception:
            return None
        if len(dl) > 4:
            return None
        while len(dl) < 4:
            dl.insert(0, 0)

        ret = int(dl[0]) * 60 * 60 * 24 + int(dl[1]) * \
            60 * 60 + int(dl[2]) * 60 + int(dl[3])
        return ret * 1000

    async def cog_before_invoke(self, ctx):
        """ Command before-invoke handler. """
        guild_check = ctx.guild is not None
        #  This is essentially the same as `@commands.guild_only()`
        #  except it saves us repeating ourselves (and also a few lines).

        if guild_check:
            await self.ensure_voice(ctx)
            #  Ensure that the bot and command author share a mutual voicechannel.

        return guild_check

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(embed=self.error_embed(str(error.original)))
            # The above handles errors thrown in this cog and shows them to the user.
            # This shouldn't be a problem as the only errors thrown in this cog are from `ensure_voice`
            # which contain a reason string, such as "Join a voicechannel" etc. You can modify the above
            # if you want to do things differently.

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """ Leave voice after `timeout` seconds of inactivity """
        # This makes sure that the bot leaves
        # the voice channel after a settable timeout
        # for performance improvements.
        timeout = 600  # seconds
        if not member.id == self.bot.user.id:
            return
        elif before.channel is None:
            player = self.bot.lavalink.player_manager.get(member.guild.id)
            time = 0
            while True:
                await asyncio.sleep(1)
                time += 1

                # Check if after channel none & clear queue
                if after.channel is None:
                    player.queue.clear()
                    # Stop the current track so Lavalink consumes less resources.
                    await player.stop()
                    break

                # Timeout after `timeout` seconds for performance improvements.
                if player.is_playing:
                    time = 0
                if time == timeout:
                    ch = await self.bot.fetch_channel(
                        self.preferred_channels[str(player.guild_id)])
                    await member.guild.change_voice_state(channel=None)
                    await ch.send(embed=self.reply_embed("Left voice channel after no activity for `10 minutes`."))
                    del self.preferred_channels[str(player.guild_id)]
                if not player.is_connected:
                    break

    async def ensure_voice(self, ctx):
        """ This check ensures that the bot and command author are in the same voicechannel. """
        player = self.bot.lavalink.player_manager.create(
            ctx.guild.id, endpoint=str(ctx.guild.region))
        # Create returns a player if one exists, otherwise creates.
        # This line is important because it ensures that a player always exists for a guild.

        # Most people might consider this a waste of resources for guilds that aren't playing, but this is
        # the easiest and simplest way of ensuring players are created.

        # These are commands that require the bot to join a voicechannel (i.e. initiating playback).
        # Commands such as volume/skip etc don't require the bot to be in a voicechannel so don't need listing here.
        should_connect = ctx.command.name in ('play',)

        if not ctx.author.voice or not ctx.author.voice.channel:
            # Our cog_command_error handler catches this and sends it to the voicechannel.
            # Exceptions allow us to "short-circuit" command invocation via checks so the
            # execution state of the command goes no further.
            raise commands.CommandInvokeError(
                "You aren't connected to voice channel.")

        if not player.is_connected:
            if not should_connect:
                raise commands.CommandInvokeError('Player is not connected.')

            permissions = ctx.author.voice.channel.permissions_for(ctx.me)

            if not permissions.connect or not permissions.speak:  # Check user limit too?
                raise commands.CommandInvokeError(
                    'I need to have both `connect` and `speak` permissions.')

            player.store('channel', ctx.channel.id)
            await ctx.guild.change_voice_state(channel=ctx.author.voice.channel)
        else:
            if int(player.channel_id) != ctx.author.voice.channel.id:
                raise commands.CommandInvokeError(
                    'You need to be connected to the same voice channel.')

    async def track_hook(self, event):
        if isinstance(event, lavalink.events.QueueEndEvent):
            # When this track_hook receives a "QueueEndEvent" from lavalink.py
            # it indicates that there are no tracks left in the player's queue.
            # To save on resources, we can tell the bot to disconnect from the voicechannel.
            # M - This is now done with the usage of a cog.listener()
            pass
        elif isinstance(event, lavalink.events.TrackStartEvent):
            player = event.player
            length = player.current.extra["length"]
            fl = self.parse_duration(length)
            g = await self.bot.fetch_guild(player.guild_id)
            r = await g.fetch_member(event.track.requester)
            ch = await self.bot.fetch_channel(
                self.preferred_channels[str(player.guild_id)])
            await ch.send(embed=self.reply_embed(f"Playing [{player.current.title}](https://www.youtube.com/watch?v={player.current.identifier}) - {fl} [{r.mention}]"))

    @commands.command(aliases=['p'])
    async def play(self, ctx, *, query: str):
        """ Searches and plays a song from a given query. """
        # Get the player for this guild from cache.
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        # If player is paused - unpause, return
        if player.paused:
            return await player.set_pause(False)

        # Remove leading and trailing <>. <> may be used to suppress embedding links in Discord.
        query = query.strip('<>')

        # Check if the user input might be a URL. If it isn't, we can Lavalink do a YouTube search for it instead.
        # SoundCloud searching is possible by prefixing "scsearch:" instead.
        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        # Get the results for the query from Lavalink.
        results = await player.node.get_tracks(query)

        # Results could be None if Lavalink returns an invalid response (non-JSON/non-200 (OK)).
        # ALternatively, resullts['tracks'] could be an empty array if the query yielded no tracks.
        if not results or not results['tracks']:
            return await ctx.send(embed=self.error_embed(f"No results found for `{query}`"))

        embed = discord.Embed(color=discord.Color.blurple())

        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        if results['loadType'] == 'PLAYLIST_LOADED':
            tracks = results['tracks']

            for track in tracks:
                # Add all of the tracks from the playlist to the queue.
                length = track["info"]["length"]
                track = lavalink.models.AudioTrack(
                    track, requester=ctx.author.id, recommended=True, length=length)
                player.add(requester=ctx.author.id, track=track)

            embed.title = ''
            embed.description = f'Queued **{results["playlistInfo"]["name"]}** - {len(tracks)} tracks'
        else:
            track = results['tracks'][0]
            embed.title = ""
            embed.description = f'Queued [{track["info"]["title"]}]({track["info"]["uri"]}) [{ctx.message.author.mention}]'
            length = track["info"]["length"]

            # You can attach additional information to audiotracks through kwargs, however this involves
            # constructing the AudioTrack class yourself.
            track = lavalink.models.AudioTrack(
                track, requester=ctx.author.id, recommended=True, length=length)
            player.add(requester=ctx.author.id, track=track)

        # Save text channel in which bot command was sent
        # for further reply
        self.preferred_channels[str(ctx.guild.id)] = ctx.message.channel.id

        await ctx.send(embed=embed)

        # We don't want to call .play() if the player is playing as that will effectively skip
        # the current track.
        if not player.is_playing:
            await player.play()

    @commands.command(aliases=['n', 'next', 's'])
    async def skip(self, ctx):
        """ Skips current track, playing next track in queue, if any."""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await ctx.send(embed=self.error_embed(f'Not playing. [{ctx.message.author.mention}]'))

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await ctx.send(embed=self.error_embed(f'Not connected to the same voice channel. [{ctx.message.author.mention}]'))

        # Skips track
        await player.skip()
        # Add reaction
        await ctx.message.add_reaction("⏩")

    @commands.command()
    async def shuffle(self, ctx):
        """ Shuffles queue. """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await ctx.send(embed=self.error_embed(f'Not playing. [{ctx.message.author.mention}]'))

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await ctx.send(embed=self.error_embed(f'Not connected to the same voice channel. [{ctx.message.author.mention}]'))

        # Toggles shuffle
        player.shuffle = not player.shuffle

        # Add emote corresponding to current state
        if player.shuffle:
            await ctx.message.add_reaction("✅")
        else:
            await ctx.message.add_reaction("⛔")

    @commands.command(aliases=["v", "vol"])
    async def volume(self, ctx, volume: int = 100):
        """ Changes volume (0-1000). """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await ctx.send(embed=self.error_embed(f'Not playing. [{ctx.message.author.mention}]'))

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await ctx.send(embed=self.error_embed(f'Not connected to the same voice channel. [{ctx.message.author.mention}]'))

        # Check if value valid
        if not (volume >= 0 and volume <= 1000):
            return await ctx.send(embed=self.error_embed("Invalid value `(1-1000 required)`"))

        # Sets player volume (0-1000)
        await player.set_volume(volume)
        # Send confirmation message
        await ctx.send(embed=self.reply_embed(f"Set volume to {volume} [{ctx.message.author.mention}]"))

    @commands.command()
    async def pause(self, ctx):
        """ Pauses. """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await ctx.send(embed=self.error_embed(f'Not playing. [{ctx.message.author.mention}]'))

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await ctx.send(embed=self.error_embed(f'Not connected to the same voice channel. [{ctx.message.author.mention}]'))

        # Pause the player
        await player.set_pause(True)

        # Add emote corresponding to current state
        if player.paused:
            await ctx.message.add_reaction("⏯️")

    @commands.command(aliases=["unpause"])
    async def resume(self, ctx):
        """ Unpauses. """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await ctx.send(embed=self.error_embed(f'Not playing. [{ctx.message.author.mention}]'))

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await ctx.send(embed=self.error_embed(f'Not connected to the same voice channel. [{ctx.message.author.mention}]'))

        # Pause the player
        await player.set_pause(False)

        # Add emote corresponding to current state
        if not player.paused:
            await ctx.message.add_reaction("⏯️")

    @commands.command()
    async def loop(self, ctx):
        """ Loops queue. """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await ctx.send(embed=self.error_embed(f'Not playing. [{ctx.message.author.mention}]'))

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await ctx.send(embed=self.error_embed(f'Not connected to the same voice channel. [{ctx.message.author.mention}]'))

        # Repeat current track
        player.repeat = not player.repeat

        # Add emote corresponding to current state
        if player.repeat:
            await ctx.message.add_reaction("✅")
            await ctx.send(embed=self.reply_embed(f"**Looping** queue"))
        else:
            await ctx.message.add_reaction("⛔")
            await ctx.send(embed=self.reply_embed(f"**Stopped looping** queue"))

    @commands.command(aliases=["playing", "now"])
    async def current(self, ctx):
        """ Displays current track. """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        r = await ctx.guild.fetch_member(player.current.requester)
        position = player.position
        p = self.parse_duration(position)
        length = player.current.extra["length"]
        l = self.parse_duration(length)
        await ctx.channel.send(embed=self.reply_embed(f"Playing [{player.current.title}](https://www.youtube.com/watch?v={player.current.identifier})\n{p} / {l} [{r.mention}]"))

    @commands.command()
    async def seek(self, ctx, timestamp):
        """ Seeks timestamp in `:` divided format. """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await ctx.send(embed=self.error_embed(f'Not playing. [{ctx.message.author.mention}]'))

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await ctx.send(embed=self.error_embed(f'Not connected to the same voice channel. [{ctx.message.author.mention}]'))

        length = player.current.extra["length"]
        l = self.parse_duration(length)

        p = self.parse_duration_str(timestamp)

        if p is not None:
            if p > length:
                return await ctx.send(embed=self.error_embed(f"Cannot seek more than duration - {l}"))
            await player.seek(p)
            await ctx.message.add_reaction("✅")
        else:
            return await ctx.send(embed=self.error_embed(f"Invalid value (format - dd:hh:mm:ss)"))

    @commands.command(aliases=["q"])
    async def queue(self, ctx, page_num=1):
        """ Shows queue. """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await ctx.send(embed=self.error_embed(f'Not playing. [{ctx.message.author.mention}]'))

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await ctx.send(embed=self.error_embed(f'Not connected to the same voice channel. [{ctx.message.author.mention}]'))

        queue = player.queue
        # queue.insert(0, player.current)

        if len(queue) == 0:
            try:
                return await self.current(ctx)
            except AttributeError:
                return await ctx.send(embed=self.error_embed(f'Not playing. [{ctx.message.author.mention}]'))

        def chunks(lst=queue, n=10): return [
            lst[i:i + n] for i in range(0, len(lst), n)]

        queue_chunks = chunks()

        pages = len(queue_chunks)

        queue_return = []

        def queue_page(page_num):
            page = queue_chunks[page_num - 1]
            for song in page:
                song_index = page.index(song)
                song_length = song.extra["length"]
                song_length = self.parse_duration(song_length)
                c = f"{song_index + 1 + 10 * (page_num - 1)}) {song.title[0:40]}"
                c2 = c + (48 - len(c)) * " " + song_length
                queue_return.append(c2)
            fc = "\n".join(queue_return)
            return f"```nim\nPage {page_num}/{pages}\n{fc}```"

        await ctx.send(queue_page(page_num))

    @commands.command()
    async def remove(self, ctx, song_index: int):
        """ Removes a song from queue by id. """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await ctx.send(embed=self.error_embed(f'Not playing. [{ctx.message.author.mention}]'))

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await ctx.send(embed=self.error_embed(f'Not connected to the same voice channel. [{ctx.message.author.mention}]'))

        if song_index > len(player.queue) + 1:
            return await ctx.send(embed=self.error_embed("There is no such song in the queue."))

        await ctx.send(embed=self.reply_embed(f"Removed **{player.queue[song_index - 1].title}** from the queue"))
        player.queue.pop(song_index - 1)
        await ctx.message.add_reaction("✅")

    @commands.command(aliases=["move", "seeksong"])
    async def jump(self, ctx, song_index: int):
        """ Skips to song on index [song_index - 1] """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await ctx.send(embed=self.error_embed(f'Not playing. [{ctx.message.author.mention}]'))

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await ctx.send(embed=self.error_embed(f'Not connected to the same voice channel. [{ctx.message.author.mention}]'))

        if song_index > len(player.queue) + 1:
            return await ctx.send(embed=self.error_embed("There is no such song in the queue."))

        for i in range(song_index - 1):
            player.queue.pop(0)
        await player.skip()
        await ctx.message.add_reaction("✅")

    @commands.command(aliases=['dc', 'stop'])
    async def leave(self, ctx):
        """ Disconnects the player from the voice channel and clears its queue. """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            return await ctx.send(embed=self.error_embed(f'Not playing. [{ctx.message.author.mention}]'))

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the bot
            # may not disconnect the bot.
            return await ctx.send(embed=self.error_embed(f'Not connected to the same voice channel. [{ctx.message.author.mention}]'))

        # Clear the queue to ensure old tracks don't start playing
        # when someone else queues something.
        player.queue.clear()
        # Stop the current track so Lavalink consumes less resources.
        await player.stop()
        # Disconnect from the voice channel.
        await ctx.send(embed=self.reply_embed(f"Left channel `{ctx.message.author.voice.channel}` [{ctx.message.author.mention}]"))
        await ctx.guild.change_voice_state(channel=None)


def setup(bot):
    bot.add_cog(Music(bot))
