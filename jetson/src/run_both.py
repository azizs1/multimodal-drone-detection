import subprocess
import time

procs = {
    "ingestion": subprocess.Popen(["uv", "run", "python3", "-m", "sensor_ingestion.ingest_gi"]),
    "fusion": subprocess.Popen(["uv", "run", "python3", "-m", "ml.fusion_service"]),
    "inference": subprocess.Popen(["uv", "run", "python3", "-m", "ml.inference"]),
}

while True:
    for name, proc in list(procs.items()):
        ret = proc.poll()

        # This is if the process is still running fine
        if ret is None:
            continue

        print(f"{proc} exited. code: {ret}")

        # We want to stop everything if ingestion dies, but if inference dies,
        # keep going so we can at least continue streaming sensors.
        # Fusion and inference can restart independently in future iterations.
        if name in {"inference", "fusion"}:
            del procs[name]
            continue
        elif name == "ingestion":
            del procs["ingestion"]
            break

    if not procs:
        break
    time.sleep(1)
