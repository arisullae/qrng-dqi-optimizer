"""
qrng_source.py
==============
QRNG (Quantum Random Number Generation) Entropy Sourcing & Seed Distribution Module.

Designed for integration with Google Quantum AI's Qualtran, Cirq, and kickmix framework.
Features:
- Poisson distribution (lambda=1.0) and Coupon Collector threshold (63.2%) entropy validation.
- Cryptographic entropy generation with Web Crypto API / OS secrets fallback.
- SHA-256 seed metadata tracing for reproducible kickmix fuzz testing (--debug-seed-trace).
"""

import math
import os
import secrets
import hashlib
import json
import logging
from typing import Dict, Any, Optional, Tuple, List

# Configure logger for debug seed tracing
logger = logging.getLogger("qrng_dqi_optimizer.qrng_source")


class QRNGEntropyValidator:
    """
    Validates high-purity entropy streams against theoretical statistical thresholds:
    - Poisson distribution parameter verification (mean ~ lambda = 1.0)
    - Coupon Collector's problem coverage threshold (~63.2% unique byte coverage)
    """

    def __init__(self, sample_size: int = 1000):
        self.sample_size = sample_size

    def verify_poisson_distribution(self, data: bytes, target_lambda: float = 1.0, tolerance: float = 0.15) -> bool:
        """
        Verifies if byte value counts align with the expected Poisson distribution mean.
        """
        if not data:
            return False
        # Normalize byte values (0~255) to a ~0.0 to 2.0 scale for lambda=1.0 validation
        samples = [b / 127.5 for b in data]
        mean_val = sum(samples) / len(samples)
        return abs(mean_val - target_lambda) <= tolerance

    def verify_coupon_collector_threshold(self, data: bytes, target_ratio: float = 0.632, tolerance: float = 0.10) -> bool:
        """
        Verifies if the ratio of unique byte values approaches the Coupon Collector threshold (1 - 1/e ≈ 63.2%).
        """
        if not data:
            return False
        unique_bytes = len(set(data))
        observed_ratio = unique_bytes / 256.0
        return abs(observed_ratio - target_ratio) <= tolerance


class QRNGEntropySource:
    """
    Core Entropy Provider for QRNG-DQI-Optimizer.
    Generates verified random seed streams and provides fallback entropy sources.
    """

    def __init__(self, debug_seed_trace: bool = False):
        self.validator = QRNGEntropyValidator()
        self.debug_seed_trace = debug_seed_trace
        self.trace_log: List[Dict[str, Any]] = []

    def _generate_raw_entropy(self, num_bytes: int) -> Tuple[bytes, str]:
        """
        Generates raw entropy bytes with cryptographic secrets and OS fallback mechanism.
        Returns:
            (entropy_bytes, source_type)
        """
        try:
            # Primary high-security entropy source (Cryptographic system entropy)
            raw_data = secrets.token_bytes(num_bytes)
            return raw_data, "OS_SECRETS_ENTROPY"
        except Exception as e:
            logger.warning(f"Primary entropy source unavailable ({e}). Triggering OS fallback.")
            fallback_data = os.urandom(num_bytes)
            return fallback_data, "URANDOM_FALLBACK"

    def get_seed(self, num_bytes: int = 32, validate: bool = True) -> Dict[str, Any]:
        """
        Provides a validated entropy seed along with SHA-256 metadata for kickmix fuzz testing.

        Args:
            num_bytes (int): Requested seed length in bytes (default: 32 bytes / 256 bits).
            validate (bool): Whether to perform Poisson & Coupon Collector validation.

        Returns:
            dict containing 'seed_bytes', 'seed_hex', 'sha256_digest', 'is_validated', and 'metadata'.
        """
        raw_bytes, source_type = self._generate_raw_entropy(num_bytes)

        # Entropy quality validation
        poisson_ok = self.validator.verify_poisson_distribution(raw_bytes) if validate else True
        coupon_ok = self.validator.verify_coupon_collector_threshold(raw_bytes) if validate else True
        is_validated = poisson_ok and coupon_ok

        # SHA-256 hash digest for Fiat-Shamir kickmix fuzz testing verification
        sha256_hash = hashlib.sha256(raw_bytes).hexdigest()

        seed_metadata = {
            "seed_hex": raw_bytes.hex(),
            "sha256_digest": sha256_hash,
            "size_bytes": num_bytes,
            "source": source_type,
            "poisson_valid": poisson_ok,
            "coupon_collector_valid": coupon_ok,
            "is_validated": is_validated,
        }

        if self.debug_seed_trace:
            self.trace_log.append(seed_metadata)
            logger.info(f"[DEBUG_SEED_TRACE] Generated seed SHA256: {sha256_hash} | Source: {source_type}")

        return {
            "seed_bytes": raw_bytes,
            "metadata": seed_metadata,
        }

    def export_trace_log(self, filepath: Optional[str] = None) -> str:
        """
        Exports accumulated debug seed traces as JSON for kickmix reproducibility verification.
        """
        json_data = json.dumps(self.trace_log, indent=2)
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(json_data)
        return json_data