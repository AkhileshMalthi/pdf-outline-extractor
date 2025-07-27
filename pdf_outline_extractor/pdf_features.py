from pydantic import BaseModel, Field
from typing import List, Optional

# Base Feature Models

class TextContentFeatures(BaseModel):
    """Features directly related to the textual content."""
    text_content: str
    num_words: int
    num_characters: int
    is_all_caps: bool = False
    is_title_case: bool = False
    starts_with_number_pattern: bool = False # e.g., "1.", "1.1", "A."
    starts_with_bullet: bool = False # e.g., "•", "-"
    ends_with_punctuation: bool = False # e.g., ".", ",", "!"
    has_leading_whitespace: bool = False
    has_trailing_whitespace: bool = False

class FontFeatures(BaseModel):
    """Features describing the font characteristics."""
    font_size: float
    is_bold: bool
    is_italic: bool
    font_name: str  # e.g., 'Times New Roman', 'Arial'
    font_color: Optional[str] = None  # Hex code or common color name

class LayoutFeatures(BaseModel):
    """Features related to the position and layout of the text block."""
    page_number: int
    bbox: List[float] = Field(default_factory=list)  # [x0, y0, x1, y1] coordinates
    line_height: float  # Distance between baselines of consecutive lines in the block
    num_lines: int
    indentation: float  # Distance from the left edge of the page/column
    is_left_aligned: bool
    space_before: Optional[float] = None # Vertical space relative to previous block
    space_after: Optional[float] = None  # Vertical space relative to next block

# Combined/Derived Feature Models

class ContextualFeatures(BaseModel):
    """
    Features derived from the text block's context within the document
    (e.g., relative to other blocks or overall document statistics).
    """
    relative_font_size_to_avg: Optional[float] = None # Ratio to average font size on page
    # Indicates significant change in font/spacing from the previous block
    is_visually_distinct_from_prev: Optional[bool] = None
    # Indicates significant change in font/spacing to the next block
    is_visually_distinct_from_next: Optional[bool] = None

# Main Text Block Feature Model

class TextBlock(
    TextContentFeatures,
    FontFeatures,
    LayoutFeatures,
    ContextualFeatures
):
    """
    Comprehensive features for a text block, combining all modular feature sets.
    This class can be instantiated with all features required for heuristics
    and ML classification.
    """
    # We can remove this field if not needed for the heuristic pass
    # Additional Features (optional fields, can be set later)
    potential_heading_level: Optional[str] = None # e.g., "H1", "H2", "H3", "Body"
    confidence_score: Optional[float] = None # For ML model output


# Example Usage (how you might create an instance):
if __name__ == "__main__":
    sample_text_block = TextBlock(
        text_content="1. Introduction to AI",
        page_number=1,
        font_size=16.0,
        is_bold=True,
        is_italic=False,
        font_name="Arial",
        bbox=[50.0, 700.0, 300.0, 715.0],
        line_height=18.0,
        num_lines=1,
        indentation=0.0,
        is_left_aligned=True,
        num_words=4,
        num_characters=20,
        starts_with_number_pattern=True,
        ends_with_punctuation=False,
        is_all_caps=False,
        is_title_case=True,
        space_before=20.0,
        space_after=10.0,
        relative_font_size_to_avg=1.5,
        is_visually_distinct_from_prev=True
    )

    print(sample_text_block.model_dump_json(indent=2))

    # You could then update its potential heading level after a heuristic pass
    sample_text_block.potential_heading_level = "H1"
    print("\nUpdated with potential heading level:")
    print(sample_text_block.model_dump_json(indent=2))