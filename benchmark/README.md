# Benchmark

This directory contains benchmarking tools to ensure the PDF outline extractor meets the challenge constraints and validates extraction accuracy against ground truth data.

## Usage

### Basic Performance Benchmarking
```bash
# Benchmark PDFs in a directory (performance only)
python benchmark.py /path/to/pdfs

# With verbose logging
python benchmark.py /path/to/pdfs --verbose
```

### Save Results to File
```bash
# Save benchmark results to JSON file
python benchmark.py /path/to/pdfs --output results.json
python benchmark.py /path/to/pdfs -o results.json  # short form
```

### Accuracy Validation with Ground Truth
```bash
# Benchmark with ground truth validation
python benchmark.py /path/to/pdfs --ground-truth /path/to/ground_truth
python benchmark.py /path/to/pdfs -g /path/to/ground_truth  # short form

# Example with challenge sample data
python benchmark.py ../challenge/sample_dataset/pdfs/ -g ../challenge/sample_dataset/outputs/
```

### Complete Example
```bash
# Full benchmark with all options
python benchmark.py /path/to/pdfs --output results.json --ground-truth /path/to/ground_truth --verbose
```

### Help
```bash
# Show all available options
python benchmark.py --help
```

## Constraints Tested

- **Execution Time**: ≤ 10 seconds per 50-page PDF
- **Memory Usage**: Monitoring peak memory consumption
- **Success Rate**: Percentage of successfully processed files

## Accuracy Metrics (when ground truth provided)

- **Precision**: Ratio of correctly extracted outline items to total extracted items
- **Recall**: Ratio of correctly extracted outline items to total ground truth items
- **F1 Score**: Harmonic mean of precision and recall
- **Title Accuracy**: Percentage of correctly extracted document titles
- **Exact Matches**: Count of outline items matching exactly (text, level, page)
- **Partial Matches**: Count of outline items with similar text content

## Output

The benchmark script generates a JSON report with:
- Individual file processing times
- Memory usage statistics
- Constraint violation warnings
- Accuracy metrics (if ground truth provided)
- Summary statistics and quality assessment

## Ground Truth Format

Ground truth JSON files should be named identically to their corresponding PDF files:
- `document.pdf` → `document.json`

Expected JSON structure:
```json
{
  "title": "Document Title",
  "outline": [
    {
      "level": "H1",
      "text": "Chapter 1: Introduction",
      "page": 1
    }
  ]
}
```
