# --- STAGE 1: Build Dependencies ---
FROM python:3.12-slim AS builder

WORKDIR /app

# Prevent Python from writing .pyc files to disk and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies needed to build packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies into a local directory
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# --- STAGE 2: Runtime Production Image ---
FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy only the compiled packages from the builder stage
COPY --from=builder /root/.local /root/.local
COPY . .

# Ensure the paths are set correctly to find our installed modules
ENV PATH=/root/.local/bin:$PATH

# Expose the internal port FastAPI will run on
EXPOSE 8000

# Run the app using Uvicorn (configured for production container listening)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
