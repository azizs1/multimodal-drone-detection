# Multimodal Drone Detection
**Authors:** Chia-Yu Chang, Yu-Chieh Cheng, Li-Chieh Kung, Ethan Mauger, Aziz Shaik
**Course:** CS 5934: Capstone Design (Spring 2026)

This MEng capstone project aims to build a drone detection system with an AI-enabled multimodal approach.

## Prerequisites

### Python Package Manager: uv
This project uses [uv](https://github.com/astral-sh/uv) as the Python package manager for the backend, machine learning, and sensor ingestion components.

#### Installing uv

**macOS and Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Alternative (via pip):**
```bash
pip install uv
```

#### Using uv

After installing uv, navigate to the project directory and sync dependencies:

```bash
# Install dependencies from uv.lock
uv sync

# Install development dependencies
uv sync --dev

# Install only production dependencies
uv sync --no-dev
```

When running Python scripts, use `uv run`:
```bash
uv run python your_script.py
```

For package-specific commands:
```bash

cd backend

# Run the backend server
uv run uvicorn backend.src.app.main:app --reload

# Run tests
uv run pytest
```

## How to Use
This repository essentially contains three smaller repositories within it, separated based on the container that the components will be running on. Two containers, `frontend` and `backend` run on <WHERE DO THESE RUN, PROBS LAPTOP>, while the machine learning and sensor ingestion both run within the same container on a Jetson Nano.

### Frontend
#### Development
\<how to initialize this for dev\>
#### Deployment
\<how to deploy the docker container for this\>

### Backend
Backend requires `uv` for dependency management.

#### Development
1. Install uv (see Prerequisites above)
2. Navigate to the backend directory:
   ```bash
   cd backend
   ```
3. Install dependencies:
   ```bash
   uv sync --no-dev
   ```
4. Run the development server:
   ```bash
   uv run uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
   ```

#### Deployment
Build and run the Docker container from the repository root:
```bash
docker build -t drone-detection-backend -f backend/Dockerfile .
docker run -p 8000:8000 drone-detection-backend
```

### Jetson
Jetson components require `uv` for dependency management.

#### Development
1. Install uv (see Prerequisites above)
2. Navigate to the jetson directory:
   ```bash
   cd jetson
   ```
3. Install dependencies:
   ```bash
   uv sync
   ```
4. Run the components:
   ```bash
   uv run python src/run_both.py
   ```

#### Deployment
\<how to deploy the docker container for this\>
