# Use a lightweight Python base image
FROM python:3.11-slim

# Install system dependencies (Crucial for cfgrib/eccodes C-libraries)
RUN apt-get update && apt-get install -y \
    libeccodes0 \
    libeccodes-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (lightning-fast package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh

# Set the working directory
WORKDIR /app

# Hugging Face Spaces require apps to run on port 7860 by default.
# The app.main:start function already reads the $PORT env var.
ENV PORT=7860
EXPOSE 7860

# Hugging Face Spaces run Docker containers as a non-root user (id 1000)
# We must create this user and give them ownership of the app directory.
RUN useradd -m -u 1000 user && chown -R user:user /app
USER user

# Copy dependency files first (this caches the installation layer)
COPY --chown=user:user pyproject.toml uv.lock ./

# Install dependencies (without pytest, etc.)
RUN uv sync --no-dev --frozen

# Copy the rest of the backend code and the trained weights
COPY --chown=user:user . .

# Run the production server using uv
CMD ["uv", "run", "start"]
