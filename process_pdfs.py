#!/usr/bin/env python3
"""
PDF Outline Extractor - Main Processing Script

This script processes PDF files from /app/input directory and generates
JSON files with extracted outlines in /app/output directory.

For Adobe India Hackathon 2025 - Challenge 1a
"""

import json
import logging
from pathlib import Path

from pdf_outline_extractor import PDFOutlineExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_pdfs() -> None:
    """
    Main processing function that extracts outlines from all PDFs in input directory.
    """
    input_dir = Path("challenge/sample_dataset/pdfs")
    output_dir = Path("output")
    
    # Ensure directories exist
    if not input_dir.exists():
        logger.error(f"Input directory {input_dir} does not exist")
        return
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize the extractor
    extractor = PDFOutlineExtractor()
    
    # Get all PDF files
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning("No PDF files found in input directory")
        return
        
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    # Process each PDF
    processed_count = 0
    for pdf_file in pdf_files:
        try:
            logger.info(f"Processing {pdf_file.name}")
            
            # Extract outline
            result = extractor.extract_outline(pdf_file)
            
            # Create output JSON file
            output_file = output_dir / f"{pdf_file.stem}.json"
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ {pdf_file.name} -> {output_file.name}")
            processed_count += 1
            
        except Exception as e:
            logger.error(f"✗ Failed to process {pdf_file.name}: {e}")
            continue
    
    logger.info(f"Processing complete: {processed_count}/{len(pdf_files)} files processed successfully")


if __name__ == "__main__":
    logger.info("Starting PDF outline extraction")
    process_pdfs()
    logger.info("PDF outline extraction completed")
