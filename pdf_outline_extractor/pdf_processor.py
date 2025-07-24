import fitz  # PyMuPDF
import re
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import logging
from collections import Counter
from dataclasses import dataclass
from .rule_evaluator import RuleEvaluator

logger = logging.getLogger(__name__)


@dataclass
class TextBlock:
    """Represents a text block with its properties."""
    text: str
    font_size: float
    font_name: str
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    page_num: int
    is_bold: bool = False
    is_italic: bool = False


class PDFProcessor:
    """
    Robust rule-based PDF processor for extracting titles and headings.
    """
    
    def __init__(self, custom_thresholds: Optional[Dict[str, float]] = None):
        """Initialize the PDF processor with rule evaluator."""
        self.rule_evaluator = RuleEvaluator(custom_thresholds)
        self.min_font_size = 8.0
        self.max_font_size = 72.0
        
    def get_lines_with_full_details(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extracts detailed information for each text line in a PDF document.
        
        Args:
            pdf_path: The path to the PDF file.
            
        Returns:
            List of dictionaries with line features and metadata.
        """
        document = fitz.open(pdf_path)
        all_lines_details = []
        
        # Initialize previous line data for calculating space_above
        prev_line_bbox = None
        prev_line_page = -1
        
        for page_num in range(len(document)):
            page = document.load_page(page_num)
            blocks = page.get_text("dict")["blocks"]
            page_height = page.rect.height
            page_width = page.rect.width
            
            # Sort blocks by their top-left Y-coordinate first, then X-coordinate
            blocks.sort(key=lambda b: (b["bbox"][1], b["bbox"][0]))
            
            for block in blocks:
                if block["type"] == 0:  # Text block
                    lines = sorted(block["lines"], key=lambda line_item: line_item["bbox"][1])
                    
                    for line in lines:
                        line_text = ""
                        font_sizes = []
                        font_names = []
                        is_bold_flag = False
                        
                        for span in line["spans"]:
                            line_text += span["text"]
                            font_sizes.append(span["size"])
                            font_names.append(span["font"])
                            
                            if "bold" in span["font"].lower() or (span["flags"] & 16):  # 16 is bold flag
                                is_bold_flag = True
                        
                        cleaned_text = line_text.strip()
                        if not cleaned_text:
                            continue
                        
                        dominant_font_size = np.median(font_sizes) if font_sizes else None
                        current_line_bbox = line["bbox"]
                        
                        space_above = 0
                        if prev_line_bbox and prev_line_page == page_num:
                            space_above = current_line_bbox[1] - prev_line_bbox[3]
                            if space_above < 0:
                                space_above = 0
                        
                        all_lines_details.append({
                            "text": cleaned_text,
                            "font_size": dominant_font_size,
                            "is_bold": is_bold_flag,
                            "font_name_sample": font_names[0] if font_names else "unknown",
                            "x0": current_line_bbox[0],
                            "y0": current_line_bbox[1],
                            "x1": current_line_bbox[2],
                            "y1": current_line_bbox[3],
                            "line_height": current_line_bbox[3] - current_line_bbox[1],
                            "page": page_num + 1,
                            "page_height": page_height,
                            "page_width": page_width,
                            "line_length": len(cleaned_text),
                            "num_words": len(cleaned_text.split()),
                            "is_all_caps": cleaned_text.isupper() and len(cleaned_text) > 2,
                            "ends_with_punctuation": bool(re.search(r'[.!?;\:]$', cleaned_text)),
                            "starts_with_number_or_bullet": bool(re.match(r'^\s*(\d+\.?(\d+\.?)*|\-|\*|\u2022)\s+', cleaned_text)),
                            "space_above": space_above
                        })
                        prev_line_bbox = current_line_bbox
                        prev_line_page = page_num
        
        document.close()
        return all_lines_details
        
    def extract_text_blocks(self, pdf_path: str) -> List[TextBlock]:
        """
        Extract text blocks with formatting information from PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of TextBlock objects containing text and formatting info
        """
        text_blocks = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = page.get_text("dict")
                
                for block in blocks["blocks"]:
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                if span["text"].strip():
                                    text_block = TextBlock(
                                        text=span["text"].strip(),
                                        font_size=span["size"],
                                        font_name=span["font"],
                                        bbox=span["bbox"],
                                        page_num=page_num,
                                        is_bold="Bold" in span["font"] or span["flags"] & 2**4,
                                        is_italic="Italic" in span["font"] or span["flags"] & 2**1
                                    )
                                    text_blocks.append(text_block)
            
            doc.close()
            return text_blocks
            
        except Exception as e:
            logger.error(f"Error extracting text blocks: {e}")
            raise
    
    def analyze_font_hierarchy(self, text_blocks: List[TextBlock]) -> Dict[str, Any]:
        """
        Analyze font sizes and styles to determine hierarchy.
        This method can be used to dynamically update thresholds.
        
        Args:
            text_blocks: List of text blocks
            
        Returns:
            Dictionary containing font analysis results
        """
        font_sizes = [block.font_size for block in text_blocks]
        font_names = [block.font_name for block in text_blocks]
        
        # Get font size statistics
        size_counter = Counter(font_sizes)
        most_common_size = size_counter.most_common(1)[0][0]
        
        # Determine size thresholds
        unique_sizes = sorted(list(set(font_sizes)), reverse=True)
        
        # Calculate dynamic thresholds
        dynamic_thresholds = {}
        if len(unique_sizes) >= 4:
            dynamic_thresholds = {
                "TITLE_FONT_MIN": unique_sizes[0],
                "H1_FONT_MIN": unique_sizes[1],
                "H2_FONT_MIN": unique_sizes[2],
                "H3_FONT_MIN": unique_sizes[3],
                "BODY_TEXT_FONT_MAX": most_common_size
            }
        
        # Update rule evaluator with dynamic thresholds
        if dynamic_thresholds:
            self.rule_evaluator.update_thresholds(dynamic_thresholds)
        
        return {
            "most_common_size": most_common_size,
            "title_threshold": unique_sizes[0] if unique_sizes else most_common_size,
            "h1_threshold": unique_sizes[1] if len(unique_sizes) > 1 else most_common_size * 1.2,
            "h2_threshold": unique_sizes[2] if len(unique_sizes) > 2 else most_common_size * 1.1,
            "h3_threshold": most_common_size,
            "unique_sizes": unique_sizes,
            "font_names": list(set(font_names)),
            "dynamic_thresholds": dynamic_thresholds
        }
    
    def is_likely_heading(self, text_block: TextBlock, font_analysis: Dict[str, Any]) -> bool:
        """
        Determine if a text block is likely a heading based on heuristics.
        
        Args:
            text_block: The text block to analyze
            font_analysis: Font analysis results
            
        Returns:
            True if likely a heading, False otherwise
        """
        text = text_block.text.strip()
        
        # Skip very short or very long text
        if len(text) < 3 or len(text) > 200:
            return False
        
        # Skip text that looks like body content
        if len(text.split()) > 20:
            return False
        
        # Check for heading indicators
        heading_indicators = [
            text_block.font_size > font_analysis["most_common_size"],
            text_block.is_bold,
            re.match(r'^\d+\.?\s+[A-Z]', text),  # Numbered headings
            re.match(r'^[A-Z][A-Z\s]+$', text),  # All caps
            any(keyword.lower() in text.lower() for keyword in self.title_keywords),
            text.endswith(':') and len(text.split()) <= 5,  # Short text ending with colon
        ]
        
        # Must have at least 2 indicators to be considered a heading
        return sum(heading_indicators) >= 2
    
    def classify_heading_level(self, text_block: TextBlock, font_analysis: Dict[str, Any]) -> str:
        """
        Classify the heading level (title, h1, h2, h3).
        
        Args:
            text_block: The text block to classify
            font_analysis: Font analysis results
            
        Returns:
            String indicating the heading level
        """
        font_size = text_block.font_size
        text = text_block.text.strip()
        
        # Check for title indicators
        if (font_size >= font_analysis["title_threshold"] or 
            text_block.page_num == 0 and any(word.lower() in text.lower() 
            for word in ['abstract', 'introduction']) and text_block.is_bold):
            return "title"
        
        # Check for H1
        elif font_size >= font_analysis["h1_threshold"]:
            return "h1"
        
        # Check for H2
        elif font_size >= font_analysis["h2_threshold"]:
            return "h2"
        
        # Default to H3
        else:
            return "h3"
    
    def extract_headings(self, pdf_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract headings and titles from PDF using heuristic-based analysis.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing extracted headings organized by level
        """
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            # Extract text blocks
            text_blocks = self.extract_text_blocks(pdf_path)
            
            if not text_blocks:
                return {"title": [], "h1": [], "h2": [], "h3": []}
            
            # Analyze font hierarchy
            font_analysis = self.analyze_font_hierarchy(text_blocks)
            
            # Extract headings
            headings = {"title": [], "h1": [], "h2": [], "h3": []}
            
            for block in text_blocks:
                if self.is_likely_heading(block, font_analysis):
                    level = self.classify_heading_level(block, font_analysis)
                    
                    heading_info = {
                        "text": block.text,
                        "page": block.page_num + 1,  # 1-based page numbering
                        "font_size": block.font_size,
                        "font_name": block.font_name,
                        "is_bold": block.is_bold,
                        "is_italic": block.is_italic,
                        "bbox": block.bbox
                    }
                    
                    headings[level].append(heading_info)
            
            # Remove duplicates while preserving order
            for level in headings:
                seen = set()
                unique_headings = []
                for heading in headings[level]:
                    text_key = heading["text"].lower().strip()
                    if text_key not in seen:
                        seen.add(text_key)
                        unique_headings.append(heading)
                headings[level] = unique_headings
            
            logger.info(f"Extracted {sum(len(h) for h in headings.values())} headings from {pdf_path}")
            return headings
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            raise
    
    def extract_outline_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Processes a PDF to extract its title and outline using rule-based classification.
        
        Args:
            pdf_path: The path to the PDF file.
            
        Returns:
            Dictionary in the specified JSON format with "title" and "outline".
        """
        all_lines = self.get_lines_with_full_details(pdf_path)
        
        title = ""
        outline = []
        potential_headings = []
        
        for line in all_lines:
            predicted_level = self.rule_evaluator.classify_line(line)
            line["predicted_level"] = predicted_level
            
            if predicted_level == "Title":
                if not title:
                    title = line["text"]
            elif predicted_level in ["H1", "H2", "H3"]:
                potential_headings.append({
                    "level": predicted_level,
                    "text": line["text"],
                    "page": line["page"]
                })
        
        # Sort potential headings by page number, then vertical position
        potential_headings.sort(key=lambda x: (x["page"], x["text"]))
        
        for heading in potential_headings:
            if heading["text"].strip():
                outline.append({
                    "level": heading["level"],
                    "text": heading["text"].strip(),
                    "page": heading["page"] - 1  # Convert to 0-indexed
                })
        
        return {
            "title": title.strip(),
            "outline": outline
        }
    
    def get_document_outline(self, pdf_path: str) -> Dict[str, Any]:
        """
        Get a structured outline of the document.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing document outline and metadata
        """
        headings = self.extract_headings(pdf_path)
        
        # Determine document title
        doc_title = "Untitled Document"
        if headings["title"]:
            doc_title = headings["title"][0]["text"]
        elif headings["h1"]:
            doc_title = headings["h1"][0]["text"]
        
        return {
            "document_title": doc_title,
            "headings": headings,
            "total_headings": sum(len(h) for h in headings.values()),
            "processed_file": pdf_path
        }