# Use Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen

# Copy application code
COPY . .

# Create directory for database if it doesn't exist
RUN mkdir -p /app/data

# Run the bot
CMD ["uv", "run", "python", "main.py"]