"""
Example script showing how to process PDFs and generate JSON output matching the required format.
"""
import os
import json
from pdf_outline_extractor.main import PDFOutlineExtractor

def process_pdfs_to_json():
    """Process PDFs and save results in the required JSON format."""
    extractor = PDFOutlineExtractor()
    
    # Input and output directories
    input_dir = "challenge/sample_dataset/pdfs"
    output_dir = "output"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Process all PDF files in the input directory
    if os.path.exists(input_dir):
        for filename in os.listdir(input_dir):
            if filename.lower().endswith('.pdf'):
                pdf_path = os.path.join(input_dir, filename)
                output_filename = filename.replace('.pdf', '.json')
                output_path = os.path.join(output_dir, output_filename)
                
                print(f"Processing: {filename}")
                
                try:
                    # Extract outline
                    result = extractor.extract_outline(pdf_path)
                    
                    # Save to JSON file
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)
                    
                    print(f"  ✓ Saved to: {output_path}")
                    print(f"  Title: {result['title']}")
                    print(f"  Outline items: {len(result['outline'])}")
                    
                except Exception as e:
                    print(f"  ✗ Error: {e}")
    else:
        print(f"Input directory not found: {input_dir}")

if __name__ == "__main__":
    process_pdfs_to_json()
