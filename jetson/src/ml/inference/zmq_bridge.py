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
