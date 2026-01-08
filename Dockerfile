FROM ghcr.io/astral-sh/uv:python3.13-bookworm

# Install Google Chrome and xvfb
RUN apt update && apt install -y \
    wget \
    unzip \
    gnupg2
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list
RUN apt update && apt install -y \
    google-chrome-stable \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy current directory contents to container at /app
COPY . /app

# Install dependencies
RUN uv sync --frozen

# Run app
CMD ["uv", "run", "python", "-m", "winamax_farmer"]