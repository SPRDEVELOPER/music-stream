from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls.types import MediaStream
from pytgcalls.exceptions import NoActiveGroupCall
import os
from utils.yt import downloader
from utils.queue import get_queue, Track, MediaType
from utils.helpers import is_admin, is_group_admin, Progress
from config import Config
import logging

logger = logging.getLogger(__name__)

@Client.on_message(filters.command(["video", "v"]) & filters.group)
async def video_command(client: Client, message: Message):
    """Play video in voice chat"""
    try:
        # Check if user provided query
        if len(message.command) < 2:
            await message.reply_text(
                "**Usage:** `/video <video name or URL>`\n\n"
                "**Examples:**\n"
                "• `/video Despacito`\n"
                "• `/video https://youtube.com/watch?v=...`\n\n"
                "**Note:** Video will play in voice chat with audio and video."
            )
            return
        
        # Get query
        query = message.text.split(None, 1)[1]
        chat_id = message.chat.id
        
        # Get queue
        queue = get_queue(chat_id)
        
        # Send processing message
        processing_msg = await message.reply_text("🔍 **Searching for video...**")
        
        # Search or get info
        if downloader.is_url(query):
            info = await downloader.get_info(query)
            if not info:
                await processing_msg.edit_text("❌ **Error:** Invalid URL or video not found.")
                return
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
        
        # Create track
        track = await downloader.create_track_from_info(
            info,
            MediaType.VIDEO,
            message.from_user.first_name,
            message.from_user.id,
            chat_id
        )
        
        # Check duration
        if track.duration > Config.MAX_DURATION:
            await processing_msg.edit_text(
                f"❌ **Error:** Video too long! Maximum duration is "
                f"{Config.MAX_DURATION // 60} minutes."
            )
            return
        
        # Add to queue
        position = queue.add(track)
        
        # If nothing is playing, start playing
        if not queue.is_playing and not queue.current:
            await start_video_playback(client, chat_id, processing_msg)
        else:
            # Just added to queue
            await processing_msg.edit_text(
                f"✅ **Video added to queue at position {position}**\n\n"
                f"🎬 **Title:** {track.title}\n"
                f"⏰ **Duration:** {format_duration(track.duration)}\n"
                f"📂 **Source:** {track.source.title()}\n"
                f"👤 **Requested by:** {track.requested_by}",
                reply_markup=video_keyboard()
            )
    
    except Exception as e:
        logger.error(f"Video command error: {e}")
        try:
            await processing_msg.edit_text("❌ **Error:** Something went wrong while processing your request.")
        except:
            await message.reply_text("❌ **Error:** Something went wrong while processing your request.")

async def start_video_playback(client: Client, chat_id: int, message: Message):
    """Start playing the next video"""
    try:
        queue = get_queue(chat_id)
        
        # Get next track
        track = queue.get_next()
        if not track:
            await message.edit_text("❌ **Queue is empty!**")
            return
        
        queue.current = track
        
        # Update message
        await message.edit_text(f"⬇️ **Downloading video:** {track.title}")
        
        # Progress callback
        progress = Progress(message, "Downloading video")
        
        # Download video
        filepath = await downloader.download_video(
            track.url,
            progress_callback=progress.update
        )
        
        if not filepath or not os.path.exists(filepath):
            await message.edit_text("❌ **Error:** Video download failed!")
            # Try next track
            await start_video_playback(client, chat_id, message)
            return
        
        track.filepath = filepath
        
        # Join voice chat and play video
        try:
            await client.call_py.join_group_call(
                chat_id,
                MediaStream(
                    filepath,
                    audio_bitrate=Config.AUDIO_BITRATE,
                    video_bitrate=Config.VIDEO_BITRATE
                )
            )
        except NoActiveGroupCall:
            await message.edit_text(
                "❌ **Error:** No active voice chat found!\n\n"
                "Please start a voice chat first, then use `/video` command."
            )
            return
        except Exception as e:
            if "already joined" in str(e).lower():
                # Already joined, just change stream
                await client.call_py.change_stream(
                    chat_id,
                    MediaStream(
                        filepath,
                        audio_bitrate=Config.AUDIO_BITRATE,
                        video_bitrate=Config.VIDEO_BITRATE
                    )
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
            f"🎬 **Now Playing Video**\n\n"
            f"🎬 **Title:** {track.title}\n"
            f"⏰ **Duration:** {format_duration(track.duration)}\n"
            f"📂 **Source:** {track.source.title()}\n"
            f"👤 **Requested by:** {track.requested_by}\n\n"
            f"💡 **Tip:** Video is playing in the voice chat with both audio and video!",
            reply_markup=video_playback_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Video playback error: {e}")
        await message.edit_text(f"❌ **Error:** {str(e)}")

def format_duration(seconds: int) -> str:
    """Format duration from seconds to MM:SS"""
    if seconds < 3600:
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def video_keyboard():
    """Create video queue keyboard"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 Show Queue", callback_data="queue"),
            InlineKeyboardButton("⏭️ Skip", callback_data="skip")
        ]
    ])

def video_playback_keyboard():
    """Create video playback control keyboard"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏸️ Pause", callback_data="pause"),
            InlineKeyboardButton("⏭️ Skip", callback_data="skip"),
            InlineKeyboardButton("⏹️ Stop", callback_data="stop")
        ],
        [
            InlineKeyboardButton("📋 Queue", callback_data="queue"),
            InlineKeyboardButton("🔁 Loop", callback_data="loop")
        ]
    ])