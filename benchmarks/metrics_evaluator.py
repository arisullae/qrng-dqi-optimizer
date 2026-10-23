"""
metrics_evaluator.py
====================
Automated Performance Metrics Evaluator for QRNG-DQI-Optimizer.

Calculates Gate Depth reduction ratios, QROM memory footprint savings,
and outputs standardized score evaluation for competition benchmarks.
"""

import logging
import json
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("qrng_dqi_optimizer.metrics_evaluator")


class MetricsEvaluator:
    """
    Evaluates quantum circuit compression performance metrics.
    Focuses on Gate Depth reduction and QROM memory overhead minimization.
    """

    def __init__(self, target_depth_weight: float = 0.6, qrom_weight: float = 0.4):
        self.target_depth_weight = target_depth_weight
        self.qrom_weight = qrom_weight

    def calculate_depth_reduction(self, baseline_depth: int, compressed_depth: int) -> float:
        """
        Calculates the ratio of gate depth reduction.
        """
        if baseline_depth <= 0:
            return 0.0
        reduction = (baseline_depth - compressed_depth) / baseline_depth
        return max(0.0, reduction)

    def calculate_qrom_footprint_savings(self, baseline_qrom_bytes: int, compressed_qrom_bytes: int) -> float:
        """
        Calculates the percentage of QROM memory footprint saved.
        """
        if baseline_qrom_bytes <= 0:
            return 0.0
        savings = (baseline_qrom_bytes - compressed_qrom_bytes) / baseline_qrom_bytes
        return max(0.0, savings)

    def evaluate_circuit_score(self, baseline_depth: int, compressed_depth: int,
                               baseline_qrom: int, compressed_qrom: int) -> Dict[str, Any]:
        """
        Computes a comprehensive performance score for Google Quantum AI competition guidelines.
        """
        depth_reduction_ratio = self.calculate_depth_reduction(baseline_depth, compressed_depth)
        qrom_savings_ratio = self.calculate_qrom_footprint_savings(baseline_qrom, compressed_qrom)

        # Weighted combined score
        composite_score = (depth_reduction_ratio * self.target_depth_weight) + (qrom_savings_ratio * self.qrom_weight)

        metrics_summary = {
            "baseline_gate_depth": baseline_depth,
            "compressed_gate_depth": compressed_depth,
            "gate_depth_reduction_pct": round(depth_reduction_ratio * 100, 2),
            "baseline_qrom_bytes": baseline_qrom,
            "compressed_qrom_bytes": compressed_qrom,
            "qrom_savings_pct": round(qrom_savings_ratio * 100, 2),
            "composite_performance_score": round(composite_score * 100, 2),
            "passed_competition_threshold": depth_reduction_ratio >= 0.25 and qrom_savings_ratio >= 0.15
        }

        logger.info(f"Evaluation Complete | Score: {metrics_summary['composite_performance_score']} | Passed Threshold: {metrics_summary['passed_competition_threshold']}")
        return metrics_summary


if __name__ == "__main__":
    evaluator = MetricsEvaluator()
    sample_eval = evaluator.evaluate_circuit_score(
        baseline_depth=1920,
        compressed_depth=1248,
        baseline_qrom=1024,
        compressed_qrom=384
    )
    print(json.dumps(sample_eval, indent=2))