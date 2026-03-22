from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(
    tags=["websocket"],
)


class AlterConnectionManager:
    """Tracks active websocket clients connected to the alter endpoint."""

    def __init__(self):
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast_detection_id(self, detection_id: str) -> None:
        stale_connections: list[WebSocket] = []
        for connection in self._connections:
            try:
                await connection.send_text(detection_id)
            except Exception:
                stale_connections.append(connection)

        for connection in stale_connections:
            self.disconnect(connection)


alter_connection_manager = AlterConnectionManager()


@router.websocket("/detections/alter")
async def alter_socket(websocket: WebSocket):
    """Websocket endpoint to receive real-time detection IDs."""
    await alter_connection_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        alter_connection_manager.disconnect(websocket)
