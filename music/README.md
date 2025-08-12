# 🎵 Telegram Voice Chat Music & Video Streaming Bot

A powerful Telegram bot for playing music and videos in group voice chats. Built with Python, Pyrogram, and PyTgCalls.

## ✨ Features

### 🎵 Music & Video Playback
- Play music/video in Telegram group voice chats
- Support for YouTube, SoundCloud, Spotify, and direct links
- High-quality audio (512kbps) and video (1000kbps) streaming
- Queue system with up to 50 tracks
- Auto-play next track when current ends

### 🎛️ Playback Controls  
- Pause, resume, skip, and stop playback
- Loop mode for repeating current track
- Shuffle queue functionality
- Volume control and quality settings
- Real-time "Now Playing" information

### 👥 Group Management
- Multi-group support
- Admin-only playback controls
- Inline keyboard controls for easy interaction
- Queue display with track information
- Automatic cleanup of temporary files

### 🔧 Technical Features
- Async/await architecture for better performance
- Comprehensive error handling
- Progress tracking for downloads
- Automatic file cleanup
- Detailed logging system
- Support for various audio/video formats

## 🚀 Deployment on Replit

### Step 1: Setup Environment
1. Fork this repository or create a new Replit project
2. Upload all project files to your Replit
3. The `.replit` and `replit.nix` files will automatically configure the environment

### Step 2: Install Dependencies
Run in Replit shell:
```bash
pip install -r requirements.txt
```

### Step 3: Get Telegram Credentials

#### Get Bot Token:
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Create a new bot with `/newbot`
3. Save the bot token

#### Get API Credentials:
1. Visit [my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Go to "API development tools"
4. Create a new application
5. Save `API_ID` and `API_HASH`

#### Generate Session String:
Run in Replit shell:
```bash
python3 generate_session.py
```
Follow the prompts to generate your session string.

### Step 4: Configure Environment
Edit the `.env` file with your credentials:
```env
BOT_TOKEN=your_bot_token_here
API_ID=your_api_id_here  
API_HASH=your_api_hash_here
SESSION_STRING=your_session_string_here

# Optional
OWNER_ID=your_telegram_user_id
SUDO_USERS=user_id1,user_id2
LOG_CHAT_ID=-1001234567890
```

### Step 5: Install FFmpeg
FFmpeg is automatically installed via the `replit.nix` configuration. If you need to install it manually:
```bash
# This should be automatic, but if needed:
apt install ffmpeg -y
```

### Step 6: Start the Bot
```bash
python3 main.py
```

The bot will start and show startup logs. If successful, you'll see:
```
✓ Music Bot initialized successfully
✓ PyTgCalls started  
✓ Pyrogram client started
✓ Bot started as @YourBotUsername
```

## 🎮 Commands

### Music Commands
- `/play <song name/URL>` - Play audio in voice chat
- `/video <video name/URL>` - Play video in voice chat  
- `/pause` - Pause current playback
- `/resume` - Resume paused playback
- `/skip` - Skip to next track
- `/stop` - Stop playback and clear queue

### Queue Management
- `/queue` - Show current queue
- `/np` - Show now playing information
- `/loop` - Toggle loop mode for current track
- `/shuffle` - Shuffle the queue
- `/clear` - Clear the queue

### Admin Commands (Private)
- `/stats` - Show bot statistics
- `/logs` - Get bot log file
- `/cleanup` - Clean temporary files
- `/broadcast <message>` - Broadcast to all chats
- `/restart` - Restart the bot

### General
- `/help` - Show help message
- `/start` - Welcome message

## 📋 Usage Instructions

### For Users:
1. Add the bot to your group
2. Give the bot admin permissions
3. Start a voice chat in the group
4. Use `/play <song name>` to start playing music
5. Use inline buttons or commands to control playback

### For Admins:
1. Only group admins can control playback (pause, skip, stop, etc.)
2. Bot owner and sudo users have additional privileges
3. Use admin commands in private chat with the bot

## 🎯 Supported Platforms

- **YouTube** (youtube.com, youtu.be)
- **SoundCloud** (soundcloud.com)  
- **Direct Links** (MP3, MP4, WAV, FLAC, M4A, WebM, MKV)
- **Many others** supported by yt-dlp

## 🔧 Configuration

### Audio/Video Quality
- Audio bitrate: 512kbps
- Video bitrate: 1000kbps  
- Maximum track duration: 1 hour
- Queue limit: 50 tracks

### File Structure
```
/project
├── main.py              # Main bot file
├── config.py            # Configuration settings
├── requirements.txt     # Python dependencies
├── utils/
│   ├── yt.py           # YouTube/platform handlers
│   ├── queue.py        # Queue management  
│   └── helpers.py      # Helper functions
├── handlers/
│   ├── play.py         # Play command handlers
│   ├── video.py        # Video command handlers
│   ├── control.py      # Playback controls
│   └── admin.py        # Admin commands
├── downloads/          # Temporary downloads
├── cache/             # Cache directory
├── temp/              # Temporary files
└── logs/              # Log files
```

## 🐛 Troubleshooting

### Common Issues:

**Bot doesn't respond:**
- Check if bot token is correct
- Verify the bot is added to the group with admin permissions

**"No active voice chat" error:**
- Start a voice chat in the group first
- Make sure the bot has permission to join voice chats

**Download failures:**
- Check internet connection
- Some videos may be geo-restricted or unavailable
- Try with different URLs

**Session string errors:**
- Regenerate session string with `generate_session.py`
- Ensure API_ID and API_HASH are correct

### Getting Help:
1. Check the bot logs: `/logs` command (admin only)
2. Verify all environment variables are set correctly
3. Ensure FFmpeg is installed and working
4. Check Replit console for error messages

## 📝 Notes

- The bot automatically cleans up temporary files
- Downloaded files are stored temporarily and deleted after playback  
- Maximum file size depends on available storage
- Bot requires stable internet connection for streaming
- Keep your session string and bot token private

## 🔒 Security

- Never share your bot token or session string
- Use environment variables for sensitive data
- Regular cleanup of temporary files
- Admin-only sensitive commands
- Proper error handling to prevent crashes

## 📞 Support

If you encounter any issues:
1. Check this README for solutions
2. Review the error logs
3. Ensure all dependencies are installed correctly
4. Verify your Telegram credentials are valid

---

**Enjoy your music bot! 🎵**

*Built with ❤️ using Python, Pyrogram, and PyTgCalls*