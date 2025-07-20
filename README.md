# PDF Outline Extractor

## Overview
This project is a PDF processing solution developed for the Adobe India Hackathon 2025 Challenge 1a. It extracts structured outline data from PDF documents and outputs JSON files containing the document title and hierarchical outline information.

## Challenge Description
The solution addresses Challenge 1a requirements:
- **Objective**: Extract structured outline/table of contents from PDF documents
- **Input**: PDF files in `/app/input` directory (read-only)
- **Output**: JSON files with extracted title and outline structure
- **Constraints**: 
  - Execution time ≤ 10 seconds for 50-page PDFs
  - Model size ≤ 200MB (if using ML models)
  - No internet access during runtime
  - CPU-only execution (AMD64, 8 CPUs, 16GB RAM)
  - All libraries must be open source

## Features
- Automatic PDF text extraction using PyMuPDF
- Hierarchical outline detection and structuring
- JSON output conforming to specified schema
- Docker containerization for consistent deployment
- Optimized for performance within challenge constraints

## Project Structure
```
pdf-outline-extractor/
├── pdf_outline_extractor/  # Main package implementation
├── notebooks/              # Development and testing notebooks
├── benchmark/              # Performance benchmarking
├── pyproject.toml          # Project dependencies
├── uv.lock                 # Lock file for dependencies
├── Dockerfile              # Production Docker configuration
└── README.md               # This file
```


## Dependencies
- **Python**: ≥3.12
- **PyMuPDF**: PDF text extraction and processing
- **ipykernel**: Jupyter notebook support for development

## Output Format
The solution generates JSON files with the following structure:
```json
{
  "title": "Document Title",
  "outline": [
    {
      "level": "H1",
      "text": "Chapter 1: Introduction",
      "page": 1
    },
    {
      "level": "H2", 
      "text": "1.1 Overview",
      "page": 2
    }
  ]
}
```

### Schema Details
- **title**: String containing the document title
- **outline**: Array of outline items with:
  - **level**: Heading level (H1, H2, H3, etc.)
  - **text**: Heading text content
  - **page**: Page number where the heading appears

## Docker Usage

### Build
```bash
docker build --platform linux/amd64 -t pdf-outline-extractor .
```

### Run
```bash
docker run --rm \
  -v $(pwd)/input:/app/input:ro \
  -v $(pwd)/output:/app/output \
  --network none \
  pdf-outline-extractor
```

## Development

### Setup Environment
```bash
# Install dependencies with uv
uv sync

# Or with pip
pip install -e .
```

### Benchmarking
Performance benchmarks can be run from the `benchmark/` directory to ensure compliance with challenge constraints.

## Implementation Approach
1. **PDF Processing**: Uses PyMuPDF for efficient PDF text extraction
2. **Outline Detection**: Analyzes text formatting, font sizes, and structure to identify headings
3. **Hierarchy Building**: Creates hierarchical outline structure with appropriate levels
4. **JSON Generation**: Outputs structured data conforming to the required schema

## Performance Optimizations
- Efficient memory management for large PDFs
- Optimized text processing algorithms
- Minimal dependencies to reduce container size
- CPU-optimized processing for AMD64 architecture

## License
Open source - all libraries and tools used are open source compliant.

## Contributing
This project was developed for the Adobe India Hackathon 2025. Feel free to explore the implementation and suggest improvements.