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

    async def broadcast_alert(self, payload: dict) -> None:
        stale_connections: list[WebSocket] = []
        for connection in list(self._connections):
            try:
                await connection.send_json(payload)
            except (WebSocketDisconnect, RuntimeError, OSError):
                stale_connections.append(connection)

        for connection in stale_connections:
            self.disconnect(connection)


alert_connection_manager = AlertConnectionManager()


@router.websocket("/incidents/alert")
async def alert_socket(websocket: WebSocket):
    """Websocket endpoint to receive real-time incident alerts."""
    await alert_connection_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print("Client disconnected")
    finally:
        alert_connection_manager.disconnect(websocket)
