"""
Configuration file for PDF outline extraction rules and thresholds.
"""

# Font size and formatting thresholds
THRESHOLDS = {
    "TITLE_FONT_MIN": 20.0,
    "H1_FONT_MIN": 15.0,
    "H2_FONT_MIN": 12.0,
    "H3_FONT_MIN": 11.0,
    "BODY_TEXT_FONT_MAX": 12.5,
    "LARGE_SPACE_ABOVE": 15,
    "MEDIUM_SPACE_ABOVE": 8,
    "SMALL_SPACE_ABOVE": 3,
    "MAIN_INDENT_X0_MAX": 0.15,  # Normalized by page width
    "SUB_INDENT_X0_MIN": 0.15,
    "SUB_SUB_INDENT_X0_MIN": 0.20,
}

# Keywords that might indicate titles or specific sections
TITLE_KEYWORDS = [
    'abstract', 'introduction', 'conclusion', 'references', 'bibliography',
    'acknowledgments', 'appendix', 'methodology', 'results', 'discussion'
]

# Exclusion patterns for non-heading text
EXCLUSION_PATTERNS = {
    "footer_header_keywords": ["page", "chapter", "confidential"],
    "separator_patterns": ["-------", ":"],
    "form_field_patterns": [r'^\s*(\d+\.?(\d+\.?)*|\-|\*|\u2022)\s+']
}

# Rule definitions for heading classification
CLASSIFICATION_RULES = [
    {
        "name": "Title_Rule",
        "priority": 1,
        "label": "Title",
        "conditions": {
            "required": [
                {"feature": "page", "operator": "==", "value": 1},
                {"feature": "is_bold", "operator": "==", "value": True},
            ],
            "any_of": [
                {
                    "all_of": [
                        {"feature": "font_size", "operator": ">=", "threshold": "TITLE_FONT_MIN"},
                        {"feature": "is_centered", "operator": "==", "value": True},
                        {"feature": "is_top_of_page", "operator": "==", "value": True}
                    ]
                },
                {
                    "all_of": [
                        {"feature": "font_size", "operator": ">=", "threshold": "H1_FONT_MIN"},
                        {"feature": "is_centered", "operator": "==", "value": True},
                        {"feature": "is_top_of_page", "operator": "==", "value": True},
                        {"feature": "line_length", "operator": "<", "value": 80}
                    ]
                }
            ]
        },
        "exclusions": []
    },
    {
        "name": "Exclusion_FormFields",
        "priority": 2,
        "label": "BodyText",
        "conditions": {
            "required": [
                {"feature": "starts_with_number_or_bullet", "operator": "==", "value": True},
                {"feature": "font_size", "operator": "<=", "threshold": "BODY_TEXT_FONT_MAX", "offset": 1},
                {"feature": "is_bold", "operator": "==", "value": False}
            ]
        },
        "exclusions": []
    },
    {
        "name": "Exclusion_HeaderFooter",
        "priority": 3,
        "label": "Other",
        "conditions": {
            "required": [
                {"feature": "contains_keywords", "operator": "==", "value": True, "keywords": "footer_header_keywords"},
                {"feature": "font_size", "operator": "<", "threshold": "H3_FONT_MIN", "offset": 2}
            ],
            "any_of": [
                {"feature": "is_at_margins", "operator": "==", "value": True}
            ]
        },
        "exclusions": []
    },
    {
        "name": "H1_Rule",
        "priority": 4,
        "label": "H1",
        "conditions": {
            "required": [
                {"feature": "font_size", "operator": ">=", "threshold": "H1_FONT_MIN"},
                {"feature": "is_bold", "operator": "==", "value": True},
                {"feature": "space_above", "operator": ">=", "threshold": "LARGE_SPACE_ABOVE"},
                {"feature": "line_length", "operator": "<", "value": 80},
                {"feature": "ends_with_punctuation", "operator": "==", "value": False},
                {"feature": "x0_normalized", "operator": "<", "threshold": "MAIN_INDENT_X0_MAX"}
            ]
        },
        "exclusions": [
            {"feature": "contains_separators", "operator": "==", "value": True}
        ]
    },
    {
        "name": "H2_Rule",
        "priority": 5,
        "label": "H2",
        "conditions": {
            "required": [
                {"feature": "font_size", "operator": ">=", "threshold": "H2_FONT_MIN"},
                {"feature": "is_bold", "operator": "==", "value": True},
                {"feature": "space_above", "operator": ">=", "threshold": "MEDIUM_SPACE_ABOVE"},
                {"feature": "line_length", "operator": "<", "value": 90},
                {"feature": "ends_with_punctuation", "operator": "==", "value": False},
                {"feature": "x0_normalized", "operator": ">=", "threshold": "SUB_INDENT_X0_MIN"},
                {"feature": "x0_normalized", "operator": "<", "threshold": "SUB_SUB_INDENT_X0_MIN"}
            ]
        },
        "exclusions": []
    },
    {
        "name": "H3_Rule",
        "priority": 6,
        "label": "H3",
        "conditions": {
            "required": [
                {"feature": "font_size", "operator": ">=", "threshold": "H3_FONT_MIN"},
                {"feature": "is_bold", "operator": "==", "value": True},
                {"feature": "space_above", "operator": ">=", "threshold": "SMALL_SPACE_ABOVE"},
                {"feature": "line_length", "operator": "<", "value": 100},
                {"feature": "ends_with_punctuation", "operator": "==", "value": False},
                {"feature": "x0_normalized", "operator": ">=", "threshold": "SUB_SUB_INDENT_X0_MIN"}
            ]
        },
        "exclusions": []
    }
]
