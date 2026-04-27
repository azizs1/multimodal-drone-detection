import os
import shutil
import socket
import subprocess
import time


def cleanup(procs):
    print("\nShutting down all components...")
    for name in list(procs.keys()):
        proc = procs[name]
        if proc.poll() is None:
            print(f"Stopping {name}...")
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                print(f"{name} forced kill.")
                proc.kill()


def wait_for_port(port, host="localhost", timeout=10):
    start_time = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except (ConnectionRefusedError, OSError):
            if time.time() - start_time > timeout:
                return False
            time.sleep(0.5)


def main():
    # clean up possible lingering zeromq sockets
    if os.path.exists("/tmp/frames_bus"):
        os.remove("/tmp/frames_bus")

    gst_cache = os.path.expanduser("~/.cache/gstreamer-1.0")
    if os.path.exists(gst_cache):
        shutil.rmtree(gst_cache)

    procs = {}

    env = os.environ.copy()
    source_mode = env.get("INFERENCE_SOURCE", "stream").lower()
    run_ingestion = source_mode != "videos"
    print(f"run mode: {source_mode}")
    print(f"ingestion enabled: {run_ingestion}")

    procs["mediamtx"] = subprocess.Popen(["/app/mediamtx"])
    print("Waiting for MediaMTX to accept connections on port 8554...")
    if not wait_for_port(8554):
        print("ERROR: MediaMTX failed to start")
        cleanup(procs)
        return

    if run_ingestion:
        procs["ingestion"] = subprocess.Popen(["python3", "-m", "sensor_ingestion.ingest_gi"], env=env)
    procs["fusion"] = subprocess.Popen(["python3", "-m", "ml.fusion_service"], env=env)
    procs["inference"] = subprocess.Popen(["python3", "-m", "ml.inference"], env=env)

    try:
        while procs:
            for name, proc in list(procs.items()):
                ret = proc.poll()

                # this is if the process is still running fine
                if ret is None:
                    continue

                print(f"{proc} exited. code: {ret}")
                proc.wait()

                # we want to stop everything if ingestion dies, but if inference dies,
                # keep going so we can at least continue streaming sensors.
                # fusion and inference can restart independently in future iterations.
                if name == "mediamtx":
                    # MediaMTX dying is fatal
                    procs.clear()
                    cleanup(procs)
                    break
                elif name == "ingestion" and run_ingestion:
                    # restart ingestion if it dies
                    procs["ingestion"] = subprocess.Popen(
                        ["python3", "-m", "sensor_ingestion.ingest_gi"], env=env
                    )
                    continue
                else:
                    del procs[name]
                    continue

            if not procs:
                break
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup(procs)


if __name__ == "__main__":
    main()
