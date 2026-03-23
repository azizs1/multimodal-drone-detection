import subprocess
import time
import os

# clean up possible lingering zeromq sockets
if os.path.exists("/tmp/frame_bus"):
    os.remove("/tmp/frame_bus")

procs = {
    "ingestion": subprocess.Popen(["uv", "run", "python3", "-m", "sensor_ingestion.ingest_gi"]),
    "fusion": subprocess.Popen(["uv", "run", "python3", "-m", "ml.fusion_service"]),
    "inference": subprocess.Popen(["uv", "run", "python3", "-m", "ml.inference"]),
}

def cleanup():
    print("shutting down all components...")
    for _, proc in procs.items():
        if proc.poll() is None:
            proc.terminate()
    print("cleanup finished")

try:
    while procs:
        for name, proc in list(procs.items()):
            ret = proc.poll()

            # This is if the process is still running fine
            if ret is None:
                continue

            print(f"{proc} exited. code: {ret}")
            proc.wait()

            # We want to stop everything if ingestion dies, but if inference dies,
            # keep going so we can at least continue streaming sensors.
            # Fusion and inference can restart independently in future iterations.
            if name == "ingestion":
                procs.clear()
                cleanup()
                break
            else:
                del procs[name]
                continue

        if not procs:
            break
        time.sleep(1)
except KeyboardInterrupt:
    cleanup()