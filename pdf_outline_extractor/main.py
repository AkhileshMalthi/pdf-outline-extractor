import logging
from pathlib import Path
from typing import Dict, Any, Union
from .pdf_processor import PDFProcessor

"""
PDF Outline Extractor Class

Main class for extracting outlines from PDF files using rule-based classification.
"""


logger = logging.getLogger(__name__)


class PDFOutlineExtractor:
    """
    Extracts outline/bookmark structure from PDF files using rule-based classification.
    """
    
    def __init__(self, custom_thresholds: Union[Dict[str, float], None] = None):
        """
        Initialize the PDF outline extractor.
        
        Args:
            custom_thresholds: Optional custom thresholds for rule evaluation
        """
        self.processor = PDFProcessor(custom_thresholds)
    
    def extract_outline(self, pdf_file: Union[str, Path]) -> Dict[str, Any]:
        """
        Extract outline from a PDF file using rule-based classification.
        
        Args:
            pdf_file: Path to the PDF file
            
        Returns:
            Dictionary containing the extracted outline data
            
        Raises:
            Exception: If PDF processing fails
        """
        # Convert to Path object if string
        pdf_path = Path(pdf_file)
        
        # Validate file exists
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            return self.processor.extract_outline_from_pdf(str(pdf_path))
        except Exception as e:
            logger.error(f"Error extracting outline from {pdf_path}: {e}")
            raise