FROM python:3.12-slim

WORKDIR /app

# Copy project metadata and lock file
COPY pyproject.toml ./pyproject.toml

# Install dependencies using uv
RUN pip install uv && uv sync --no-dev

# Copy application source code
COPY src ./

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]