FROM python:3.11-slim

WORKDIR /app

# Copy necessary files for pip install
COPY ./LICENSE ./LICENSE
COPY ./README.md ./README.md
COPY ./pyproject.toml ./pyproject.toml

# Create necessary directory structure
RUN mkdir -p src/whatsapp_mcp

# Copy the source code
COPY ./src/whatsapp_mcp ./src/whatsapp_mcp
COPY ./run.sh ./run.sh

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set the entry point
ENTRYPOINT ["python", "-m", "whatsapp_mcp.main"]
