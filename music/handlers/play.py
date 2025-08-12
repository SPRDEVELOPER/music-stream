from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
from pytgcalls.exceptions import NoActiveGroupCall
import asyncio
import os
from utils.yt import downloader
from utils.queue import get_queue, Track, MediaType
from utils.helpers import is_admin, is_group_admin, Progress
from config import Config
import logging

logger = logging.getLogger(__name__)

@Client.on_message(filters.command(["play", "p"]) & filters.group)
async def play_command(client: Client, message: Message):
    """Play audio in voice chat"""
    try:
        # Check if user provided query
        if len(message.command) < 2:
            await message.reply_text(
                "**Usage:** `/play <song name or URL>`\n\n"
                "**Examples:**\n"
                "• `/play Shape of You`\n"
                "• `/play https://youtube.com/watch?v=...`\n"
                "• `/play https://soundcloud.com/...`"
            )
            return
        
        # Get query
        query = message.text.split(None, 1)[1]
        chat_id = message.chat.id
        
        # Get queue
        queue = get_queue(chat_id)
        
        # Send processing message
        processing_msg = await message.reply_text("🔍 **Searching...**")
        
        # Search or get info
        if downloader.is_url(query):
            info = await downloader.get_info(query)
            if not info:
                await processing_msg.edit_text("❌ **Error:** Invalid URL or video not found.")
                return
            
            track_info = [info]
        else:
            # Search for the query
            search_results = await downloader.search(query, limit=1)
            if not search_results:
                await processing_msg.edit_text("❌ **Error:** No results found.")
                return
            
            # Get info for first result
            video_url = search_results[0]['link']
            info = await downloader.get_info(video_url)
            if not info:
                await processing_msg.edit_text("❌ **Error:** Could not get video information.")
                return
            
            track_info = [info]
        
        # Create track
        track = await downloader.create_track_from_info(
            track_info[0],
            MediaType.AUDIO,
            message.from_user.first_name,
            message.from_user.id,
            chat_id
        )
        
        # Check duration
        if track.duration > Config.MAX_DURATION:
            await processing_msg.edit_text(
                f"❌ **Error:** Track too long! Maximum duration is "
                f"{Config.MAX_DURATION // 60} minutes."
            )
            return
        
        # Add to queue
        position = queue.add(track)
        
        # If nothing is playing, start playing
        if not queue.is_playing and not queue.current:
            await start_playback(client, chat_id, processing_msg)
        else:
            # Just added to queue
            await processing_msg.edit_text(
                f"✅ **Added to queue at position {position}**\n\n"
                f"🎵 **Title:** {track.title}\n"
                f"⏰ **Duration:** {format_duration(track.duration)}\n"
                f"📂 **Source:** {track.source.title()}\n"
                f"👤 **Requested by:** {track.requested_by}",
                reply_markup=queue_keyboard()
            )
    
    except Exception as e:
        logger.error(f"Play command error: {e}")
        try:
            await processing_msg.edit_text("❌ **Error:** Something went wrong while processing your request.")
        except:
            await message.reply_text("❌ **Error:** Something went wrong while processing your request.")

async def start_playback(client: Client, chat_id: int, message: Message):
    """Start playing the next track"""
    try:
        queue = get_queue(chat_id)
        
        # Get next track
        track = queue.get_next()
        if not track:
            await message.edit_text("❌ **Queue is empty!**")
            return
        
        queue.current = track
        
        # Update message
        await message.edit_text(f"⬇️ **Downloading:** {track.title}")
        
        # Progress callback
        progress = Progress(message, "Downloading")
        
        # Download audio
        filepath = await downloader.download_audio(
            track.url,
            progress_callback=progress.update
        )
        
        if not filepath or not os.path.exists(filepath):
            await message.edit_text("❌ **Error:** Download failed!")
            # Try next track
            await start_playback(client, chat_id, message)
            return
        
        track.filepath = filepath
        
        # Join voice chat and play
        try:
            await client.call_py.join_group_call(
                chat_id,
                MediaStream(filepath, audio_bitrate=Config.AUDIO_BITRATE)
            )
        except NoActiveGroupCall:
            await message.edit_text(
                "❌ **Error:** No active voice chat found!\n\n"
                "Please start a voice chat first, then use `/play` command."
            )
            return
        except Exception as e:
            if "already joined" in str(e).lower():
                # Already joined, just change stream
                await client.call_py.change_stream(
                    chat_id,
                    MediaStream(filepath, audio_bitrate=Config.AUDIO_BITRATE)
                )
            else:
                logger.error(f"Join group call error: {e}")
                await message.edit_text(f"❌ **Error:** Could not join voice chat!\n\n`{str(e)}`")
                return
        
        # Update status
        queue.is_playing = True
        queue.is_paused = False
        
        # Send now playing message
        await message.edit_text(
            f"▶️ **Now Playing**\n\n"
            f"🎵 **Title:** {track.title}\n"
            f"⏰ **Duration:** {format_duration(track.duration)}\n"
            f"📂 **Source:** {track.source.title()}\n"
            f"👤 **Requested by:** {track.requested_by}",
            reply_markup=playback_keyboard()
        )
        
        # Auto-play next track when current ends
        asyncio.create_task(wait_for_completion(client, chat_id))
        
    except Exception as e:
        logger.error(f"Playback error: {e}")
        await message.edit_text(f"❌ **Error:** {str(e)}")

async def wait_for_completion(client: Client, chat_id: int):
    """Wait for current track to complete and play next"""
    try:
        queue = get_queue(chat_id)
        if not queue.current:
            return
        
        # Wait for track duration
        await asyncio.sleep(queue.current.duration + 5)  # Add 5 seconds buffer
        
        # Check if still playing same track
        if queue.is_playing and not queue.is_paused:
            # Clean up current file
            if queue.current and queue.current.filepath:
                try:
                    os.remove(queue.current.filepath)
                except:
                    pass
            
            # Play next track if available
            if queue.queue or queue.loop_mode:
                # Send message about next track
                try:
                    next_msg = await client.send_message(chat_id, "⏭️ **Playing next track...**")
                    await start_playback(client, chat_id, next_msg)
                except:
                    pass
            else:
                # No more tracks, leave voice chat
                try:
                    await client.call_py.leave_group_call(chat_id)
                    queue.clear()
                    await client.send_message(
                        chat_id, 
                        "✅ **Playback finished!** Left voice chat."
                    )
                except:
                    pass
    
    except Exception as e:
        logger.error(f"Completion wait error: {e}")

def format_duration(seconds: int) -> str:
    """Format duration from seconds to MM:SS"""
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

def playback_keyboard():
    """Create playback control keyboard"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏸️ Pause", callback_data="pause"),
            InlineKeyboardButton("⏭️ Skip", callback_data="skip"),
            InlineKeyboardButton("⏹️ Stop", callback_data="stop")
        ],
        [
            InlineKeyboardButton("📋 Queue", callback_data="queue"),
            InlineKeyboardButton("🔁 Loop", callback_data="loop"),
            InlineKeyboardButton("🔀 Shuffle", callback_data="shuffle")
        ]
    ])

def queue_keyboard():
    """Create queue keyboard"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 Show Queue", callback_data="queue"),
            InlineKeyboardButton("⏭️ Skip", callback_data="skip")
        ]
    ])

# Callback query handlers
@Client.on_callback_query(filters.regex(r"^(pause|resume|skip|stop|queue|loop|shuffle)$"))
async def playback_callbacks(client: Client, callback: CallbackQuery):
    """Handle playback control callbacks"""
    try:
        chat_id = callback.message.chat.id
        user_id = callback.from_user.id
        action = callback.data
        
        # Check admin permission for controls (except queue)
        if action != "queue":
            if not await is_group_admin(callback.message, user_id) and not is_admin(callback.message):
                await callback.answer("❌ You need to be an admin to control playback!", show_alert=True)
                return
        
        queue = get_queue(chat_id)
        
        if action == "pause":
            if queue.is_playing and not queue.is_paused:
                await client.call_py.pause_stream(chat_id)
                queue.is_paused = True
                await callback.answer("⏸️ Paused")
                
                # Update keyboard
                new_keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("▶️ Resume", callback_data="resume"),
                        InlineKeyboardButton("⏭️ Skip", callback_data="skip"),
                        InlineKeyboardButton("⏹️ Stop", callback_data="stop")
                    ],
                    [
                        InlineKeyboardButton("📋 Queue", callback_data="queue"),
                        InlineKeyboardButton("🔁 Loop", callback_data="loop"),
                        InlineKeyboardButton("🔀 Shuffle", callback_data="shuffle")
                    ]
                ])
                await callback.message.edit_reply_markup(new_keyboard)
            else:
                await callback.answer("❌ Nothing to pause!")
        
        elif action == "resume":
            if queue.is_paused:
                await client.call_py.resume_stream(chat_id)
                queue.is_paused = False
                await callback.answer("▶️ Resumed")
                
                # Update keyboard back to pause
                await callback.message.edit_reply_markup(playback_keyboard())
            else:
                await callback.answer("❌ Nothing to resume!")
        
        elif action == "skip":
            if queue.is_playing or queue.queue:
                # Clean up current file
                if queue.current and queue.current.filepath:
                    try:
                        os.remove(queue.current.filepath)
                    except:
                        pass
                
                if queue.queue:
                    await start_playback(client, chat_id, callback.message)
                    await callback.answer("⏭️ Skipped to next track")
                else:
                    await client.call_py.leave_group_call(chat_id)
                    queue.clear()
                    await callback.message.edit_text("⏹️ **Playback stopped!** No more tracks in queue.")
                    await callback.answer("⏭️ Skipped - Queue empty")
            else:
                await callback.answer("❌ Nothing to skip!")
        
        elif action == "stop":
            if queue.is_playing:
                await client.call_py.leave_group_call(chat_id)
                
                # Clean up files
                if queue.current and queue.current.filepath:
                    try:
                        os.remove(queue.current.filepath)
                    except:
                        pass
                
                queue.clear()
                await callback.message.edit_text("⏹️ **Playback stopped!**")
                await callback.answer("⏹️ Stopped")
            else:
                await callback.answer("❌ Nothing to stop!")
        
        elif action == "loop":
            queue.loop_mode = not queue.loop_mode
            status = "enabled" if queue.loop_mode else "disabled"
            await callback.answer(f"🔁 Loop {status}")
        
        elif action == "shuffle":
            if queue.queue:
                queue.shuffle()
                status = "enabled" if queue.shuffle_mode else "disabled"
                await callback.answer(f"🔀 Shuffle {status}")
            else:
                await callback.answer("❌ Queue is empty!")
        
        elif action == "queue":
            queue_text = queue.get_queue_text()
            await callback.answer()
            await callback.message.reply_text(queue_text)
    
    except Exception as e:
        logger.error(f"Callback error: {e}")
        await callback.answer("❌ Error occurred!")

@Client.on_message(filters.command(["np", "nowplaying"]) & filters.group)
async def now_playing_command(client: Client, message: Message):
    """Show now playing info"""
    try:
        queue = get_queue(message.chat.id)
        
        if not queue.current:
            await message.reply_text("❌ **Nothing is currently playing!**")
            return
        
        track = queue.current
        status = "⏸️ Paused" if queue.is_paused else "▶️ Playing"
        loop_status = "🔁 Loop: ON" if queue.loop_mode else "🔁 Loop: OFF"
        
        text = (
            f"**{status}**\n\n"
            f"🎵 **Title:** {track.title}\n"
            f"⏰ **Duration:** {format_duration(track.duration)}\n"
            f"📂 **Source:** {track.source.title()}\n"
            f"👤 **Requested by:** {track.requested_by}\n\n"
            f"{loop_status}\n"
            f"📋 **Queue:** {len(queue.queue)} tracks"
        )
        
        await message.reply_text(text, reply_markup=playback_keyboard())
    
    except Exception as e:
        logger.error(f"Now playing error: {e}")
        await message.reply_text("❌ **Error:** Could not get current track info.")