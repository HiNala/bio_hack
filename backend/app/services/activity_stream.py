"""
Activity Stream Service

Provides real-time activity updates via Server-Sent Events (SSE).
Tracks agent activities like thinking, searching, processing, etc.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class ActivityType(str, Enum):
    """Types of agent activities."""
    IDLE = "idle"
    THINKING = "thinking"
    SEARCHING = "searching"
    FETCHING = "fetching"
    PROCESSING = "processing"
    EMBEDDING = "embedding"
    SYNTHESIZING = "synthesizing"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class AgentActivity:
    """Represents an agent activity event."""
    type: ActivityType
    message: str
    detail: Optional[str] = None
    api_call: Optional[str] = None
    articles_found: Optional[int] = None
    progress: Optional[float] = None
    timestamp: Optional[str] = None
    job_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type.value if isinstance(self.type, ActivityType) else self.type,
            "message": self.message,
            "detail": self.detail,
            "apiCall": self.api_call,
            "articlesFound": self.articles_found,
            "progress": self.progress,
            "timestamp": self.timestamp,
            "jobId": self.job_id,
        }


class ActivityStreamManager:
    """
    Manages activity streams for multiple clients.
    
    Uses asyncio queues to broadcast activities to all connected clients.
    """
    
    def __init__(self):
        self._subscribers: Dict[str, asyncio.Queue] = {}
        self._current_activity: AgentActivity = AgentActivity(
            type=ActivityType.IDLE,
            message="Ready to explore the scientific literature..."
        )
        self._activity_history: List[AgentActivity] = []
        self._max_history = 50
        
        # Fun idle messages
        self._idle_messages = [
            ("🔬", "Ready to explore the scientific literature..."),
            ("📚", "Awaiting your research question..."),
            ("🧠", "Neural pathways standing by..."),
            ("🔍", "250M+ papers at your fingertips..."),
            ("✨", "What shall we discover today?"),
            ("🌟", "Science never sleeps, and neither do I..."),
            ("🎯", "Ask me anything about science..."),
            ("💡", "Every great discovery starts with a question..."),
            ("🚀", "Ready for launch. Where to?"),
            ("🧬", "From DNA to dark matter, I'm here to help..."),
            ("⚛️", "Quantum states initialized..."),
            ("🧪", "Beakers bubbling, hypotheses forming..."),
            ("🔭", "Telescope calibrated for discovery..."),
            ("🧮", "Algorithms humming, vectors aligning..."),
            ("🌌", "Exploring the universe of knowledge..."),
        ]
        self._idle_index = 0
    
    def subscribe(self) -> str:
        """
        Subscribe to activity stream.
        
        Returns:
            Subscription ID
        """
        sub_id = str(uuid.uuid4())
        self._subscribers[sub_id] = asyncio.Queue(maxsize=100)
        logger.info(f"New activity stream subscriber: {sub_id}")
        return sub_id
    
    def unsubscribe(self, sub_id: str):
        """Unsubscribe from activity stream."""
        if sub_id in self._subscribers:
            del self._subscribers[sub_id]
            logger.info(f"Activity stream subscriber disconnected: {sub_id}")
    
    async def broadcast(self, activity: AgentActivity):
        """
        Broadcast activity to all subscribers.
        
        Args:
            activity: Activity to broadcast
        """
        self._current_activity = activity
        
        # Add to history (skip idle)
        if activity.type != ActivityType.IDLE:
            self._activity_history.append(activity)
            if len(self._activity_history) > self._max_history:
                self._activity_history = self._activity_history[-self._max_history:]
        
        # Broadcast to all subscribers
        for sub_id, queue in list(self._subscribers.items()):
            try:
                # Non-blocking put, drop if queue is full
                queue.put_nowait(activity)
            except asyncio.QueueFull:
                logger.warning(f"Activity queue full for subscriber {sub_id}")
    
    async def get_activity(self, sub_id: str, timeout: float = 30.0) -> Optional[AgentActivity]:
        """
        Get next activity for a subscriber.
        
        Args:
            sub_id: Subscription ID
            timeout: Timeout in seconds
            
        Returns:
            Next activity or None if timeout
        """
        if sub_id not in self._subscribers:
            return None
        
        try:
            return await asyncio.wait_for(
                self._subscribers[sub_id].get(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            # Send idle message on timeout
            emoji, message = self._idle_messages[self._idle_index]
            self._idle_index = (self._idle_index + 1) % len(self._idle_messages)
            return AgentActivity(
                type=ActivityType.IDLE,
                message=f"{emoji} {message}"
            )
    
    def get_current_activity(self) -> AgentActivity:
        """Get the current activity state."""
        return self._current_activity
    
    def get_history(self, limit: int = 20) -> List[AgentActivity]:
        """Get recent activity history."""
        return self._activity_history[-limit:]
    
    # Convenience methods for common activities
    
    async def thinking(self, message: str, detail: Optional[str] = None, job_id: Optional[str] = None):
        """Broadcast thinking activity."""
        await self.broadcast(AgentActivity(
            type=ActivityType.THINKING,
            message=f"🧠 {message}",
            detail=detail,
            job_id=job_id,
        ))
    
    async def searching(self, message: str, api_call: Optional[str] = None, job_id: Optional[str] = None):
        """Broadcast searching activity."""
        await self.broadcast(AgentActivity(
            type=ActivityType.SEARCHING,
            message=f"🔍 {message}",
            api_call=api_call,
            job_id=job_id,
        ))
    
    async def fetching(self, message: str, articles_found: int = 0, api_call: Optional[str] = None, job_id: Optional[str] = None):
        """Broadcast fetching activity."""
        await self.broadcast(AgentActivity(
            type=ActivityType.FETCHING,
            message=f"📡 {message}",
            articles_found=articles_found,
            api_call=api_call,
            job_id=job_id,
        ))
    
    async def processing(self, message: str, detail: Optional[str] = None, progress: Optional[float] = None, job_id: Optional[str] = None):
        """Broadcast processing activity."""
        await self.broadcast(AgentActivity(
            type=ActivityType.PROCESSING,
            message=f"⚙️ {message}",
            detail=detail,
            progress=progress,
            job_id=job_id,
        ))
    
    async def embedding(self, message: str, progress: float = 0.0, job_id: Optional[str] = None):
        """Broadcast embedding activity."""
        await self.broadcast(AgentActivity(
            type=ActivityType.EMBEDDING,
            message=f"🧮 {message}",
            progress=progress,
            job_id=job_id,
        ))
    
    async def synthesizing(self, message: str, detail: Optional[str] = None, job_id: Optional[str] = None):
        """Broadcast synthesizing activity."""
        await self.broadcast(AgentActivity(
            type=ActivityType.SYNTHESIZING,
            message=f"✨ {message}",
            detail=detail,
            job_id=job_id,
        ))
    
    async def complete(self, message: str, detail: Optional[str] = None, job_id: Optional[str] = None):
        """Broadcast completion activity."""
        await self.broadcast(AgentActivity(
            type=ActivityType.COMPLETE,
            message=f"✅ {message}",
            detail=detail,
            job_id=job_id,
        ))
    
    async def error(self, message: str, detail: Optional[str] = None, job_id: Optional[str] = None):
        """Broadcast error activity."""
        await self.broadcast(AgentActivity(
            type=ActivityType.ERROR,
            message=f"❌ {message}",
            detail=detail,
            job_id=job_id,
        ))
    
    async def idle(self):
        """Broadcast idle activity with rotating fun message."""
        emoji, message = self._idle_messages[self._idle_index]
        self._idle_index = (self._idle_index + 1) % len(self._idle_messages)
        await self.broadcast(AgentActivity(
            type=ActivityType.IDLE,
            message=f"{emoji} {message}",
        ))


# Global activity stream manager instance
activity_stream = ActivityStreamManager()


async def activity_event_generator(sub_id: str) -> AsyncGenerator[str, None]:
    """
    Generate SSE events for activity stream.
    
    Args:
        sub_id: Subscription ID
        
    Yields:
        SSE formatted event strings
    """
    try:
        # Send initial current state
        current = activity_stream.get_current_activity()
        yield f"data: {json.dumps(current.to_dict())}\n\n"
        
        # Send history
        history = activity_stream.get_history(10)
        if history:
            yield f"event: history\ndata: {json.dumps([a.to_dict() for a in history])}\n\n"
        
        # Stream updates
        while True:
            activity = await activity_stream.get_activity(sub_id)
            if activity:
                yield f"data: {json.dumps(activity.to_dict())}\n\n"
    except asyncio.CancelledError:
        logger.info(f"Activity stream cancelled for {sub_id}")
        raise
    finally:
        activity_stream.unsubscribe(sub_id)
