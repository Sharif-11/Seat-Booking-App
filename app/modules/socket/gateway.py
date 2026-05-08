from typing import Any
import socketio


class SocketManager:
    def __init__(self, cors_allowed_origins: str | list[str] = "*"):
        self.sio = socketio.AsyncServer(
            async_mode="asgi",
            cors_allowed_origins="*",
            logger=True,
            engineio_logger=True,
        )
        self._register_handlers()

    def build_app(self, fastapi_app: Any) -> Any:
        """Wrap FastAPI app — call this ONCE and use the returned app as your ASGI app."""
        combined = socketio.ASGIApp(
            self.sio,
            other_asgi_app=fastapi_app,
            socketio_path="/ws/socket.io",  # ✅ full absolute path
        )
        print("✅ Socket.IO ready at /ws/socket.io")
        return combined

    async def on_connect(self, sid: str, environ: dict, auth: dict | None = None) -> None:
        print(f"[CONNECT]    sid={sid}")

    async def on_disconnect(self, sid: str) -> None:
        print(f"[DISCONNECT] sid={sid}")

    async def on_join_show(self, sid: str, data: dict) -> None:
        show_id = data.get("show_id")
        if not show_id:
            return
        await self.sio.enter_room(sid, room=str(show_id))
        print(f"[JOIN_SHOW]  sid={sid} joined room={show_id}")

    async def on_leave_show(self, sid: str, data: dict) -> None:
        show_id = data.get("show_id")
        if not show_id:
            return
        await self.sio.leave_room(sid, room=str(show_id))
        print(f"[LEAVE_SHOW] sid={sid} left room={show_id}")

    def _register_handlers(self) -> None:
        self.sio.on("connect",    self.on_connect)
        self.sio.on("disconnect", self.on_disconnect)
        self.sio.on("join_show",  self.on_join_show)
        self.sio.on("leave_show", self.on_leave_show)

    async def broadcast_to_room(
        self,
        room: str | int,
        event: str,
        data: Any,
        skip_sid: str | None = None,
    ) -> None:
        await self.sio.emit(event, data, room=str(room), skip_sid=skip_sid)
        print(f"[BROADCAST] event={event} room={room} skip={skip_sid}")


socket_manager = SocketManager(cors_allowed_origins="*")