import os
import json
from typing import List
import logging
import time

from .pdf_parser import extract_text_blocks_with_features
from .pdf_features import TextBlock
from . import heading_rules

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def apply_heuristic_rules_and_classify(blocks: List[TextBlock]) -> List[TextBlock]:
    for block in blocks:
        is_definitely_not_heading = False
        for rule_func in heading_rules.NEGATIVE_HEADING_INDICATORS:
            if rule_func(block):
                is_definitely_not_heading = True
                break

        if is_definitely_not_heading:
            block.potential_heading_level = "Body"
            continue

        is_heading_candidate = False
        if (heading_rules.heading_if_strong_candidate(block) or
            (heading_rules.heading_if_bold(block) and heading_rules.heading_if_larger_font(block)) or
            heading_rules.heading_if_starts_with_number_pattern(block) or
            heading_rules.heading_if_distinct_spacing(block)):
            is_heading_candidate = True

        if is_heading_candidate:
            block.potential_heading_level = "Heading"
        else:
            block.potential_heading_level = "Body"

        if block.page_number == 1 and block.relative_font_size_to_avg is not None and \
           block.relative_font_size_to_avg > 2.5 and block.is_bold and block.bbox[1] < 100:
            block.potential_heading_level = "Title"

    return blocks

def generate_output(text_blocks: List[TextBlock]) -> dict:
    title = "Untitled Document"
    outline = []

    for block in text_blocks:
        if block.potential_heading_level == "Title":
            title = block.text_content
            break

    for block in text_blocks:
        if block.potential_heading_level == "Heading":
            outline.append({
                "text": block.text_content,
                "level": "",
                "page": block.page_number
            })
    return {
        "title": title,
        "outline": outline
    }

def process_pdf(input_pdf_path: str, output_json_path: str):
    logging.info(f"Processing PDF: {input_pdf_path}")
    start_time = time.time()

    try:
        extracted_blocks = extract_text_blocks_with_features(input_pdf_path)
        logging.info(f"Extracted {len(extracted_blocks)} text blocks from {input_pdf_path}.")

        classified_blocks = apply_heuristic_rules_and_classify(extracted_blocks)
        logging.info("Applied heuristic rules for heading detection.")

        final_output_json = generate_output(classified_blocks)
        logging.info("Generated final JSON output structure (Headings marked as H_GENERIC).")

        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(final_output_json, f, indent=2)
        logging.info(f"Saved output to: {output_json_path}")

    except Exception as e:
        logging.error(f"Error processing {input_pdf_path}: {e}")

    end_time = time.time()
    execution_time = end_time - start_time
    logging.info(f"Finished processing {input_pdf_path} in {execution_time:.2f} seconds.")

    if execution_time > 10:
        logging.warning(f"Execution time ({execution_time:.2f}s) exceeded 10-second limit for {input_pdf_path}.")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    INPUT_DIR = os.getenv('INPUT_DIR', '/app/input')
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', '/app/output')

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    logging.info(f"Monitoring input directory: {INPUT_DIR}")
    logging.info(f"Outputting to directory: {OUTPUT_DIR}")

    if not os.path.exists(INPUT_DIR) or not os.listdir(INPUT_DIR):
        logging.warning(f"Input directory '{INPUT_DIR}' is empty or does not exist. Creating a dummy PDF for testing.")
        dummy_pdf_path = os.path.join(INPUT_DIR, "sample_document.pdf")
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 75), "Connecting the Dots Challenge Document", fontname="helv", fontsize=24, color=(0, 0, 0))
        page.insert_text((50, 120), "1. Introduction to the Hackathon", fontname="helv-bold", fontsize=18, color=(0, 0, 0))
        page.insert_text((50, 150), "Welcome to the Adobe India Hackathon. This document outlines the challenges for Round 1.", fontname="helv", fontsize=10, color=(0, 0, 0))
        page.insert_text((50, 165), "Your mission is to reimagine the humble PDF.", fontname="helv", fontsize=10, color=(0, 0, 0))
        page.insert_text((70, 200), "1.1 Round 1A: Outline Extraction", fontname="helv-bold", fontsize=14, color=(0, 0, 0))
        page.insert_text((70, 220), "The first part involves extracting a structured outline.", fontname="helv", fontsize=10, color=(0, 0, 0))
        page.insert_text((90, 250), "1.1.1 Required Output Format", fontname="helv-bold", fontsize=12, color=(0, 0, 0))
        page.insert_text((90, 270), "The output must be a valid JSON file.", fontname="helv", fontsize=10, color=(0, 0, 0))
        page2 = doc.new_page()
        page2.insert_text((50, 75), "2. Docker Requirements", fontname="helv-bold", fontsize=18, color=(0, 0, 0))
        page2.insert_text((50, 100), "Your solution must be compatible with AMD64 architecture.", fontname="helv", fontsize=10, color=(0, 0, 0))
        doc.save(dummy_pdf_path)
        doc.close()
        logging.info(f"Dummy PDF created at: {dummy_pdf_path}")

    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith(".pdf"):
            input_pdf_path = os.path.join(INPUT_DIR, filename)
            output_json_filename = filename.replace(".pdf", ".json")
            output_json_path = os.path.join(OUTPUT_DIR, output_json_filename)
            process_pdf(input_pdf_path, output_json_path)

    logging.info("All PDFs processed.")
