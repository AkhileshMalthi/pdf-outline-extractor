"""
Rule evaluator for PDF outline extraction.
"""
from typing import Dict, Any, Optional
from .rules_config import THRESHOLDS, CLASSIFICATION_RULES, EXCLUSION_PATTERNS


class RuleEvaluator:
    """Evaluates classification rules against text line features."""
    
    def __init__(self, custom_thresholds: Optional[Dict[str, float]] = None):
        """
        Initialize the rule evaluator.
        
        Args:
            custom_thresholds: Optional custom thresholds to override defaults
        """
        self.thresholds = THRESHOLDS.copy()
        if custom_thresholds:
            self.thresholds.update(custom_thresholds)
        
        self.rules = sorted(CLASSIFICATION_RULES, key=lambda x: x["priority"])
    
    def _get_threshold_value(self, threshold_name: str, offset: float = 0) -> float:
        """Get threshold value with optional offset."""
        return self.thresholds.get(threshold_name, 0) + offset
    
    def _extract_derived_features(self, line: Dict[str, Any]) -> Dict[str, Any]:
        """Extract derived features from line data."""
        derived = line.copy()
        
        # Positional features
        page_width = line.get("page_width", 1)
        page_height = line.get("page_height", 1)
        x0 = line.get("x0", 0)
        y0 = line.get("y0", 0)
        
        derived["x0_normalized"] = x0 / page_width if page_width > 0 else 0
        derived["is_centered"] = abs(x0 - (page_width - line.get("x1", 0))) < (page_width * 0.1)
        derived["is_top_of_page"] = y0 < page_height * 0.25
        derived["is_at_margins"] = (x0 < 100 or x0 > page_width - 100) or (y0 < 50 or y0 > page_height - 50)
        
        # Text content features
        text = line.get("text", "").strip()
        derived["contains_keywords"] = any(
            keyword in text.lower() 
            for keyword in EXCLUSION_PATTERNS["footer_header_keywords"]
        )
        derived["contains_separators"] = any(
            pattern in text 
            for pattern in EXCLUSION_PATTERNS["separator_patterns"]
        )
        
        return derived
    
    def _evaluate_condition(self, condition: Dict[str, Any], features: Dict[str, Any]) -> bool:
        """Evaluate a single condition against features."""
        feature_name = condition["feature"]
        operator = condition["operator"]
        
        if feature_name not in features:
            return False
        
        feature_value = features[feature_name]
        
        # Handle threshold-based conditions
        if "threshold" in condition:
            threshold_name = condition["threshold"]
            offset = condition.get("offset", 0)
            comparison_value = self._get_threshold_value(threshold_name, offset)
        else:
            comparison_value = condition["value"]
        
        # Handle special cases
        if feature_name == "contains_keywords" and "keywords" in condition:
            keyword_list = EXCLUSION_PATTERNS.get(condition["keywords"], [])
            text = features.get("text", "").lower()
            return any(keyword in text for keyword in keyword_list)
        
        # Standard operators
        if operator == "==":
            return feature_value == comparison_value
        elif operator == "!=":
            return feature_value != comparison_value
        elif operator == "<":
            return feature_value < comparison_value
        elif operator == "<=":
            return feature_value <= comparison_value
        elif operator == ">":
            return feature_value > comparison_value
        elif operator == ">=":
            return feature_value >= comparison_value
        elif operator == "contains":
            return comparison_value in str(feature_value).lower()
        
        return False
    
    def _evaluate_condition_group(self, conditions: Dict[str, Any], features: Dict[str, Any]) -> bool:
        """Evaluate a group of conditions (required, any_of, all_of)."""
        
        # Check required conditions
        if "required" in conditions:
            for condition in conditions["required"]:
                if not self._evaluate_condition(condition, features):
                    return False
        
        # Check any_of conditions
        if "any_of" in conditions:
            any_satisfied = False
            for condition_group in conditions["any_of"]:
                if "all_of" in condition_group:
                    # Nested all_of within any_of
                    if all(self._evaluate_condition(cond, features) for cond in condition_group["all_of"]):
                        any_satisfied = True
                        break
                else:
                    # Single condition in any_of
                    if self._evaluate_condition(condition_group, features):
                        any_satisfied = True
                        break
            
            if not any_satisfied:
                return False
        
        return True
    
    def classify_line(self, line: Dict[str, Any]) -> str:
        """
        Classify a line based on the configured rules.
        
        Args:
            line: Dictionary containing line features
            
        Returns:
            Classification label (Title, H1, H2, H3, BodyText, Other)
        """
        # Extract derived features
        features = self._extract_derived_features(line)
        
        # Evaluate rules in priority order
        for rule in self.rules:
            # Check exclusions first
            excluded = False
            for exclusion in rule.get("exclusions", []):
                if self._evaluate_condition(exclusion, features):
                    excluded = True
                    break
            
            if excluded:
                continue
            
            # Check main conditions
            if self._evaluate_condition_group(rule["conditions"], features):
                return rule["label"]
        
        # Default to BodyText if no rules match
        return "BodyText"
    
    def update_thresholds(self, new_thresholds: Dict[str, float]):
        """Update threshold values."""
        self.thresholds.update(new_thresholds)
