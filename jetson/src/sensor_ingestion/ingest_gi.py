# Reference tutorials here: https://gstreamer.freedesktop.org/documentation/tutorials/basic/concepts.html?gi-language=python
# https://forums.developer.nvidia.com/t/changing-elements-in-a-pipeline/280465
# https://docs.nvidia.com/jetson/l4t-multimedia/classNvVideoConverter.html
# https://nvidia-jetson.piveral.com/jetson-orin-nano/understanding-nvvidconv-vs-videoconvert-on-the-nvidia-jetson-orin-nano-dev-board/
# ref tool: https://gstreamer.freedesktop.org/documentation/tools/gst-inspect.html?gi-language=c
# https://docs.nvidia.com/jetson/archives/r34.1/DeveloperGuide/text/SD/Multimedia/AcceleratedGstreamer.html
# rtp payload: https://gstreamer.freedesktop.org/documentation/rtp/rtph264pay.html?gi-language=c
# https://discourse.gstreamer.org/t/appsinks-new-sample-callback-function-is-never-triggered-as-the-data-flow-is-stuck/661/2
# https://forums.developer.nvidia.com/t/appsink-element-in-python-deepstream-pipeline/311528

import numpy as np
import sys

import gi
gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib, GObject

from shared_buffer import buffer

# CHANGE THIS WHEN BACKEND CONTAINER IS SETUP
BACKEND_IP = "192.168.1.23"
BACKEND_PORT = 3000

def build_gst_pipeline():
    Gst.init(None)

    pipeline = Gst.Pipeline.new("rgb-thermal-pipeline")

    # # Sources
    # rgb_src = Gst.ElementFactory.make("nvarguscamerasrc", "rgb_src")
    # thermal_src = Gst.ElementFactory.make("v4l2src", "thermal_src")
    # thermal_src.set_property("device", "/dev/video1")

    # Test sources
    rgb_src = Gst.ElementFactory.make("videotestsrc", "rgb_src")
    rgb_src.set_property("pattern", 0)  # This gives SMPTE color bars
    thermal_src = Gst.ElementFactory.make("videotestsrc", "thermal_src")
    thermal_src.set_property("pattern", 18)  # This gives moving ball pattern

    # RGB caps and conv (raw video in NVMM at 1280x720 at 30FPS)
    rgb_caps = Gst.ElementFactory.make("capsfilter", "rgb_caps")
    rgb_caps.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM),width=1280,height=720,framerate=30/1"))
    rgb_conv = Gst.ElementFactory.make("nvvidconv", "rgb_conv") # this is needed for nvstreammux later

    # Thermal caps and conv (raw video at 320x240 in GRAY16_LE at 30FPS)
    thermal_caps = Gst.ElementFactory.make("capsfilter", "thermal_caps")
    thermal_caps.set_property("caps", Gst.Caps.from_string("video/x-raw,width=320,height=240,format=GRAY16_LE,framerate=30/1"))
    thermal_conv = Gst.ElementFactory.make("nvvidconv", "thermal_conv") # convert to NV12+NVMM

    # Another capsfilter needed for thermal here since we need it in NVMM
    thermal_conv_caps = Gst.ElementFactory.make("capsfilter", "thermal_conv_caps")
    thermal_conv_caps.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM),format=NV12"))

    # Mux lets us make a single batch that has both cam data in it
    mux = Gst.ElementFactory.make("nvstreammux", "mux")
    mux.set_property("batch-size", 2)
    mux.set_property("width", 1280)
    mux.set_property("height", 720)
    mux.set_property("live-source", True)
    mux.set_property("attach-sys-ts", True)
    # mux.set_property("sync-inputs", False)
    # mux.set_property("enable-padding", True)
    # mux.set_property("batched-push-timeout", 40000) # about 40ms

    # Adding tee here so that we can split into inference shared buffer and RTP stream
    tee = Gst.ElementFactory.make("tee", "tee")

    # Inference appsink to be used with shared buffer
    inf_queue = Gst.ElementFactory.make("queue", "inf_queue")
    inf_conv = Gst.ElementFactory.make("nvvideoconvert", "inf_conv") # NV12 to BGR
    inf_conv_caps = Gst.ElementFactory.make("capsfilter", "inf_conv_caps")
    inf_conv_caps.set_property("caps", Gst.Caps.from_string("video/x-raw,format=BGR"))
    appsink = Gst.ElementFactory.make("appsink", "appsink")
    appsink.set_property("emit-signals", True)
    appsink.set_property("sync", False)
    appsink.set_property("max-buffers", 1)
    appsink.set_property("drop", True)

    # RTP stream udpsink to stream to backend
    rtp_queue = Gst.ElementFactory.make("queue", "rtp_queue")
    encoder = Gst.ElementFactory.make("nvv4l2h264enc", "encoder") # H.264 encoder
    encoder.set_property("bitrate", 4000000) # 4Mbps for now? change later
    rtp_payload = Gst.ElementFactory.make("rtph264pay", "rtp_payload")
    rtp_payload.set_property("config-interval", 1)
    rtp_payload.set_property("pt", 96) # Payload type for H.264 rtp streams
    udpsink = Gst.ElementFactory.make("udpsink", "udpsink")
    udpsink.set_property("host", BACKEND_IP)
    udpsink.set_property("port", BACKEND_PORT)
    udpsink.set_property("sync", False)
    udpsink.set_property("async", False)

    elements = [
        rgb_src, rgb_caps, rgb_conv,
        thermal_src, thermal_caps, thermal_conv, thermal_conv_caps,
        mux, tee,
        inf_queue, inf_conv, inf_conv_caps, appsink,
        rtp_queue, encoder, rtp_payload, udpsink
    ]

    if any(e is None for e in elements):
        print("GSTREAMER ELEMENT FAILED TO GET CREATED!!!!!!!!!!!")

    # Add all of the elements to the pipeline
    pipeline.add(*elements)

    # Put rgb stuff on sink 0 of mux
    rgb_src.link(rgb_caps)
    rgb_caps.link(rgb_conv)
    rgb_src_pad = rgb_conv.get_static_pad("src")
    mux_sink_0 = mux.request_pad_simple("sink_0") # if this doesn't work, switch to get_request_pad
    rgb_src_pad.link(mux_sink_0)

    # Put termal stuff on sink 0 of mux
    thermal_src.link(thermal_caps)
    thermal_caps.link(thermal_conv)
    thermal_conv.link(thermal_conv_caps)
    thermal_src_pad = thermal_conv_caps.get_static_pad("src")
    mux_sink_1 = mux.request_pad_simple("sink_1")
    thermal_src_pad.link(mux_sink_1)

    # mux into the tee to split into the 2 branches
    mux.link(tee)

    # This goes tee to inf_queue to inf_conv to inf_conv_caps to appsink
    tee.link(inf_queue)
    inf_queue.link(inf_conv)
    inf_conv.link(inf_conv_caps)
    inf_conv_caps.link(appsink)

    # This goes tee to rtp_queue to encoder to rtp_payload to udpsink
    tee.link(rtp_queue)
    rtp_queue.link(encoder)
    encoder.link(rtp_payload)
    rtp_payload.link(udpsink)

    return pipeline, appsink

# This function is what actually makes the sample available to Python for inference
def on_new_sample(appsink):
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
        buffer.update(frame)  # just store latest frame
    finally:
        # NEED THIS IN THE FINALLY, OTHERWISE ITS GOING TO STAY MAPPED AND BAD MEMORY ISSUES WILL HAPPEN!!
        buf.unmap(map_info)

    return Gst.FlowReturn.OK

# Can't completely get rid of the bus, since this callback needs to match what GStreamer wants
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
    pipeline, appsink = build_gst_pipeline()

    appsink.connect("new-sample", on_new_sample)

    loop = GLib.MainLoop() # Switch to GObject.MainLoop() if unavailable
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
        # Stopped state
        pipeline.set_state(Gst.State.NULL)
        print("Ingestion stopped")

if __name__ == "__main__":
    main()
