# Use python slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY server_manager.py .
COPY bot.py .

# Command to run the bot
CMD ["python", "bot.py"]
