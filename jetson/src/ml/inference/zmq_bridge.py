"""ZeroMQ frame-pair receive helpers for Jetson inference."""

from __future__ import annotations

from frame_pair_transport import decode_frame_pair


def _recv_zmq_frame_pair(connect_endpoint: str):
    try:
        import zmq
    except ImportError as exc:  # pragma: no cover - runtime dependency
        raise RuntimeError("pyzmq is required for jetson ZeroMQ inference mode.") from exc

    context = zmq.Context()
    sub_socket = context.socket(zmq.SUB)
    sub_socket.setsockopt(zmq.LINGER, 0)
    sub_socket.setsockopt_string(zmq.SUBSCRIBE, "frame-pair")
    sub_socket.connect(connect_endpoint)

    try:
        parts = sub_socket.recv_multipart()
        metadata, rgb_frame, thermal_frame = decode_frame_pair(parts)
        return metadata, rgb_frame, thermal_frame
    finally:
        sub_socket.close()
        context.term()


def run_one_zmq_inference(
    infer_and_send,
    rgb_model,
    thermal_model,
    fusion_endpoint: str,
    connect_endpoint: str,
    backend_incident_endpoint: str | None = None,
    **kwargs,
) -> None:
    metadata, rgb_frame, thermal_frame = _recv_zmq_frame_pair(connect_endpoint)
    print(
        "received ZeroMQ frame pair "
        f"timestamp={metadata.get('timestamp')} "
        f"rgb_shape={tuple(rgb_frame.shape)} thermal_shape={tuple(thermal_frame.shape)}"
    )
    infer_and_send(
        rgb_model=rgb_model,
        thermal_model=thermal_model,
        rgb_frame=rgb_frame,
        thermal_frame=thermal_frame,
        fusion_endpoint=fusion_endpoint,
        backend_incident_endpoint=backend_incident_endpoint,
        metadata=metadata,
        **kwargs,
    )


def run_ipc_zmq_loop(
    infer_and_send,
    rgb_model,
    thermal_model,
    fusion_endpoint: str,
    connect_endpoint: str,
    **kwargs,
) -> None:
    """Subscribe to per-frame IPC ZMQ messages (ingest_gi format) and infer on buffered pairs.

    Expects 3-part multipart messages: [topic, meta_json, raw_bytes]
    where topic is b"rgb" or b"thermal" and meta contains height/width/channels.
    This runs until interrupted — use in place of the run_one_zmq_inference loop.
    """
    import json

    import numpy as np

    try:
        import zmq
    except ImportError as exc:  # pragma: no cover - runtime dependency
        raise RuntimeError("pyzmq is required for ZMQ inference mode.") from exc

    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.LINGER, 0)
    socket.setsockopt(zmq.SUBSCRIBE, b"rgb")
    socket.setsockopt(zmq.SUBSCRIBE, b"thermal")
    socket.connect(connect_endpoint)
    print(f"ZMQ IPC subscriber connected to {connect_endpoint}")

    current_frames: dict[str, tuple | None] = {"rgb": None, "thermal": None}

    try:
        while True:
            topic_bytes, meta_raw, frame_raw = socket.recv_multipart()
            modality = topic_bytes.decode("utf-8")
            meta = json.loads(meta_raw.decode("utf-8"))

            frame = (
                np.frombuffer(frame_raw, dtype=np.uint8)
                .reshape((meta["height"], meta["width"], meta["channels"]))
                .copy()
            )
            current_frames[modality] = (meta, frame)

            if current_frames["rgb"] is not None and current_frames["thermal"] is not None:
                rgb_meta, rgb_frame = current_frames["rgb"]
                _, thermal_frame = current_frames["thermal"]
                metadata = {"timestamp": rgb_meta.get("timestamp")}
                infer_and_send(
                    rgb_model=rgb_model,
                    thermal_model=thermal_model,
                    rgb_frame=rgb_frame,
                    thermal_frame=thermal_frame,
                    fusion_endpoint=fusion_endpoint,
                    metadata=metadata,
                    **kwargs,
                )
                current_frames = {"rgb": None, "thermal": None}
    finally:
        socket.close()
        context.term()
