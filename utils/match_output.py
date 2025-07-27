import json
from typing import Tuple, List, Dict, Optional
import difflib
import sys
import argparse

# Cross-platform color support
try:
    import colorama
    colorama.init()
    COLOR_SUPPORT = True
except ImportError:
    COLOR_SUPPORT = False
    print("Warning: colorama not installed. Install with 'pip install colorama' for better color support.")

# ANSI color codes
GREEN = '\033[92m' if COLOR_SUPPORT else ''
RED = '\033[91m' if COLOR_SUPPORT else ''
YELLOW = '\033[93m' if COLOR_SUPPORT else ''
BLUE = '\033[94m' if COLOR_SUPPORT else ''
RESET = '\033[0m' if COLOR_SUPPORT else ''

def fuzzy_text_match(a: str, b: str, threshold: float = 0.85) -> bool:
    """Return True if a and b are similar enough based on sequence matching."""
    if not a and not b:
        return True
    if not a or not b:
        return False
    ratio = difflib.SequenceMatcher(None, a.strip(), b.strip()).ratio()
    return ratio >= threshold

def color_field(val: str, match: bool, show_colors: bool = True) -> str:
    """Apply color formatting to field values."""
    if not show_colors or not COLOR_SUPPORT:
        return str(val)
    return f"{GREEN}{val}{RESET}" if match else f"{RED}{val}{RESET}"

def load_json_file(file_path: str) -> Dict:
    """Load and validate JSON file with error handling."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{file_path}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading '{file_path}': {e}")
        sys.exit(1)

def find_best_match(target_obj: Dict, candidate_list: List[Dict], threshold: float) -> Tuple[Optional[Dict], int, Tuple[bool, bool, bool]]:
    """Find the best matching object from candidate list using Hungarian-like approach."""
    best_score = 0
    best_match = None
    best_fields = (False, False, False)
    
    for candidate in candidate_list:
        text_match = fuzzy_text_match(
            target_obj.get('text', ''), 
            candidate.get('text', ''), 
            threshold
        )
        level_match = target_obj.get('level', '') == candidate.get('level', '')
        page_match = target_obj.get('page', None) == candidate.get('page', None)
        
        score = int(text_match) + int(level_match) + int(page_match)
        if score > best_score:
            best_score = score
            best_match = candidate
            best_fields = (text_match, level_match, page_match)
    
    return best_match, best_score, best_fields

def compare_and_print_colored(output_path: str, target_path: str, threshold: float = 0.85, show_colors: bool = True):
    """
    Fuzzy match each object in output with each in target, print colored results and match stats.
    """
    print(f"{BLUE}Loading files...{RESET}")
    output_data = load_json_file(output_path)
    target_data = load_json_file(target_path)

    # Check title
    title_match = fuzzy_text_match(output_data.get('title', ''), target_data.get('title', ''), threshold)
    output_title = output_data.get('title', 'No title')
    target_title = target_data.get('title', 'No title')
    
    print(f"\n{BLUE}=== TITLE COMPARISON ==={RESET}")
    print(f"Output: {color_field(output_title, title_match, show_colors)}")
    print(f"Target: {color_field(target_title, title_match, show_colors)}")
    print(f"Match: {'✓' if title_match else '✗'}")

    output_outline = output_data.get('outline', [])
    target_outline = target_data.get('outline', [])

    if not output_outline and not target_outline:
        print(f"\n{YELLOW}Both files have empty outlines.{RESET}")
        return

    print(f"\n{BLUE}=== OUTLINE COMPARISON ==={RESET}")
    print(f"Output entries: {len(output_outline)}")
    print(f"Target entries: {len(target_outline)}")

    perfect_matches = 0
    partial_matches = 0
    no_matches = 0

    # Track which target entries have been matched to avoid double-counting
    used_targets = set()

    for out_idx, out_obj in enumerate(output_outline):
        # Find best match among unused targets
        available_targets = [t for i, t in enumerate(target_outline) if i not in used_targets]
        best_match, best_score, best_fields = find_best_match(out_obj, available_targets, threshold)
        
        # Mark the matched target as used
        if best_match:
            for i, target_obj in enumerate(target_outline):
                if target_obj == best_match and i not in used_targets:
                    used_targets.add(i)
                    break

        # Categorize matches
        if best_score == 3:
            perfect_matches += 1
        elif best_score > 0:
            partial_matches += 1
        else:
            no_matches += 1

        # Print colored output
        text_val = out_obj.get('text', 'No text')[:100] + ('...' if len(out_obj.get('text', '')) > 100 else '')
        level_val = str(out_obj.get('level', 'No level'))
        page_val = str(out_obj.get('page', 'No page'))
        
        text_col = color_field(text_val, best_fields[0] if best_fields else False, show_colors)
        level_col = color_field(level_val, best_fields[1] if best_fields else False, show_colors)
        page_col = color_field(page_val, best_fields[2] if best_fields else False, show_colors)
        
        match_indicator = "✓✓✓" if best_score == 3 else "✓✓" if best_score == 2 else "✓" if best_score == 1 else "✗"
        
        print(f"[{out_idx:3d}] {match_indicator} | text: {text_col}")
        print(f"       {'':4} | level: {level_col} | page: {page_col}")

    # Print summary statistics
    total_output = len(output_outline)
    total_target = len(target_outline)
    
    print(f"\n{BLUE}=== MATCH STATISTICS ==={RESET}")
    print(f"Perfect Matches (3/3): {GREEN}{perfect_matches}{RESET} / {total_output}")
    print(f"Partial Matches (1-2/3): {YELLOW}{partial_matches}{RESET} / {total_output}")
    print(f"No Matches (0/3): {RED}{no_matches}{RESET} / {total_output}")
    
    if total_output > 0:
        accuracy = (perfect_matches + partial_matches * 0.5) / total_output
        print(f"Overall Accuracy: {accuracy:.2%}")
    
    # Check for unmatched target entries
    unmatched_targets = total_target - len(used_targets)
    if unmatched_targets > 0:
        print(f"{YELLOW}Unmatched target entries: {unmatched_targets}{RESET}")

def compare_json_outputs(output_path: str, target_path: str, threshold: float = 0.85) -> Tuple[float, List[Dict]]:
    """
    Compare two JSON files and return a similarity score and a list of differences.
    Enhanced with fuzzy matching and better similarity calculation.
    """
    output_data = load_json_file(output_path)
    target_data = load_json_file(target_path)

    output_outline = output_data.get('outline', [])
    target_outline = target_data.get('outline', [])

    if not output_outline and not target_outline:
        return 1.0, []

    total_entries = max(len(output_outline), len(target_outline))
    if total_entries == 0:
        return 1.0, []

    matched_score = 0
    differences = []
    used_targets = set()

    # Use fuzzy matching instead of exact position matching
    for i, out_entry in enumerate(output_outline):
        available_targets = [
            (j, t) for j, t in enumerate(target_outline) 
            if j not in used_targets
        ]
        
        best_match_idx = None
        best_score = 0
        
        for j, tgt_entry in available_targets:
            text_match = fuzzy_text_match(
                out_entry.get('text', ''), 
                tgt_entry.get('text', ''), 
                threshold
            )
            level_match = out_entry.get('level', '') == tgt_entry.get('level', '')
            page_match = out_entry.get('page', None) == tgt_entry.get('page', None)
            
            score = int(text_match) + int(level_match) + int(page_match)
            if score > best_score:
                best_score = score
                best_match_idx = j
        
        if best_match_idx is not None:
            used_targets.add(best_match_idx)
            matched_score += best_score / 3.0  # Normalize to 0-1
            
            if best_score < 3:  # Not a perfect match
                differences.append({
                    'output_index': i,
                    'target_index': best_match_idx,
                    'output': out_entry,
                    'target': target_outline[best_match_idx],
                    'match_score': best_score / 3.0
                })
        else:
            differences.append({
                'output_index': i,
                'target_index': None,
                'output': out_entry,
                'target': None,
                'match_score': 0.0
            })

    # Add unmatched target entries
    for j, tgt_entry in enumerate(target_outline):
        if j not in used_targets:
            differences.append({
                'output_index': None,
                'target_index': j,
                'output': None,
                'target': tgt_entry,
                'match_score': 0.0
            })

    similarity = matched_score / total_entries if total_entries > 0 else 1.0
    return similarity, differences

def main():
    parser = argparse.ArgumentParser(
        description="Fuzzy compare two JSON outline files and print colored match results.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python script.py output.json target.json
  python script.py output.json target.json --threshold 0.9
  python script.py output.json target.json --no-color --score-only
        """
    )
    
    parser.add_argument("output_file", help="Path to output JSON file")
    parser.add_argument("target_file", help="Path to target JSON file")
    parser.add_argument(
        "--threshold", 
        type=float, 
        default=0.85, 
        help="Fuzzy match threshold (0.0-1.0, default: 0.85)"
    )
    parser.add_argument(
        "--no-color", 
        action="store_true", 
        help="Disable colored output"
    )
    parser.add_argument(
        "--score-only", 
        action="store_true", 
        help="Only print similarity score and exit"
    )
    
    args = parser.parse_args()
    
    # Validate threshold
    if not 0.0 <= args.threshold <= 1.0:
        print("Error: Threshold must be between 0.0 and 1.0")
        sys.exit(1)
    
    if args.score_only:
        similarity, differences = compare_json_outputs(
            args.output_file, 
            args.target_file, 
            args.threshold
        )
        print(f"{similarity:.4f}")
    else:
        compare_and_print_colored(
            args.output_file, 
            args.target_file, 
            args.threshold,
            show_colors=not args.no_color
        )

if __name__ == "__main__":
    main()