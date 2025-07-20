"""
Benchmark Script for PDF Outline Extractor

Tests performance against challenge constraints:
- Execution time ≤ 10 seconds for 50-page PDFs
- Memory usage monitoring
- CPU utilization tracking
- Accuracy validation against ground truth data
"""

import time
import psutil
import json
import argparse
from pathlib import Path
from pdf_outline_extractor.extractor import PDFOutlineExtractor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_accuracy_metrics(predicted: dict, ground_truth: dict) -> dict:
    """
    Calculate accuracy metrics by comparing predicted output with ground truth.
    
    Args:
        predicted: Predicted extraction result
        ground_truth: Ground truth JSON data
        
    Returns:
        Dictionary containing accuracy metrics
    """
    metrics = {
        "title_match": False,
        "title_similarity": 0.0,
        "outline_items_predicted": len(predicted.get("outline", [])),
        "outline_items_ground_truth": len(ground_truth.get("outline", [])),
        "exact_matches": 0,
        "partial_matches": 0,
        "precision": 0.0,
        "recall": 0.0,
        "f1_score": 0.0
    }
    
    # Title comparison
    pred_title = predicted.get("title", "").strip().lower()
    gt_title = ground_truth.get("title", "").strip().lower()
    
    if pred_title and gt_title:
        # Exact match
        metrics["title_match"] = pred_title == gt_title
        
        # Similarity score (simple word overlap)
        pred_words = set(pred_title.split())
        gt_words = set(gt_title.split())
        if gt_words:
            metrics["title_similarity"] = len(pred_words & gt_words) / len(gt_words)
    
    # Outline comparison
    pred_outline = predicted.get("outline", [])
    gt_outline = ground_truth.get("outline", [])
    
    if gt_outline:
        # Compare outline items
        exact_matches = 0
        partial_matches = 0
        
        for gt_item in gt_outline:
            gt_text = gt_item.get("text", "").strip().lower()
            gt_level = gt_item.get("level", "")
            gt_page = gt_item.get("page", 0)
            
            # Check for exact matches
            exact_match_found = False
            for pred_item in pred_outline:
                pred_text = pred_item.get("text", "").strip().lower()
                pred_level = pred_item.get("level", "")
                pred_page = pred_item.get("page", 0)
                
                if (gt_text == pred_text and 
                    gt_level == pred_level and 
                    gt_page == pred_page):
                    exact_matches += 1
                    exact_match_found = True
                    break
            
            # If no exact match, check for partial matches (text similarity)
            if not exact_match_found:
                for pred_item in pred_outline:
                    pred_text = pred_item.get("text", "").strip().lower()
                    
                    # Simple word overlap similarity
                    gt_words = set(gt_text.split())
                    pred_words = set(pred_text.split())
                    
                    if gt_words and len(gt_words & pred_words) / len(gt_words) > 0.5:
                        partial_matches += 1
                        break
        
        metrics["exact_matches"] = exact_matches
        metrics["partial_matches"] = partial_matches
        
        # Calculate precision, recall, F1
        if pred_outline:
            metrics["precision"] = exact_matches / len(pred_outline)
        
        metrics["recall"] = exact_matches / len(gt_outline)
        
        if metrics["precision"] + metrics["recall"] > 0:
            metrics["f1_score"] = 2 * (metrics["precision"] * metrics["recall"]) / (metrics["precision"] + metrics["recall"])
    
    return metrics


def benchmark_extraction(pdf_path: Path, ground_truth_dir: Path = None) -> dict:
    """
    Benchmark a single PDF extraction.
    
    Args:
        pdf_path: Path to PDF file
        ground_truth_dir: Optional directory containing ground truth JSON files
        
    Returns:
        Benchmark results dictionary
    """
    extractor = PDFOutlineExtractor()
    
    # Monitor process
    process = psutil.Process()
    
    # Record initial state
    start_memory = process.memory_info().rss / 1024 / 1024  # MB
    start_time = time.time()
    
    try:
        # Extract outline
        result = extractor.extract_outline(pdf_path)
        
        # Record final state
        end_time = time.time()
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        execution_time = end_time - start_time
        memory_used = end_memory - start_memory
        
        benchmark_result = {
            "file": pdf_path.name,
            "success": True,
            "execution_time": execution_time,
            "memory_used_mb": memory_used,
            "peak_memory_mb": end_memory,
            "outline_items": len(result.get("outline", [])),
            "title_extracted": bool(result.get("title", "").strip())
        }
        
        # Add accuracy metrics if ground truth is available
        if ground_truth_dir:
            gt_file = ground_truth_dir / f"{pdf_path.stem}.json"
            if gt_file.exists():
                try:
                    with open(gt_file, "r", encoding="utf-8") as f:
                        ground_truth = json.load(f)
                    
                    accuracy_metrics = calculate_accuracy_metrics(result, ground_truth)
                    benchmark_result["accuracy"] = accuracy_metrics
                    
                except Exception as e:
                    logger.warning(f"Failed to load ground truth for {pdf_path.name}: {e}")
                    benchmark_result["accuracy"] = {"error": str(e)}
            else:
                logger.warning(f"No ground truth file found for {pdf_path.name}")
                benchmark_result["accuracy"] = {"error": "Ground truth file not found"}
        
        return benchmark_result
        
    except Exception as e:
        end_time = time.time()
        return {
            "file": pdf_path.name,
            "success": False,
            "execution_time": end_time - start_time,
            "error": str(e)
        }


def run_benchmarks(input_dir: Path, output_file: Path = None, ground_truth_dir: Path = None) -> dict:
    """
    Run benchmarks on all PDFs in input directory.
    
    Args:
        input_dir: Directory containing PDF files
        output_file: Optional output file for results
        ground_truth_dir: Optional directory containing ground truth JSON files
        
    Returns:
        Aggregated benchmark results
    """
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {input_dir}")
        return {}
    
    logger.info(f"Benchmarking {len(pdf_files)} PDF files")
    
    if ground_truth_dir:
        logger.info(f"Using ground truth data from {ground_truth_dir}")
    
    results = []
    total_time = 0
    successful_extractions = 0
    accuracy_stats = {
        "files_with_ground_truth": 0,
        "total_precision": 0.0,
        "total_recall": 0.0,
        "total_f1": 0.0,
        "title_matches": 0
    }
    
    for pdf_file in pdf_files:
        logger.info(f"Benchmarking {pdf_file.name}")
        
        result = benchmark_extraction(pdf_file, ground_truth_dir)
        results.append(result)
        
        if result["success"]:
            successful_extractions += 1
            total_time += result["execution_time"]
            
            # Check constraints
            if result["execution_time"] > 10.0:
                logger.warning(f"⚠️  {pdf_file.name} exceeded 10s limit: {result['execution_time']:.2f}s")
            else:
                logger.info(f"✓ {pdf_file.name}: {result['execution_time']:.2f}s")
            
            # Collect accuracy statistics
            if "accuracy" in result and "error" not in result["accuracy"]:
                accuracy = result["accuracy"]
                accuracy_stats["files_with_ground_truth"] += 1
                accuracy_stats["total_precision"] += accuracy["precision"]
                accuracy_stats["total_recall"] += accuracy["recall"]
                accuracy_stats["total_f1"] += accuracy["f1_score"]
                if accuracy["title_match"]:
                    accuracy_stats["title_matches"] += 1
                
                logger.info(f"  📊 Accuracy - Precision: {accuracy['precision']:.2f}, "
                           f"Recall: {accuracy['recall']:.2f}, F1: {accuracy['f1_score']:.2f}")
    
    # Aggregate results
    summary = {
        "total_files": len(pdf_files),
        "successful_extractions": successful_extractions,
        "average_time": total_time / successful_extractions if successful_extractions > 0 else 0,
        "total_time": total_time,
        "constraint_violations": sum(1 for r in results if r.get("execution_time", 0) > 10.0),
        "detailed_results": results
    }
    
    # Add accuracy summary if ground truth was used
    if ground_truth_dir and accuracy_stats["files_with_ground_truth"] > 0:
        gt_count = accuracy_stats["files_with_ground_truth"]
        summary["accuracy_summary"] = {
            "files_evaluated": gt_count,
            "average_precision": accuracy_stats["total_precision"] / gt_count,
            "average_recall": accuracy_stats["total_recall"] / gt_count,
            "average_f1_score": accuracy_stats["total_f1"] / gt_count,
            "title_accuracy": accuracy_stats["title_matches"] / gt_count
        }
    
    # Save results if output file specified
    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Benchmark results saved to {output_file}")
    
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Benchmark PDF Outline Extractor performance and accuracy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic performance benchmarking
  python benchmark.py /path/to/pdfs

  # Save results to file
  python benchmark.py /path/to/pdfs --output results.json

  # Include accuracy validation with ground truth
  python benchmark.py /path/to/pdfs --ground-truth /path/to/ground_truth

  # Full benchmark with all options
  python benchmark.py /path/to/pdfs --output results.json --ground-truth /path/to/ground_truth
        """
    )
    
    parser.add_argument(
        "input_directory",
        type=Path,
        help="Directory containing PDF files to benchmark"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="JSON file to save benchmark results"
    )
    
    parser.add_argument(
        "-g", "--ground-truth",
        type=Path,
        help="Directory containing ground truth JSON files for accuracy validation"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate input directory
    if not args.input_directory.exists():
        print(f"❌ Input directory {args.input_directory} does not exist")
        exit(1)
    
    # Validate ground truth directory if provided
    if args.ground_truth and not args.ground_truth.exists():
        print(f"❌ Ground truth directory {args.ground_truth} does not exist")
        exit(1)
    
    # Run benchmarks
    print(f"🚀 Starting benchmark for PDFs in {args.input_directory}")
    if args.ground_truth:
        print(f"📊 Using ground truth data from {args.ground_truth}")
    if args.output:
        print(f"💾 Results will be saved to {args.output}")
    
    results = run_benchmarks(args.input_directory, args.output, args.ground_truth)
    
    # Print summary
    print("\n" + "="*60)
    print("BENCHMARK SUMMARY")
    print("="*60)
    print(f"Total files: {results['total_files']}")
    print(f"Successful extractions: {results['successful_extractions']}")
    print(f"Average time: {results['average_time']:.2f}s")
    print(f"Constraint violations (>10s): {results['constraint_violations']}")
    
    if results['constraint_violations'] == 0:
        print("✅ All files processed within 10s constraint!")
    else:
        print(f"⚠️  {results['constraint_violations']} files exceeded time limit")
    
    # Print accuracy summary if available
    if "accuracy_summary" in results:
        acc = results["accuracy_summary"]
        print("\n" + "-"*60)
        print("ACCURACY SUMMARY (vs Ground Truth)")
        print("-"*60)
        print(f"Files evaluated: {acc['files_evaluated']}")
        print(f"Average Precision: {acc['average_precision']:.3f}")
        print(f"Average Recall: {acc['average_recall']:.3f}")
        print(f"Average F1 Score: {acc['average_f1_score']:.3f}")
        print(f"Title Accuracy: {acc['title_accuracy']:.3f}")
        
        # Quality assessment
        f1_score = acc['average_f1_score']
        if f1_score >= 0.8:
            print("🎯 Excellent extraction quality!")
        elif f1_score >= 0.6:
            print("👍 Good extraction quality")
        elif f1_score >= 0.4:
            print("⚠️  Moderate extraction quality - needs improvement")
        else:
            print("❌ Poor extraction quality - requires significant improvement")
    else:
        print("\n💡 Tip: Use ground truth directory to evaluate extraction accuracy")
