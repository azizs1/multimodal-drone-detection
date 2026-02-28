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

from sensor_ingestion import buffer

latest_rgb = None
latest_thermal = None

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
    rgb_tee = Gst.ElementFactory.make("tee", "rgb_tee")

    # RGB into inference
    rgb_inf_queue = Gst.ElementFactory.make("queue", "rgb_inf_queue")
    rgb_inf_conv = Gst.ElementFactory.make("nvvideoconvert", "rgb_inf_conv") # NV12 to BGR
    rgb_inf_caps = Gst.ElementFactory.make("capsfilter", "rgb_inf_caps")
    rgb_inf_caps.set_property("caps", Gst.Caps.from_string("video/x-raw,format=BGR"))
    rgb_appsink = Gst.ElementFactory.make("appsink", "rgb_appsink")
    rgb_appsink.set_property("emit-signals", True)
    rgb_appsink.set_property("sync", False)
    rgb_appsink.set_property("max-buffers", 1)
    rgb_appsink.set_property("drop", True)

    # RTP stream udpsink to stream RGB to backend
    rgb_rtp_queue = Gst.ElementFactory.make("queue", "rgb_rtp_queue")
    rgb_encoder = Gst.ElementFactory.make("nvv4l2h264enc", "rgb_encoder") # H.264 encoder
    rgb_encoder.set_property("bitrate", 4000000) # 4Mbps for now? change later
    rgb_rtp_payload = Gst.ElementFactory.make("rtph264pay", "rgb_rtp_payload")
    rgb_rtp_payload.set_property("config-interval", 1)
    rgb_rtp_payload.set_property("pt", 96) # Payload type for H.264 rtp streams
    rgb_udpsink = Gst.ElementFactory.make("udpsink", "rgb_udpsink")
    rgb_udpsink.set_property("host", BACKEND_IP)
    rgb_udpsink.set_property("port", BACKEND_PORT)
    rgb_udpsink.set_property("sync", False)
    rgb_udpsink.set_property("async", False)

    # Thermal caps and conv (raw video at 320x240 in GRAY16_LE at 30FPS)
    thermal_caps = Gst.ElementFactory.make("capsfilter", "thermal_caps")
    thermal_caps.set_property("caps", Gst.Caps.from_string("video/x-raw,width=320,height=240,format=GRAY16_LE,framerate=30/1"))
    thermal_conv = Gst.ElementFactory.make("nvvidconv", "thermal_conv") # convert to NV12+NVMM

    thermal_tee = Gst.ElementFactory.make("tee", "thermal_tee")

    # thermal into inference
    thermal_inf_queue = Gst.ElementFactory.make("queue", "thermal_inf_queue")
    thermal_appsink = Gst.ElementFactory.make("appsink", "thermal_appsink")
    thermal_appsink.set_property("emit-signals", True)
    thermal_appsink.set_property("sync", False)
    thermal_appsink.set_property("max-buffers", 1)
    thermal_appsink.set_property("drop", True)

    # RTP stream udpsink to stream thermal to backend
    thermal_rtp_queue = Gst.ElementFactory.make("queue", "thermal_rtp_queue")
    thermal_encoder = Gst.ElementFactory.make("nvv4l2h264enc", "thermal_encoder") # H.264 encoder
    thermal_encoder.set_property("bitrate", 4000000) # 4Mbps for now? change later
    thermal_rtp_payload = Gst.ElementFactory.make("rtph264pay", "thermal_rtp_payload")
    thermal_rtp_payload.set_property("config-interval", 1)
    thermal_rtp_payload.set_property("pt", 96)
    thermal_udpsink = Gst.ElementFactory.make("udpsink", "thermal_udpsink")
    thermal_udpsink.set_property("host", BACKEND_IP)
    thermal_udpsink.set_property("port", BACKEND_PORT+1)
    thermal_udpsink.set_property("sync", False)
    thermal_udpsink.set_property("async", False)

    elements = [
        rgb_src, rgb_caps, rgb_conv, rgb_tee,
        rgb_inf_queue, rgb_inf_conv, rgb_inf_caps, rgb_appsink,
        rgb_rtp_queue, rgb_encoder, rgb_rtp_payload, rgb_udpsink,
        thermal_src, thermal_caps, thermal_conv, thermal_tee,
        thermal_inf_queue, thermal_appsink,
        thermal_rtp_queue, thermal_encoder, thermal_rtp_payload, thermal_udpsink
    ]

    # Add all of the elements to the pipeline
    for e in elements:
        if e is None:
            print("GSTREAMER ELEMENT FAILED TO GET CREATED!!!!!!!!!!!")
        else:
            pipeline.add(e)

    # Linking RGB stuff
    rgb_src.link(rgb_caps)
    rgb_caps.link(rgb_conv)
    rgb_conv.link(rgb_tee)
    
    rgb_tee.link(rgb_inf_queue)
    rgb_inf_queue.link(rgb_inf_conv)
    rgb_inf_conv.link(rgb_inf_caps)
    rgb_inf_caps.link(rgb_appsink)

    rgb_tee.link(rgb_rtp_queue)
    rgb_rtp_queue.link(rgb_encoder)
    rgb_encoder.link(rgb_rtp_payload)
    rgb_rtp_payload.link(rgb_udpsink)

    # Linking thermal stuff
    thermal_src.link(thermal_caps)
    thermal_caps.link(thermal_conv)
    thermal_conv.link(thermal_tee)
    
    thermal_tee.link(thermal_inf_queue)
    thermal_inf_queue.link(thermal_appsink)

    thermal_tee.link(thermal_rtp_queue)
    thermal_rtp_queue.link(thermal_encoder)
    thermal_encoder.link(thermal_rtp_payload)
    thermal_rtp_payload.link(thermal_udpsink)

    return pipeline, rgb_appsink, thermal_appsink

def update_buffer():
    global latest_rgb, latest_thermal

    if latest_rgb is not None and latest_thermal is not None:
        timestamp = GLib.get_monotonic_time()
        buffer.update(timestamp, latest_rgb, latest_thermal)

# This function is what actually makes the RGB sample available to Python for inference
def on_new_rgb_sample(appsink):
    global latest_rgb

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
        update_buffer()
    finally:
        # NEED THIS IN THE FINALLY, OTHERWISE ITS GOING TO STAY MAPPED AND BAD MEMORY ISSUES WILL HAPPEN!!
        buf.unmap(map_info)

    return Gst.FlowReturn.OK

# This function is what actually makes the thermal sample available to Python for inference
def on_new_thermal_sample(appsink):
    global latest_thermal
    
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
        frame = np.frombuffer(map_info.data, dtype=np.uint16) # format is GRAY16_LE so 16bit
        frame = frame.reshape((height, width))
        update_buffer()
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
    pipeline, rgb_appsink, thermal_appsink = build_gst_pipeline()

    rgb_appsink.connect("new-sample", on_new_rgb_sample)
    thermal_appsink.connect("new-sample", on_new_thermal_sample)

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
