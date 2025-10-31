# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system deps (for instagrapi)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg-dev zlib1g-dev libssl-dev libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Create downloads folder
RUN mkdir -p downloads

RUN touch session.json

# Run the bot
CMD ["python", "bot.py"]
