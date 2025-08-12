from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from utils.queue import get_queue, clear_queue
from utils.helpers import is_admin, is_group_admin
import logging

logger = logging.getLogger(__name__)

@Client.on_message(filters.command(["pause"]) & filters.group)
async def pause_command(client: Client, message: Message):
    """Pause current playback"""
    try:
        # Check admin permission
        if not await is_group_admin(message) and not is_admin(message):
            await message.reply_text("❌ **You need to be an admin to control playback!**")
            return
        
        chat_id = message.chat.id
        queue = get_queue(chat_id)
        
        if not queue.is_playing or queue.is_paused:
            await message.reply_text("❌ **Nothing is playing or already paused!**")
            return
        
        await client.call_py.pause_stream(chat_id)
        queue.is_paused = True
        
        await message.reply_text(
            f"⏸️ **Paused**\n\n🎵 **Track:** {queue.current.title if queue.current else 'Unknown'}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("▶️ Resume", callback_data="resume")]
            ])
        )
    
    except Exception as e:
        logger.error(f"Pause command error: {e}")
        await message.reply_text("❌ **Error:** Could not pause playback.")

@Client.on_message(filters.command(["resume"]) & filters.group)
async def resume_command(client: Client, message: Message):
    """Resume current playback"""
    try:
        # Check admin permission
        if not await is_group_admin(message) and not is_admin(message):
            await message.reply_text("❌ **You need to be an admin to control playback!**")
            return
        
        chat_id = message.chat.id
        queue = get_queue(chat_id)
        
        if not queue.is_paused:
            await message.reply_text("❌ **Nothing is paused!**")
            return
        
        await client.call_py.resume_stream(chat_id)
        queue.is_paused = False
        
        await message.reply_text(
            f"▶️ **Resumed**\n\n🎵 **Track:** {queue.current.title if queue.current else 'Unknown'}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⏸️ Pause", callback_data="pause")]
            ])
        )
    
    except Exception as e:
        logger.error(f"Resume command error: {e}")
        await message.reply_text("❌ **Error:** Could not resume playback.")

@Client.on_message(filters.command(["skip", "next"]) & filters.group)
async def skip_command(client: Client, message: Message):
    """Skip current track"""
    try:
        # Check admin permission
        if not await is_group_admin(message) and not is_admin(message):
            await message.reply_text("❌ **You need to be an admin to control playback!**")
            return
        
        chat_id = message.chat.id
        queue = get_queue(chat_id)
        
        if not queue.is_playing and not queue.current:
            await message.reply_text("❌ **Nothing is playing!**")
            return
        
        current_title = queue.current.title if queue.current else "Unknown"
        
        # Clean up current file
        if queue.current and queue.current.filepath:
            try:
                import os
                os.remove(queue.current.filepath)
            except:
                pass
        
        if queue.queue:
            # Import here to avoid circular imports
            from handlers.play import start_playback
            
            skip_msg = await message.reply_text(f"⏭️ **Skipped:** {current_title}\n\n🔄 **Loading next track...**")
            await start_playback(client, chat_id, skip_msg)
        else:
            # No more tracks
            await client.call_py.leave_group_call(chat_id)
            queue.clear()
            await message.reply_text(f"⏭️ **Skipped:** {current_title}\n\n✅ **Queue finished!** Left voice chat.")
    
    except Exception as e:
        logger.error(f"Skip command error: {e}")
        await message.reply_text("❌ **Error:** Could not skip track.")

@Client.on_message(filters.command(["stop", "end"]) & filters.group)
async def stop_command(client: Client, message: Message):
    """Stop playback and clear queue"""
    try:
        # Check admin permission
        if not await is_group_admin(message) and not is_admin(message):
            await message.reply_text("❌ **You need to be an admin to control playback!**")
            return
        
        chat_id = message.chat.id
        queue = get_queue(chat_id)
        
        if not queue.is_playing and not queue.current:
            await message.reply_text("❌ **Nothing is playing!**")
            return
        
        # Clean up current file
        if queue.current and queue.current.filepath:
            try:
                import os
                os.remove(queue.current.filepath)
            except:
                pass
        
        # Leave voice chat
        try:
            await client.call_py.leave_group_call(chat_id)
        except:
            pass
        
        # Clear queue
        tracks_cleared = len(queue.queue)
        queue.clear()
        
        await message.reply_text(
            f"⏹️ **Playback stopped!**\n\n"
            f"🗑️ **Cleared {tracks_cleared} tracks from queue**\n"
            f"✅ **Left voice chat**"
        )
    
    except Exception as e:
        logger.error(f"Stop command error: {e}")
        await message.reply_text("❌ **Error:** Could not stop playback.")

@Client.on_message(filters.command(["queue", "q"]) & filters.group)
async def queue_command(client: Client, message: Message):
    """Show current queue"""
    try:
        queue = get_queue(message.chat.id)
        queue_text = queue.get_queue_text()
        
        keyboard = None
        if queue.current or queue.queue:
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⏸️ Pause", callback_data="pause"),
                    InlineKeyboardButton("⏭️ Skip", callback_data="skip")
                ],
                [
                    InlineKeyboardButton("🔁 Loop", callback_data="loop"),
                    InlineKeyboardButton("⏹️ Stop", callback_data="stop")
                ]
            ])
        
        await message.reply_text(queue_text, reply_markup=keyboard)
    
    except Exception as e:
        logger.error(f"Queue command error: {e}")
        await message.reply_text("❌ **Error:** Could not get queue information.")

@Client.on_message(filters.command(["loop"]) & filters.group)
async def loop_command(client: Client, message: Message):
    """Toggle loop mode"""
    try:
        # Check admin permission
        if not await is_group_admin(message) and not is_admin(message):
            await message.reply_text("❌ **You need to be an admin to control playback!**")
            return
        
        queue = get_queue(message.chat.id)
        queue.loop_mode = not queue.loop_mode
        
        status = "**enabled**" if queue.loop_mode else "**disabled**"
        icon = "🔁" if queue.loop_mode else "➡️"
        
        await message.reply_text(f"{icon} **Loop mode {status}**")
    
    except Exception as e:
        logger.error(f"Loop command error: {e}")
        await message.reply_text("❌ **Error:** Could not toggle loop mode.")

@Client.on_message(filters.command(["shuffle"]) & filters.group)
async def shuffle_command(client: Client, message: Message):
    """Shuffle queue"""
    try:
        # Check admin permission
        if not await is_group_admin(message) and not is_admin(message):
            await message.reply_text("❌ **You need to be an admin to control playback!**")
            return
        
        queue = get_queue(message.chat.id)
        
        if not queue.queue:
            await message.reply_text("❌ **Queue is empty!**")
            return
        
        queue.shuffle()
        status = "**enabled**" if queue.shuffle_mode else "**disabled**"
        
        await message.reply_text(f"🔀 **Queue shuffled!** Shuffle mode {status}")
    
    except Exception as e:
        logger.error(f"Shuffle command error: {e}")
        await message.reply_text("❌ **Error:** Could not shuffle queue.")

@Client.on_message(filters.command(["clear", "clearqueue"]) & filters.group)
async def clear_command(client: Client, message: Message):
    """Clear queue"""
    try:
        # Check admin permission
        if not await is_group_admin(message) and not is_admin(message):
            await message.reply_text("❌ **You need to be an admin to control playback!**")
            return
        
        chat_id = message.chat.id
        queue = get_queue(chat_id)
        
        if not queue.queue:
            await message.reply_text("❌ **Queue is already empty!**")
            return
        
        tracks_cleared = len(queue.queue)
        queue.queue.clear()
        
        await message.reply_text(f"🗑️ **Cleared {tracks_cleared} tracks from queue!**")
    
    except Exception as e:
        logger.error(f"Clear command error: {e}")
        await message.reply_text("❌ **Error:** Could not clear queue.")