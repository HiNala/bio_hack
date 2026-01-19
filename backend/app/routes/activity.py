"""
Activity Stream Routes

Provides Server-Sent Events (SSE) endpoint for real-time agent activity updates.
"""

from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse
from app.services.activity_stream import activity_stream, activity_event_generator

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("/stream")
async def stream_activity():
    """
    Stream agent activity updates via Server-Sent Events.
    
    Connect to this endpoint to receive real-time updates about what the agent is doing.
    
    Event types:
    - data: Current activity update
    - history: Recent activity history (sent on connect)
    
    Activity types:
    - idle: Agent is waiting for input
    - thinking: Agent is analyzing the query
    - searching: Agent is searching databases
    - fetching: Agent is retrieving papers
    - processing: Agent is processing data
    - embedding: Agent is generating embeddings
    - synthesizing: Agent is creating the response
    - complete: Task completed
    - error: An error occurred
    """
    sub_id = activity_stream.subscribe()
    
    return StreamingResponse(
        activity_event_generator(sub_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.get("/current")
async def get_current_activity():
    """
    Get the current agent activity state.
    
    Returns the most recent activity without streaming.
    """
    current = activity_stream.get_current_activity()
    return current.to_dict()


@router.get("/history")
async def get_activity_history(limit: int = 20):
    """
    Get recent activity history.
    
    Args:
        limit: Maximum number of activities to return (default: 20)
    
    Returns:
        List of recent activities
    """
    history = activity_stream.get_history(limit)
    return [a.to_dict() for a in history]
