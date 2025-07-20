FROM --platform=linux/amd64 python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PyMuPDF
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install uv for fast package management
RUN pip install uv

# Install dependencies
RUN uv sync --frozen

# Copy source code
COPY pdf_outline_extractor/ ./pdf_outline_extractor/

# Copy main processing script
COPY process_pdfs.py ./

# Create necessary directories
RUN mkdir -p /app/input /app/output

# Run the PDF processing script
CMD ["uv", "run", "python", "process_pdfs.py"]
