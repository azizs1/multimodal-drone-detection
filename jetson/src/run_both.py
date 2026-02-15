import subprocess

# rename these as we actually build them out
for proc in [
    subprocess.Popen(["uv", "run", "python3", "-m", "sensor_ingestion.ingest"]), 
    subprocess.Popen(["uv", "run", "python3", "-m", "ml.inference"])]:
    proc.wait()

# update this using proc.poll() here so that we can monitor each process