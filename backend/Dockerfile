FROM python:3.12-slim

WORKDIR /app

# Copy project metadata and lock file from repository root
COPY backend/pyproject.toml ./pyproject.toml
COPY uv.lock ./uv.lock

# Install dependencies using uv
RUN pip install uv && uv sync --no-dev

# Copy application source code
COPY backend/src ./

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]