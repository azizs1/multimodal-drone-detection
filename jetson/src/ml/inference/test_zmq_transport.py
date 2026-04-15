import numpy as np

from frame_pair_transport import decode_frame_pair, encode_frame_pair

from . import zmq_bridge


def test_frame_pair_codec_round_trip():
    rgb = np.arange(24, dtype=np.uint8).reshape(2, 4, 3)
    thermal = (np.arange(24, dtype=np.uint8) + 10).reshape(2, 4, 3)

    parts = encode_frame_pair(123.5, rgb, thermal)
    metadata, decoded_rgb, decoded_thermal = decode_frame_pair(parts)

    assert metadata["timestamp"] == 123.5
    assert decoded_rgb.shape == rgb.shape
    assert decoded_thermal.shape == thermal.shape
    assert np.array_equal(decoded_rgb, rgb)
    assert np.array_equal(decoded_thermal, thermal)


def test_one_shot_zmq_inference_uses_received_frames(monkeypatch):
    calls = {}

    class DummyModel:
        def __call__(self, frame, verbose=False):
            calls.setdefault("shapes", []).append(frame.shape)
            return [object()]

    rgb = np.zeros((2, 2, 3), dtype=np.uint8)
    thermal = np.ones((2, 2, 3), dtype=np.uint8)

    monkeypatch.setattr(
        zmq_bridge,
        "_recv_zmq_frame_pair",
        lambda endpoint: ({"timestamp": 1.0}, rgb, thermal),
    )

    zmq_bridge.run_one_zmq_inference(
        infer_and_send=lambda **kwargs: calls.update(kwargs),
        rgb_model=DummyModel(),
        thermal_model=DummyModel(),
        fusion_endpoint="http://fusion",
        connect_endpoint="tcp://127.0.0.1:5560",
    )

    assert calls["rgb_frame"].shape == (2, 2, 3)
    assert calls["thermal_frame"].shape == (2, 2, 3)
