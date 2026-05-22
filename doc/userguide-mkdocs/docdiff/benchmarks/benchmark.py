#!/usr/bin/env python3
"""Benchmark script for docdiff performance analysis.

This module provides comprehensive benchmarking for all major components
of the docdiff tool:
- HTML extraction
- Markdown extraction
- Section alignment
- Content comparison
- Full pipeline execution

Results are output in a structured format suitable for analysis.
"""

import gc
import statistics
import subprocess
import sys
import time
import tracemalloc
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""
    name: str
    iterations: int
    times_ms: List[float] = field(default_factory=list)
    memory_current_mb: float = 0.0
    memory_peak_mb: float = 0.0

    @property
    def mean_ms(self) -> float:
        return statistics.mean(self.times_ms) if self.times_ms else 0.0

    @property
    def stdev_ms(self) -> float:
        return statistics.stdev(self.times_ms) if len(self.times_ms) > 1 else 0.0

    @property
    def min_ms(self) -> float:
        return min(self.times_ms) if self.times_ms else 0.0

    @property
    def max_ms(self) -> float:
        return max(self.times_ms) if self.times_ms else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "iterations": self.iterations,
            "mean_ms": round(self.mean_ms, 2),
            "stdev_ms": round(self.stdev_ms, 2),
            "min_ms": round(self.min_ms, 2),
            "max_ms": round(self.max_ms, 2),
            "memory_current_mb": round(self.memory_current_mb, 2),
            "memory_peak_mb": round(self.memory_peak_mb, 2),
        }


def run_benchmark(
    name: str,
    func: Callable,
    iterations: int = 5,
    warmup: int = 1,
    measure_memory: bool = True,
) -> BenchmarkResult:
    """Run a benchmark function multiple times and collect metrics.

    Args:
        name: Name of the benchmark
        func: Function to benchmark (no arguments)
        iterations: Number of timed iterations
        warmup: Number of warmup iterations (not timed)
        measure_memory: Whether to measure memory usage

    Returns:
        BenchmarkResult with timing and memory metrics
    """
    result = BenchmarkResult(name=name, iterations=iterations)

    # Warmup runs
    for _ in range(warmup):
        func()

    # Force garbage collection before measurement
    gc.collect()

    # Memory measurement (on last iteration)
    if measure_memory:
        tracemalloc.start()

    # Timed iterations
    for i in range(iterations):
        start = time.perf_counter()
        func()
        elapsed = time.perf_counter() - start
        result.times_ms.append(elapsed * 1000)

        # Measure memory on last iteration
        if measure_memory and i == iterations - 1:
            current, peak = tracemalloc.get_traced_memory()
            result.memory_current_mb = current / 1024 / 1024
            result.memory_peak_mb = peak / 1024 / 1024
            tracemalloc.stop()

    return result


def benchmark_html_extraction() -> BenchmarkResult:
    """Benchmark HTML section extraction."""
    from docdiff.extractors.html_extractor import extract_from_file

    html_file = Path(__file__).parent.parent / "data" / "RobotFrameworkUserGuide.html"
    if not html_file.exists():
        print(f"  [SKIP] HTML file not found: {html_file}")
        return BenchmarkResult(name="html_extraction", iterations=0)

    def bench():
        return extract_from_file(str(html_file))

    return run_benchmark("html_extraction", bench, iterations=5)


def benchmark_md_extraction() -> BenchmarkResult:
    """Benchmark Markdown directory extraction."""
    from docdiff.extractors.md_extractor import extract_from_directory

    md_dir = Path("/home/many/workspace/robotframework/doc/userguide-mkdocs/docs")
    if not md_dir.exists():
        print(f"  [SKIP] Markdown directory not found: {md_dir}")
        return BenchmarkResult(name="md_extraction", iterations=0)

    def bench():
        return extract_from_directory(str(md_dir))

    return run_benchmark("md_extraction", bench, iterations=5)


def benchmark_alignment() -> BenchmarkResult:
    """Benchmark section alignment between HTML and MD sections."""
    from docdiff.extractors.html_extractor import extract_from_file
    from docdiff.extractors.md_extractor import extract_from_directory
    from docdiff.aligners import align_sections
    from docdiff.cli import flatten_all_sections

    html_file = Path(__file__).parent.parent / "data" / "RobotFrameworkUserGuide.html"
    md_dir = Path("/home/many/workspace/robotframework/doc/userguide-mkdocs/docs")

    if not html_file.exists() or not md_dir.exists():
        print("  [SKIP] Required files not found for alignment benchmark")
        return BenchmarkResult(name="alignment", iterations=0)

    # Pre-extract sections (not part of alignment benchmark)
    html_sections = extract_from_file(str(html_file))
    md_sections_by_file = extract_from_directory(str(md_dir))
    md_sections = []
    for sections in md_sections_by_file.values():
        md_sections.extend(sections)

    html_flat = flatten_all_sections(html_sections)
    md_flat = flatten_all_sections(md_sections)

    def bench():
        return align_sections(html_flat, md_flat)

    return run_benchmark("alignment", bench, iterations=5)


def benchmark_comparison() -> BenchmarkResult:
    """Benchmark content comparison of aligned sections."""
    from docdiff.extractors.html_extractor import extract_from_file
    from docdiff.extractors.md_extractor import extract_from_directory
    from docdiff.aligners import align_sections
    from docdiff.comparators.content_comparator import compare_section
    from docdiff.cli import flatten_all_sections

    html_file = Path(__file__).parent.parent / "data" / "RobotFrameworkUserGuide.html"
    md_dir = Path("/home/many/workspace/robotframework/doc/userguide-mkdocs/docs")

    if not html_file.exists() or not md_dir.exists():
        print("  [SKIP] Required files not found for comparison benchmark")
        return BenchmarkResult(name="comparison", iterations=0)

    # Pre-extract and align (not part of comparison benchmark)
    html_sections = extract_from_file(str(html_file))
    md_sections_by_file = extract_from_directory(str(md_dir))
    md_sections = []
    for sections in md_sections_by_file.values():
        md_sections.extend(sections)

    html_flat = flatten_all_sections(html_sections)
    md_flat = flatten_all_sections(md_sections)
    alignment = align_sections(html_flat, md_flat)

    def bench():
        for old_section, new_section in alignment.matched:
            try:
                compare_section(old_section, new_section)
            except Exception:
                # Handle edge cases in comparators gracefully
                pass

    return run_benchmark("comparison", bench, iterations=5)


def benchmark_full_pipeline() -> BenchmarkResult:
    """Benchmark complete comparison pipeline via CLI."""
    docdiff_dir = Path(__file__).parent.parent
    html_file = docdiff_dir / "data" / "RobotFrameworkUserGuide.html"
    md_dir = Path("/home/many/workspace/robotframework/doc/userguide-mkdocs/docs")

    if not html_file.exists() or not md_dir.exists():
        print("  [SKIP] Required files not found for full pipeline benchmark")
        return BenchmarkResult(name="full_pipeline", iterations=0)

    result = BenchmarkResult(name="full_pipeline", iterations=3)

    for _ in range(3):
        start = time.perf_counter()
        proc = subprocess.run(
            [
                sys.executable, "-m", "docdiff",
                "--old-html", str(html_file),
                "--new-md-dir", str(md_dir),
                "-o", "/dev/null",
                "-q"
            ],
            capture_output=True,
            cwd=str(docdiff_dir),
        )
        elapsed = time.perf_counter() - start
        result.times_ms.append(elapsed * 1000)

    return result


def benchmark_normalizers() -> BenchmarkResult:
    """Benchmark text normalization functions."""
    from docdiff.normalizers import (
        normalize_text,
        normalize_whitespace,
        strip_formatting,
        similarity_ratio,
    )

    # Sample texts of varying lengths
    short_text = "This is a short sample text with some **markdown** formatting."
    medium_text = short_text * 10
    long_text = short_text * 100

    def bench():
        # Normalize various text lengths
        for text in [short_text, medium_text, long_text]:
            normalize_text(text)
            normalize_whitespace(text)
            strip_formatting(text)

        # Similarity comparisons
        for _ in range(100):
            similarity_ratio(short_text, short_text[:40])
            similarity_ratio(medium_text, medium_text[:200])

    return run_benchmark("normalizers", bench, iterations=10)


def benchmark_memory_html() -> Dict[str, float]:
    """Profile memory usage for HTML extraction."""
    from docdiff.extractors.html_extractor import extract_from_file

    html_file = Path(__file__).parent.parent / "data" / "RobotFrameworkUserGuide.html"
    if not html_file.exists():
        return {"current_mb": 0, "peak_mb": 0}

    gc.collect()
    tracemalloc.start()

    sections = extract_from_file(str(html_file))

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "current_mb": current / 1024 / 1024,
        "peak_mb": peak / 1024 / 1024,
        "sections": len(sections),
    }


def benchmark_memory_md() -> Dict[str, float]:
    """Profile memory usage for Markdown extraction."""
    from docdiff.extractors.md_extractor import extract_from_directory

    md_dir = Path("/home/many/workspace/robotframework/doc/userguide-mkdocs/docs")
    if not md_dir.exists():
        return {"current_mb": 0, "peak_mb": 0}

    gc.collect()
    tracemalloc.start()

    sections_by_file = extract_from_directory(str(md_dir))

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    total_sections = sum(len(s) for s in sections_by_file.values())

    return {
        "current_mb": current / 1024 / 1024,
        "peak_mb": peak / 1024 / 1024,
        "files": len(sections_by_file),
        "sections": total_sections,
    }


def benchmark_memory_full() -> Dict[str, float]:
    """Profile memory usage for full pipeline."""
    from docdiff.extractors.html_extractor import extract_from_file
    from docdiff.extractors.md_extractor import extract_from_directory
    from docdiff.aligners import align_sections
    from docdiff.comparators.content_comparator import compare_section
    from docdiff.cli import flatten_all_sections

    html_file = Path(__file__).parent.parent / "data" / "RobotFrameworkUserGuide.html"
    md_dir = Path("/home/many/workspace/robotframework/doc/userguide-mkdocs/docs")

    if not html_file.exists() or not md_dir.exists():
        return {"current_mb": 0, "peak_mb": 0}

    gc.collect()
    tracemalloc.start()

    # Full pipeline
    html_sections = extract_from_file(str(html_file))
    md_sections_by_file = extract_from_directory(str(md_dir))
    md_sections = []
    for sections in md_sections_by_file.values():
        md_sections.extend(sections)

    html_flat = flatten_all_sections(html_sections)
    md_flat = flatten_all_sections(md_sections)
    alignment = align_sections(html_flat, md_flat)

    findings = []
    for old_section, new_section in alignment.matched:
        try:
            _, section_findings = compare_section(old_section, new_section)
            findings.extend(section_findings)
        except Exception:
            # Handle edge cases in comparators gracefully
            pass

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "current_mb": current / 1024 / 1024,
        "peak_mb": peak / 1024 / 1024,
        "html_sections": len(html_flat),
        "md_sections": len(md_flat),
        "matched": len(alignment.matched),
        "findings": len(findings),
    }


def count_blocks_by_type() -> Dict[str, int]:
    """Count blocks by type for profiling insights."""
    from docdiff.extractors.html_extractor import extract_from_file
    from docdiff.cli import flatten_all_sections

    html_file = Path(__file__).parent.parent / "data" / "RobotFrameworkUserGuide.html"
    if not html_file.exists():
        return {}

    sections = extract_from_file(str(html_file))
    flat = flatten_all_sections(sections)

    counts: Dict[str, int] = {}
    for section in flat:
        for block in section.blocks:
            block_type = str(block.block_type)
            counts[block_type] = counts.get(block_type, 0) + 1

    return counts


def print_results(results: List[BenchmarkResult], memory_results: Dict[str, Any]) -> None:
    """Print benchmark results in a formatted table."""
    print("\n" + "=" * 70)
    print("BENCHMARK RESULTS")
    print("=" * 70)

    print("\n## Timing Benchmarks")
    print("-" * 70)
    print(f"{'Benchmark':<25} {'Mean':>10} {'StdDev':>10} {'Min':>10} {'Max':>10}")
    print("-" * 70)

    for r in results:
        if r.iterations > 0:
            print(f"{r.name:<25} {r.mean_ms:>9.1f}ms {r.stdev_ms:>9.1f}ms {r.min_ms:>9.1f}ms {r.max_ms:>9.1f}ms")

    print("\n## Memory Usage")
    print("-" * 70)

    for name, data in memory_results.items():
        if isinstance(data, dict) and "peak_mb" in data:
            print(f"{name}:")
            for key, value in data.items():
                if "mb" in key.lower():
                    print(f"  {key}: {value:.2f} MB")
                else:
                    print(f"  {key}: {value}")

    print("\n## Performance Analysis")
    print("-" * 70)

    # Calculate totals
    extraction_total = sum(r.mean_ms for r in results if "extraction" in r.name)
    alignment_time = next((r.mean_ms for r in results if r.name == "alignment"), 0)
    comparison_time = next((r.mean_ms for r in results if r.name == "comparison"), 0)
    full_pipeline_time = next((r.mean_ms for r in results if r.name == "full_pipeline"), 0)

    print(f"Extraction total: {extraction_total:.1f}ms")
    print(f"Alignment: {alignment_time:.1f}ms")
    print(f"Comparison: {comparison_time:.1f}ms")
    print(f"Full pipeline: {full_pipeline_time:.1f}ms ({full_pipeline_time/1000:.2f}s)")

    if full_pipeline_time > 0:
        overhead = full_pipeline_time - (extraction_total + alignment_time + comparison_time)
        print(f"Overhead (I/O, reporting, etc.): {overhead:.1f}ms")


def main():
    """Run all benchmarks and output results."""
    print("DocdDiff Performance Benchmarks")
    print("=" * 70)
    print(f"Python: {sys.version}")
    print(f"Working directory: {Path.cwd()}")
    print()

    results = []
    memory_results = {}

    # Run timing benchmarks
    print("Running timing benchmarks...")

    print("  - HTML extraction...")
    results.append(benchmark_html_extraction())

    print("  - Markdown extraction...")
    results.append(benchmark_md_extraction())

    print("  - Section alignment...")
    results.append(benchmark_alignment())

    print("  - Content comparison...")
    results.append(benchmark_comparison())

    print("  - Normalizers...")
    results.append(benchmark_normalizers())

    print("  - Full pipeline...")
    results.append(benchmark_full_pipeline())

    # Run memory benchmarks
    print("\nRunning memory benchmarks...")

    print("  - HTML extraction memory...")
    memory_results["html_extraction"] = benchmark_memory_html()

    print("  - Markdown extraction memory...")
    memory_results["md_extraction"] = benchmark_memory_md()

    print("  - Full pipeline memory...")
    memory_results["full_pipeline"] = benchmark_memory_full()

    # Count blocks
    print("\nCounting block types...")
    block_counts = count_blocks_by_type()
    memory_results["block_counts"] = block_counts

    # Print results
    print_results(results, memory_results)

    # Performance targets check
    print("\n## Target Performance Check")
    print("-" * 70)

    full_time = next((r.mean_ms for r in results if r.name == "full_pipeline"), 0)
    full_memory = memory_results.get("full_pipeline", {}).get("peak_mb", 0)

    targets = [
        ("Full pipeline < 45s", full_time < 45000, f"{full_time/1000:.2f}s"),
        ("Memory < 100MB", full_memory < 100, f"{full_memory:.2f}MB"),
    ]

    for name, passed, actual in targets:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name} (actual: {actual})")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
