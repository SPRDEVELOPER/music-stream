import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class MediaType(Enum):
    AUDIO = "audio"
    VIDEO = "video"

@dataclass
class Track:
    """Track information"""
    title: str
    duration: int
    url: str
    source: str
    media_type: MediaType
    filepath: str = None
    thumbnail: str = None
    requested_by: str = None
    user_id: int = None
    chat_id: int = None

class MusicQueue:
    """Music queue manager for each chat"""
    
    def __init__(self):
        self.queue: List[Track] = []
        self.current: Optional[Track] = None
        self.is_playing: bool = False
        self.is_paused: bool = False
        self.loop_mode: bool = False
        self.shuffle_mode: bool = False
        self.volume: int = 100
        self.position: int = 0
        
    def add(self, track: Track) -> int:
        """Add track to queue"""
        self.queue.append(track)
        return len(self.queue)
    
    def get_next(self) -> Optional[Track]:
        """Get next track"""
        if self.loop_mode and self.current:
            return self.current
        
        if self.queue:
            return self.queue.pop(0)
        return None
    
    def skip(self) -> Optional[Track]:
        """Skip current track"""
        self.current = self.get_next()
        return self.current
    
    def clear(self):
        """Clear queue"""
        self.queue.clear()
        self.current = None
        self.is_playing = False
        self.is_paused = False
    
    def remove(self, index: int) -> bool:
        """Remove track by index"""
        try:
            if 0 <= index < len(self.queue):
                self.queue.pop(index)
                return True
        except:
            pass
        return False
    
    def shuffle(self):
        """Shuffle queue"""
        import random
        random.shuffle(self.queue)
        self.shuffle_mode = not self.shuffle_mode
    
    def get_queue_text(self) -> str:
        """Get formatted queue text"""
        if not self.current and not self.queue:
            return "**Queue is empty**"
        
        text = ""
        
        # Current track
        if self.current:
            status = "⏸️ Paused" if self.is_paused else "▶️ Playing"
            loop_icon = "🔁" if self.loop_mode else ""
            text += f"**{status} {loop_icon}**\n"
            text += f"🎵 **{self.current.title}**\n"
            text += f"⏰ Duration: {self._format_duration(self.current.duration)}\n"
            text += f"📂 Source: {self.current.source.title()}\n\n"
        
        # Queue
        if self.queue:
            text += f"**📋 Queue ({len(self.queue)} tracks):**\n"
            for i, track in enumerate(self.queue[:10], 1):  # Show first 10
                text += f"`{i}.` **{track.title}** - {self._format_duration(track.duration)}\n"
            
            if len(self.queue) > 10:
                text += f"\n... and {len(self.queue) - 10} more tracks"
        
        return text
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration"""
        if seconds < 3600:
            minutes = seconds // 60
            seconds = seconds % 60
            return f"{minutes:02d}:{seconds:02d}"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

# Global queue manager
queues: Dict[int, MusicQueue] = {}

def get_queue(chat_id: int) -> MusicQueue:
    """Get or create queue for chat"""
    if chat_id not in queues:
        queues[chat_id] = MusicQueue()
    return queues[chat_id]

def clear_queue(chat_id: int):
    """Clear queue for chat"""
    if chat_id in queues:
        queues[chat_id].clear()

def remove_queue(chat_id: int):
    """Remove queue for chat"""
    if chat_id in queues:
        del queues[chat_id]