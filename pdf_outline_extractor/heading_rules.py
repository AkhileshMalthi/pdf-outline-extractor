from .pdf_features import TextBlock

MIN_HEADING_FONT_SIZE_DIFF = 2.0
MIN_RELATIVE_FONT_SIZE = 1.2
MAX_HEADING_WORDS = 15
MIN_SPACE_BEFORE_HEADING = 5.0
MIN_SPACE_AFTER_HEADING = 2.0


def heading_if_larger_font(block: TextBlock) -> bool:
    """
    Rule: A text block is a heading if its font size is significantly larger
    than the average font size on the page.
    """
    if block.relative_font_size_to_avg is None:
        return False
    estimated_avg_font_size = block.font_size / block.relative_font_size_to_avg if block.relative_font_size_to_avg else 0
    return block.relative_font_size_to_avg > MIN_RELATIVE_FONT_SIZE or \
           (block.font_size - estimated_avg_font_size) > MIN_HEADING_FONT_SIZE_DIFF


def heading_if_bold(block: TextBlock) -> bool:
    """
    Rule: A text block is a heading if it is bold.
    """
    return block.is_bold


def heading_if_distinct_spacing(block: TextBlock) -> bool:
    """
    Rule: A text block is a heading if it has significant vertical spacing
    before and/or after it, indicating separation from body text.
    """
    has_space_before = block.space_before is not None and block.space_before > MIN_SPACE_BEFORE_HEADING
    has_space_after = block.space_after is not None and block.space_after > MIN_SPACE_AFTER_HEADING
    return has_space_before or has_space_after


def heading_if_starts_with_number_pattern(block: TextBlock) -> bool:
    """
    Rule: A text block is a heading if it starts with a common numbering
    pattern (e.g., 1., 1.1, A.).
    """
    return block.starts_with_number_pattern


def heading_if_short_and_concise(block: TextBlock) -> bool:
    """
    Rule: A text block is a heading if it is relatively short and concise.
    """
    return block.num_words <= MAX_HEADING_WORDS


def not_heading_if_ends_with_punctuation(block: TextBlock) -> bool:
    """
    Rule: A text block is NOT a heading if it ends with common sentence-ending
    punctuation (e.g., period, comma), as headings typically don't.
    """
    return block.ends_with_punctuation


def heading_if_title_or_all_caps(block: TextBlock) -> bool:
    """
    Rule: A text block is a heading if it is in Title Case or ALL CAPS.
    """
    return block.is_title_case or block.is_all_caps


def heading_if_left_aligned(block: TextBlock) -> bool:
    """
    Rule: A text block is a heading if it is left-aligned.
    """
    return block.is_left_aligned


def heading_if_visually_distinct_from_surroundings(block: TextBlock) -> bool:
    """
    Rule: A text block is a heading if it is visually distinct from the
    preceding and/or succeeding text blocks (e.g., due to a significant
    change in font size, bolding, or vertical spacing).
    """
    return block.is_visually_distinct_from_prev is True or \
           block.is_visually_distinct_from_next is True


# --- Composite/Combined Heading Rules ---

def heading_if_strong_candidate(block: TextBlock) -> bool:
    """
    A strong candidate rule combining several features often seen in headings.
    """
    return (
        heading_if_larger_font(block) and
        heading_if_bold(block) and
        heading_if_short_and_concise(block) and
        not not_heading_if_ends_with_punctuation(block) and
        heading_if_left_aligned(block) and
        heading_if_distinct_spacing(block)
    )

# --- "Not Heading" Specific Rules ---

def not_heading_if_very_long(block: TextBlock) -> bool:
    """
    Rule: A text block is NOT a heading if it's exceptionally long (likely body text).
    """
    return block.num_words > 50


def not_heading_if_no_bold_or_large_font(block: TextBlock) -> bool:
    """
    Rule: A text block is NOT a heading if it's neither bold nor significantly large.
    """
    return not block.is_bold and not heading_if_larger_font(block)


POSITIVE_HEADING_INDICATORS = [
    heading_if_larger_font,
    heading_if_bold,
    heading_if_distinct_spacing,
    heading_if_starts_with_number_pattern,
    heading_if_short_and_concise,
    heading_if_title_or_all_caps,
    heading_if_left_aligned,
    heading_if_visually_distinct_from_surroundings,
]

NEGATIVE_HEADING_INDICATORS = [
    not_heading_if_ends_with_punctuation,
    not_heading_if_very_long,
    not_heading_if_no_bold_or_large_font,
]
