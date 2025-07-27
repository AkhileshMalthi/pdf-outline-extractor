# pdf_parser.py
from typing import List, Optional
import fitz  # PyMuPDF
import re # For regex operations

# Import the TextBlock and other feature models from the separate file
from .pdf_features import TextBlock
from pprint import pprint

def get_hex_color(rgb_int: int) -> Optional[str]:
    """Converts an integer RGB color to a hex string. Handles None input."""
    if rgb_int is None:
        return None
    # PyMuPDF's colors are usually 0xRRGGBB, so convert to hex
    return f"#{rgb_int:06x}"

def extract_text_blocks_with_features(pdf_path: str) -> List[TextBlock]:
    """
    Parses a PDF and extracts text blocks with their features.
    This function performs a single pass to get most features and then
    a second pass for contextual features.
    """
    document = fitz.open(pdf_path)
    all_text_blocks: List[TextBlock] = []

    for page_number, page in enumerate(document, start=1):
        page_dict = page.get_text("dict")
        blocks_on_page = page_dict.get("blocks", [])

        current_page_text_blocks: List[TextBlock] = []
        page_font_sizes = []

        for b in blocks_on_page:
            if b['type'] == 0:  # This is a text block
                for line in b.get("lines", []):
                    full_line_text = ""
                    line_spans = line.get("spans", [])

                    if not line_spans: # Skip empty lines
                        continue

                    for span in line_spans:
                        full_line_text += span["text"]

                    stripped_text = full_line_text.strip()
                    if not stripped_text: # Skip lines that are just whitespace
                        continue

                    # Use properties from the first span for the whole 'line' block
                    first_span = line_spans[0]

                    # Text Content Features
                    text_content = stripped_text
                    num_words = len(text_content.split())
                    num_characters = len(text_content)
                    is_all_caps = text_content.isupper() and len(text_content) > 1 # Avoid single chars
                    is_title_case = text_content.istitle()
                    starts_with_number_pattern = bool(
                        re.match(r"^\s*(\d+(\.\d+)*|\w+\.)\s+", text_content)
                    )
                    starts_with_bullet = bool(re.match(r"^\s*[-•*§]\s+", text_content)) # Added common bullet chars
                    ends_with_punctuation = text_content.endswith(('.', '!', '?', ','))
                    has_leading_whitespace = full_line_text != full_line_text.lstrip()
                    has_trailing_whitespace = full_line_text != full_line_text.rstrip()


                    # Font Features
                    font_size = first_span["size"]
                    page_font_sizes.append(font_size)
                    font_name = first_span["font"]
                    # More robust check for bold/italic - look for typical keywords
                    is_bold = "bold" in font_name.lower() or "black" in font_name.lower() or "heavy" in font_name.lower()
                    is_italic = "italic" in font_name.lower() or "oblique" in font_name.lower() or "kursiv" in font_name.lower()
                    font_color = get_hex_color(first_span["color"])

                    # Layout Features
                    line_bbox = list(line["bbox"])
                    # A more robust line_height estimate might require comparing y-coords of successive lines
                    # For now, a common multiplier or avg span height.
                    line_height = line_bbox[3] - line_bbox[1] # Height of the bbox itself
                    if line_height < font_size * 0.5: # Correct for very small measured heights
                        line_height = font_size * 1.2 # Fallback to heuristic

                    indentation = line_bbox[0]
                    # Heuristic: Check if x0 is close to the typical left margin.
                    # This threshold might need tuning for different document types.
                    is_left_aligned = indentation < (page.rect.width * 0.15) # Within 15% of page width from left

                    text_block_instance = TextBlock(
                        text_content=text_content,
                        page_number=page_number,
                        font_size=font_size,
                        is_bold=is_bold,
                        is_italic=is_italic,
                        font_name=font_name,
                        font_color=font_color,
                        bbox=line_bbox,
                        line_height=line_height,
                        num_lines=1, # Each TextBlock currently represents one line from PyMuPDF
                        indentation=indentation,
                        is_left_aligned=is_left_aligned,
                        num_words=num_words,
                        num_characters=num_characters,
                        starts_with_number_pattern=starts_with_number_pattern,
                        starts_with_bullet=starts_with_bullet,
                        ends_with_punctuation=ends_with_punctuation,
                        is_all_caps=is_all_caps,
                        is_title_case=is_title_case,
                        has_leading_whitespace=has_leading_whitespace,
                        has_trailing_whitespace=has_trailing_whitespace,
                    )
                    current_page_text_blocks.append(text_block_instance)

        # --- Second Pass for Contextual Features (per page) ---
        if current_page_text_blocks:
            avg_font_size_on_page = sum(page_font_sizes) / len(page_font_sizes) if page_font_sizes else 0

            for i, current_block in enumerate(current_page_text_blocks):
                if avg_font_size_on_page > 0:
                    current_block.relative_font_size_to_avg = current_block.font_size / avg_font_size_on_page

                # Calculate vertical spacing and visual distinctness relative to surrounding blocks
                if i > 0:
                    prev_block = current_page_text_blocks[i-1]
                    # space_before: bottom of previous to top of current
                    current_block.space_before = current_block.bbox[1] - prev_block.bbox[3]
                    # Heuristic for distinctness: large gap OR significant font size/boldness change
                    if (current_block.space_before > current_block.font_size * 0.8 or
                        abs(current_block.font_size - prev_block.font_size) > (prev_block.font_size * 0.2) or # More than 20% diff
                        current_block.is_bold != prev_block.is_bold):
                        current_block.is_visually_distinct_from_prev = True
                    else:
                        current_block.is_visually_distinct_from_prev = False

                if i < len(current_page_text_blocks) - 1:
                    next_block = current_page_text_blocks[i+1]
                    # space_after: bottom of current to top of next
                    current_block.space_after = next_block.bbox[1] - current_block.bbox[3]
                    # Similar distinctness check for the next block
                    if (current_block.space_after > current_block.font_size * 0.8 or
                        abs(current_block.font_size - next_block.font_size) > (next_block.font_size * 0.2) or
                        current_block.is_bold != next_block.is_bold):
                        current_block.is_visually_distinct_from_next = True
                    else:
                        current_block.is_visually_distinct_from_next = False

        all_text_blocks.extend(current_page_text_blocks)

    document.close()
    return all_text_blocks

if __name__ == "__main__":
    # Example usage with file02.pdf

    pdf_path = "d:/Competitions/pdf-outline-extractor/challenge/sample_dataset/pdfs/file02.pdf"
    blocks = extract_text_blocks_with_features(pdf_path)
    # Print summary of first 10 blocks
    for block in blocks[:10]:
        pprint(block.model_dump())