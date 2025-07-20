"""
PDF Outline Extractor

Main module for extracting structured outlines from PDF documents.
Uses PyMuPDF for PDF processing and text analysis for outline detection.
"""

import fitz  # PyMuPDF
import re
from pathlib import Path
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class PDFOutlineExtractor:
    """
    Extracts structured outlines from PDF documents.
    
    This class analyzes PDF content to identify headings and structure them
    into a hierarchical outline format suitable for the hackathon challenge.
    """
    
    def __init__(self):
        """Initialize the PDF outline extractor."""
        # Common heading patterns
        self.heading_patterns = [
            r'^\d+\.\s+',  # 1. Chapter Title
            r'^\d+\.\d+\s+',  # 1.1 Section Title
            r'^\d+\.\d+\.\d+\s+',  # 1.1.1 Subsection Title
            r'^Chapter\s+\d+',  # Chapter 1
            r'^Section\s+\d+',  # Section 1
            r'^Appendix\s+[A-Z]',  # Appendix A
            r'^[A-Z]+\.\s+',  # A. Title
            r'^\([a-z]\)\s+',  # (a) subtitle
        ]
        
        # Font size thresholds for heading detection
        self.heading_font_threshold = 12.0
        self.title_font_threshold = 16.0
    
    def extract_outline(self, pdf_path: Path) -> Dict[str, any]:
        """
        Extract outline from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing title and outline structure
        """
        try:
            doc = fitz.open(str(pdf_path))
            
            # Extract title
            title = self._extract_title(doc)
            
            # Extract outline
            outline = self._extract_outline_items(doc)
            
            doc.close()
            
            return {
                "title": title,
                "outline": outline
            }
            
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}")
            # Return empty structure on error
            return {
                "title": pdf_path.stem,
                "outline": []
            }
    
    def _extract_title(self, doc: fitz.Document) -> str:
        """
        Extract document title from PDF metadata or first page.
        
        Args:
            doc: PyMuPDF document object
            
        Returns:
            Document title string
        """
        # Try metadata first
        metadata = doc.metadata
        if metadata.get('title'):
            return metadata['title'].strip()
        
        # Try to find title on first page
        if len(doc) > 0:
            page = doc[0]
            blocks = page.get_text("dict")
            
            # Look for largest font on first page as title
            largest_font_size = 0
            title_text = ""
            
            for block in blocks["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            font_size = span["size"]
                            text = span["text"].strip()
                            
                            if (font_size > largest_font_size and 
                                len(text) > 5 and 
                                font_size > self.title_font_threshold):
                                largest_font_size = font_size
                                title_text = text
            
            if title_text:
                return title_text
        
        # Fallback to filename
        return doc.name or "Unknown Document"
    
    def _extract_outline_items(self, doc: fitz.Document) -> List[Dict[str, any]]:
        """
        Extract outline items from document pages.
        
        Args:
            doc: PyMuPDF document object
            
        Returns:
            List of outline items with level, text, and page
        """
        outline_items = []
        
        # First try built-in outline/bookmarks
        toc = doc.get_toc()
        if toc:
            for item in toc:
                level, title, page_num = item
                outline_items.append({
                    "level": f"H{level}",
                    "text": title.strip(),
                    "page": page_num
                })
            return outline_items
        
        # If no built-in outline, analyze text formatting
        for page_num in range(len(doc)):
            page = doc[page_num]
            items = self._analyze_page_for_headings(page, page_num + 1)
            outline_items.extend(items)
        
        return outline_items
    
    def _analyze_page_for_headings(self, page: fitz.Page, page_num: int) -> List[Dict[str, any]]:
        """
        Analyze a page for potential headings based on formatting.
        
        Args:
            page: PyMuPDF page object
            page_num: Page number (1-indexed)
            
        Returns:
            List of heading items found on this page
        """
        headings = []
        blocks = page.get_text("dict")
        
        for block in blocks["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    line_text = ""
                    max_font_size = 0
                    is_bold = False
                    
                    # Combine spans in line
                    for span in line["spans"]:
                        line_text += span["text"]
                        max_font_size = max(max_font_size, span["size"])
                        if span["flags"] & 2**4:  # Bold flag
                            is_bold = True
                    
                    line_text = line_text.strip()
                    
                    # Check if this looks like a heading
                    if self._is_heading(line_text, max_font_size, is_bold):
                        level = self._determine_heading_level(line_text, max_font_size)
                        headings.append({
                            "level": level,
                            "text": line_text,
                            "page": page_num
                        })
        
        return headings
    
    def _is_heading(self, text: str, font_size: float, is_bold: bool) -> bool:
        """
        Determine if text is likely a heading.
        
        Args:
            text: Text content
            font_size: Font size
            is_bold: Whether text is bold
            
        Returns:
            True if text appears to be a heading
        """
        # Skip very short or very long text
        if len(text) < 3 or len(text) > 200:
            return False
        
        # Check font size threshold
        if font_size < self.heading_font_threshold:
            return False
        
        # Check for heading patterns
        for pattern in self.heading_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        
        # Check if bold and reasonable length
        if is_bold and 5 <= len(text) <= 100:
            return True
        
        # Check for ALL CAPS (potential heading)
        if text.isupper() and 5 <= len(text) <= 50:
            return True
        
        return False
    
    def _determine_heading_level(self, text: str, font_size: float) -> str:
        """
        Determine heading level based on text patterns and font size.
        
        Args:
            text: Text content
            font_size: Font size
            
        Returns:
            Heading level string (H1, H2, etc.)
        """
        # Check specific patterns first
        if re.match(r'^\d+\.\s+', text):
            return "H1"
        elif re.match(r'^\d+\.\d+\s+', text):
            return "H2"
        elif re.match(r'^\d+\.\d+\.\d+\s+', text):
            return "H3"
        elif re.match(r'^Chapter\s+\d+', text, re.IGNORECASE):
            return "H1"
        elif re.match(r'^Section\s+\d+', text, re.IGNORECASE):
            return "H2"
        elif re.match(r'^Appendix\s+[A-Z]', text, re.IGNORECASE):
            return "H1"
        
        # Use font size to determine level
        if font_size >= 18:
            return "H1"
        elif font_size >= 16:
            return "H2"
        elif font_size >= 14:
            return "H3"
        else:
            return "H4"
