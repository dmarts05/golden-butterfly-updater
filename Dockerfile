FROM ghcr.io/astral-sh/uv:python3.13-bookworm

# Enable bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1

# Install system dependencies, Chrome, and xvfb in a single layer to reduce image size
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    gnupg2 \
    xvfb \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency lock files first to leverage Docker cache
COPY pyproject.toml uv.lock /app/

# Install dependencies without the project source code
RUN uv sync --frozen --no-install-project

# Copy the rest of the application
COPY . /app

# Install the project itself
RUN uv sync --frozen

# Run the application
CMD ["uv", "run", "python", "-m", "golden_butterfly_updater"]