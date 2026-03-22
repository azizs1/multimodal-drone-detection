from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(
    tags=["websocket"],
)


class AlertConnectionManager:
    """Tracks active websocket clients connected to the alert endpoint."""

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


alert_connection_manager = AlertConnectionManager()


@router.websocket("/detections/alert")
async def alert_socket(websocket: WebSocket):
    """Websocket endpoint to receive real-time detection IDs."""
    await alert_connection_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        alert_connection_manager.disconnect(websocket)
