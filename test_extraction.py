"""
Test script for the rule-based PDF outline extractor.
"""
import os
import json
from pdf_outline_extractor.main import PDFOutlineExtractor

def test_pdf_extraction():
    """Test the PDF extraction with sample files."""
    extractor = PDFOutlineExtractor()
    
    # Test with sample PDF files if they exist
    test_files = [
        "challenge/sample_dataset/pdfs/file01.pdf",
        "challenge/sample_dataset/pdfs/file02.pdf"
    ]
    
    for pdf_file in test_files:
        if os.path.exists(pdf_file):
            print(f"\nProcessing: {pdf_file}")
            try:
                result = extractor.extract_outline(pdf_file)
                print(f"Title: {result['title']}")
                print(f"Outline items: {len(result['outline'])}")
                
                for item in result['outline']:
                    print(f"  {item['level']}: {item['text']} (page {item['page']})")
                    
            except Exception as e:
                print(f"Error processing {pdf_file}: {e}")
        else:
            print(f"File not found: {pdf_file}")

if __name__ == "__main__":
    test_pdf_extraction()
