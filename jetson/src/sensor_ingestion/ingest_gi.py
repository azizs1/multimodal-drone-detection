# Reference tutorials here: https://gstreamer.freedesktop.org/documentation/tutorials/basic/concepts.html?gi-language=python
# https://forums.developer.nvidia.com/t/changing-elements-in-a-pipeline/280465
# https://docs.nvidia.com/jetson/l4t-multimedia/classNvVideoConverter.html
# https://nvidia-jetson.piveral.com/jetson-orin-nano/understanding-nvvidconv-vs-videoconvert-on-the-nvidia-jetson-orin-nano-dev-board/
# ref tool: https://gstreamer.freedesktop.org/documentation/tools/gst-inspect.html?gi-language=c
# https://docs.nvidia.com/jetson/archives/r34.1/DeveloperGuide/text/SD/Multimedia/AcceleratedGstreamer.html
# rtp payload: https://gstreamer.freedesktop.org/documentation/rtp/rtph264pay.html?gi-language=c
# https://discourse.gstreamer.org/t/appsinks-new-sample-callback-function-is-never-triggered-as-the-data-flow-is-stuck/661/2
# https://forums.developer.nvidia.com/t/appsink-element-in-python-deepstream-pipeline/311528

import json
import os
import threading
import time

import gi
import numpy as np
import zmq
from dotenv import load_dotenv

gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gst", "1.0")
from gi.repository import GLib, Gst  # noqa: E402

load_dotenv()

send_lock = threading.Lock()

# init zeromq
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.set(zmq.SNDHWM, 1)  # keep only 1 frame in queue to avoid lag
socket.setsockopt(zmq.LINGER, 0)
socket.bind("ipc:///tmp/frame_bus")

latest_rgb = None
latest_thermal = None

frame_dir = "saved_frames"
os.makedirs(frame_dir, exist_ok=True)
frame_num = 0


def link_check(first, second):
    if not first.link(second):
        raise RuntimeError(f"Failed to link {first.name} to {second.name}")
    print(f"Linked {first.name} to {second.name}")


def link_tee(tee, element):
    tee_pad = tee.get_request_pad("src_%u")
    sink_pad = element.get_static_pad("sink")
    if tee_pad is None or sink_pad is None:
        raise RuntimeError("Failed to get pads for tee link")
    if tee_pad.link(sink_pad) != Gst.PadLinkReturn.OK:
        raise RuntimeError(f"Failed to link tee {tee.name} to {element.name}")


def build_gst_pipeline():
    Gst.init(None)
    pipeline = Gst.Pipeline.new("rgb-thermal-pipeline")

    # uncomment this portion and comment out until just before rgb_tee to use the test source
    # will need to update links and elements list accordingly
    # rgb_src = Gst.ElementFactory.make("videotestsrc", "rgb_src")
    # rgb_src.set_property("pattern", 0)
    # rgb_src.set_property("is-live", True)

    rgb_src = Gst.ElementFactory.make("v4l2src", "rgb_src")
    # double-check with v4l2-ctl that this is the right device for rgb
    rgb_src.set_property("device", "/dev/video0")

    rgb_caps = Gst.ElementFactory.make("capsfilter", "rgb_caps")
    # not specifying dimensions, we do that in scale_caps
    rgb_caps.set_property("caps", Gst.Caps.from_string("image/jpeg,width=1280,height=960,framerate=15/1"))

    # decode mjpeg to raw video
    rgb_jpegdec = Gst.ElementFactory.make("jpegdec", "rgb_jpegdec")
    # scale to ensure consistent output
    rgb_scale = Gst.ElementFactory.make("videoscale", "rgb_scale")

    # Keep RGB lower-res for live inference latency on Orin Nano.
    rgb_scale_caps = Gst.ElementFactory.make("capsfilter", "rgb_scale_caps")
    rgb_scale_caps.set_property(
        "caps", Gst.Caps.from_string("video/x-raw,width=1280,height=960,format=RGB")
    )

    rgb_tee = Gst.ElementFactory.make("tee", "rgb_tee")

    # rgb into inference
    rgb_inf_queue = Gst.ElementFactory.make("queue", "rgb_inf_queue")
    rgb_inf_convert = Gst.ElementFactory.make("videoconvert", "rgb_inf_convert")

    rgb_inf_bgr_caps = Gst.ElementFactory.make("capsfilter", "rgb_inf_bgr_caps")
    rgb_inf_bgr_caps.set_property("caps", Gst.Caps.from_string("video/x-raw,format=BGR"))

    rgb_appsink = Gst.ElementFactory.make("appsink", "rgb_appsink")
    rgb_appsink.set_property("emit-signals", True)
    rgb_appsink.set_property("sync", False)
    rgb_appsink.set_property("max-buffers", 1)
    rgb_appsink.set_property("drop", True)

    # rgb to webrtc (live stream)
    rgb_rtp_queue = Gst.ElementFactory.make("queue", "rgb_rtp_queue")
    rgb_rtp_convert = Gst.ElementFactory.make("videoconvert", "rgb_rtp_convert")

    # using sw encoder since orin nano doesnt have hw encoding
    rgb_encoder = Gst.ElementFactory.make("x264enc", "rgb_encoder")
    rgb_encoder.set_property("tune", "zerolatency")
    rgb_encoder.set_property("bitrate", 4000)
    rgb_encoder.set_property("speed-preset", "ultrafast")
    rgb_encoder.set_property("key-int-max", 30)
    rgb_encoder.set_property("insert-vui", True)
    rgb_encoder.set_property("byte-stream", True)
    rgb_encoder.set_property("aud", True)

    # mpeg-ts mux instead of rtp payloader
    rgb_ts_mux = Gst.ElementFactory.make("mpegtsmux", "rgb_ts_mux")
    rgb_ts_mux.set_property("alignment", 7)  # to help with mediamtx latency

    rgb_udp_sink = Gst.ElementFactory.make("udpsink", "rgb_udp_sink")
    rgb_udp_sink.set_property("host", "127.0.0.1")
    rgb_udp_sink.set_property("port", 6100)
    rgb_udp_sink.set_property("sync", False)
    rgb_udp_sink.set_property("async", False)
    rgb_udp_sink.set_property("qos", False)

    # thermal source (currently test)
    thermal_src = Gst.ElementFactory.make("v4l2src", "thermal_src")
    thermal_src.set_property("device", os.getenv("THERMAL_CAMERA_DEVICE", "/dev/video2"))
    thermal_src.set_property("do-timestamp", True)

    thermal_caps = Gst.ElementFactory.make("capsfilter", "thermal_caps")
    thermal_caps.set_property(
    "caps",
    Gst.Caps.from_string("video/x-raw,format=YUY2,width=512,height=384,framerate=25/1"),
	)

    thermal_tee = Gst.ElementFactory.make("tee", "thermal_tee")

    # thermal to inference
    thermal_inf_queue = Gst.ElementFactory.make("queue", "thermal_inf_queue")
    thermal_inf_convert = Gst.ElementFactory.make("videoconvert", "thermal_inf_convert")

    thermal_inf_bgr_caps = Gst.ElementFactory.make("capsfilter", "thermal_inf_bgr_caps")
    thermal_inf_bgr_caps.set_property("caps", Gst.Caps.from_string("video/x-raw,format=BGR"))

    thermal_appsink = Gst.ElementFactory.make("appsink", "thermal_appsink")
    thermal_appsink.set_property("emit-signals", True)
    thermal_appsink.set_property("sync", False)
    thermal_appsink.set_property("max-buffers", 1)
    thermal_appsink.set_property("drop", True)

    # thermal to webrtc (live stream)
    thermal_rtp_queue = Gst.ElementFactory.make("queue", "thermal_rtp_queue")
    thermal_rtp_convert = Gst.ElementFactory.make("videoconvert", "thermal_rtp_convert")

    # same as before, we use sw encoder
    thermal_encoder = Gst.ElementFactory.make("x264enc", "thermal_encoder")
    thermal_encoder.set_property("tune", "zerolatency")
    thermal_encoder.set_property("bitrate", 2000)
    thermal_encoder.set_property("speed-preset", "ultrafast")
    thermal_encoder.set_property("key-int-max", 30)
    thermal_encoder.set_property("insert-vui", True)
    thermal_encoder.set_property("byte-stream", True)
    thermal_encoder.set_property("aud", True)

    # mpeg-ts mux instead of rtp payloader
    thermal_ts_mux = Gst.ElementFactory.make("mpegtsmux", "thermal_ts_mux")
    thermal_ts_mux.set_property("alignment", 7)  # to help with mediamtx latency

    thermal_udp_sink = Gst.ElementFactory.make("udpsink", "thermal_udp_sink")
    thermal_udp_sink.set_property("host", "127.0.0.1")
    thermal_udp_sink.set_property("port", 6102)
    thermal_udp_sink.set_property("sync", False)
    thermal_udp_sink.set_property("async", False)
    thermal_udp_sink.set_property("qos", False)

    # elements list
    elements = [
        rgb_src,
        rgb_caps,
        rgb_jpegdec,
        rgb_scale,
        rgb_scale_caps,
        rgb_tee,
        rgb_inf_queue,
        rgb_inf_convert,
        rgb_inf_bgr_caps,
        rgb_appsink,
        rgb_rtp_queue,
        rgb_rtp_convert,
        rgb_encoder,
        rgb_ts_mux,
        rgb_udp_sink,
        thermal_src,
        thermal_caps,
        thermal_tee,
        thermal_inf_queue,
        thermal_inf_convert,
        thermal_inf_bgr_caps,
        thermal_appsink,
        thermal_rtp_queue,
        thermal_rtp_convert,
        thermal_encoder,
        thermal_ts_mux,
        thermal_udp_sink,
    ]

    for e in elements:
        if e is None:
            raise RuntimeError("Failed to create a GStreamer element")
        pipeline.add(e)

    # rgb links
    rgb_src.link(rgb_caps)
    rgb_caps.link(rgb_jpegdec)
    rgb_jpegdec.link(rgb_scale)
    rgb_scale.link(rgb_scale_caps)
    rgb_scale_caps.link(rgb_tee)

    # rgb to inference
    rgb_tee.link(rgb_inf_queue)
    rgb_inf_queue.link(rgb_inf_convert)
    rgb_inf_convert.link(rgb_inf_bgr_caps)
    rgb_inf_bgr_caps.link(rgb_appsink)

    # rgb to webrtc
    rgb_tee.link(rgb_rtp_queue)
    rgb_rtp_queue.link(rgb_rtp_convert)
    rgb_rtp_convert.link(rgb_encoder)
    rgb_encoder.link(rgb_ts_mux)
    rgb_ts_mux.link(rgb_udp_sink)

    # thermal links
    thermal_src.link(thermal_caps)
    thermal_caps.link(thermal_tee)

    # thermal to inference
    thermal_tee.link(thermal_inf_queue)
    thermal_inf_queue.link(thermal_inf_convert)
    thermal_inf_convert.link(thermal_inf_bgr_caps)
    thermal_inf_bgr_caps.link(thermal_appsink)

    # thermal to webrtc
    thermal_tee.link(thermal_rtp_queue)
    thermal_rtp_queue.link(thermal_rtp_convert)
    thermal_rtp_convert.link(thermal_encoder)
    thermal_encoder.link(thermal_ts_mux)
    thermal_ts_mux.link(thermal_udp_sink)

    return pipeline, rgb_appsink, thermal_appsink


# this function is what actually makes the rgb sample available to inference
def on_new_rgb_sample(appsink):
    sample = appsink.emit("pull-sample")
    buf = sample.get_buffer()
    caps = sample.get_caps()
    s = caps.get_structure(0)
    width = s.get_value("width")
    height = s.get_value("height")

    ok, map_info = buf.map(Gst.MapFlags.READ)
    if not ok:
        return Gst.FlowReturn.ERROR

    try:
        frame = np.frombuffer(map_info.data, dtype=np.uint8)
        frame = frame.reshape((height, width, 3))  # in BGR format now in np array

        meta = {
            "modality": "rgb",
            "timestamp": time.time(),
            "width": width,
            "height": height,
            "channels": 3,
            "dtype": "uint8",
        }
        with send_lock:
            socket.send_multipart(
                [
                    b"rgb",
                    json.dumps(meta).encode("utf-8"),
                    frame.tobytes(),
                ]
            )

        # print("RGB frame received", flush=True)
    finally:
        # NEED THIS IN THE FINALLY, OTHERWISE ITS GOING TO STAY
        # MAPPED AND BAD MEMORY ISSUES WILL HAPPEN!!
        buf.unmap(map_info)

    return Gst.FlowReturn.OK


# this function is what actually makes the thermal sample available for inference
def on_new_thermal_sample(appsink):
    sample = appsink.emit("pull-sample")
    buf = sample.get_buffer()
    caps = sample.get_caps()
    s = caps.get_structure(0)
    width = s.get_value("width")
    height = s.get_value("height")

    ok, map_info = buf.map(Gst.MapFlags.READ)
    if not ok:
        return Gst.FlowReturn.ERROR

    try:
        frame = np.frombuffer(map_info.data, dtype=np.uint8)
        frame = frame.reshape((height, width, 3))

        meta = {
            "modality": "thermal",
            "timestamp": time.time(),
            "width": width,
            "height": height,
            "channels": 3,
            "dtype": "uint8",
        }
        with send_lock:
            socket.send_multipart(
                [
                    b"thermal",  # topic
                    json.dumps(meta).encode("utf-8"),
                    frame.tobytes(),
                ]
            )

        # print("Thermal frame received", flush=True)
    finally:
        # NEED THIS IN THE FINALLY, OTHERWISE ITS GOING TO STAY
        # MAPPED AND BAD MEMORY ISSUES WILL HAPPEN!!
        buf.unmap(map_info)

    return Gst.FlowReturn.OK


# can't completely get rid of the bus, since this callback needs to match what gstreamer wants
def on_message(_bus, message, loop):
    t = message.type
    if t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print("ERROR:", err, debug)
        loop.quit()
    elif t == Gst.MessageType.EOS:
        print("END OF STREAM")
        loop.quit()


def main():
    Gst.init(None)
    pipeline, rgb_appsink, thermal_appsink = build_gst_pipeline()

    rgb_appsink.connect("new-sample", on_new_rgb_sample)
    thermal_appsink.connect("new-sample", on_new_thermal_sample)

    loop = GLib.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", on_message, loop)

    pipeline.set_state(Gst.State.PLAYING)
    print("Ingestion started")
    try:
        loop.run()
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    finally:
        # stopped state
        pipeline.set_state(Gst.State.NULL)
        print("Ingestion stopped")


if __name__ == "__main__":
    main()
