import subprocess
import time

procs = {
    "ingestion": subprocess.Popen(["uv", "run", "python3", "-m", "sensor_ingestion.ingest_gi"]),
    "inference": subprocess.Popen(["uv", "run", "python3", "-m", "ml.inference"])
}

while True:
    for name, proc in procs.items():
        ret = proc.poll()
        
        # This is if the process is still running fine
        if ret is None:
            continue

        print(f"{proc} exited. code: {ret}")

        # We want to stop everything if ingestion dies, but if inference dies,
        # keep going so we can at least continue streaming sensors
        if name == "inference":
            del procs["inference"]
            continue
        elif name == "ingestion":
            del procs["ingestion"]
            break
    
    if not procs:
        break
    time.sleep(1)
