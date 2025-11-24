FROM python:3.12-slim-bookworm

# 1. Set pip timeout (fixes ReadTimeout)
ENV PIP_DEFAULT_TIMEOUT=120

# 2. Install system dependencies (OpenCV, tgcrypto, numpy need these)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    wget \
    ffmpeg \
    bash \
    neofetch \
    software-properties-common \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libatlas-base-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 3. Copy requirements
COPY requirements.txt .

# 4. Install python deps with retries + mirror
RUN pip3 install --upgrade pip wheel \
    && pip3 install --no-cache-dir --retries 10 --timeout 120 \
       -i https://pypi.org/simple \
       -r requirements.txt

# 5. App directory
WORKDIR /app
COPY . .

EXPOSE 8000

CMD flask run -h 0.0.0.0 -p 8000 & python3 -m Safe_repo
