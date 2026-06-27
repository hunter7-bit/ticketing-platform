# ---------------------------------------------------------
# WEBSOCKET MANAGER
# ---------------------------------------------------------

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List

router = APIRouter()

# This class keeps a list of every user's browser currently connected to our site
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        """Sends a message to EVERY connected browser instantly."""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass # If a connection dropped, just ignore it

# We create a single global instance of the manager
manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Keep the connection open and listen forever
        while True:
            # We don't actually expect the frontend to send us anything, 
            # but we need to listen so we know if they disconnect.
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.post("/ws/trigger-refresh")
async def trigger_refresh():
    """
    An internal endpoint that our background worker can call 
    to force a WebSocket broadcast to all connected users.
    """
    await manager.broadcast("refresh_events")
    return {"status": "broadcasted"}