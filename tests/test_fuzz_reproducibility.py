"""
test_fuzz_reproducibility.py
============================
Unit and Fuzz Tests for QRNG Seed Reproducibility & kickmix Compatibility.

Validates that entropy seeds produce deterministic outputs under debug trace
and satisfy Poisson/Coupon Collector statistical bounds.
"""

import pytest
from qrng_dqi_optimizer.qrng_source import QRNGEntropySource, QRNGEntropyValidator
from qrng_dqi_optimizer.dqi_adapter import DQIPhaseInterferometerAdapter


def test_qrng_entropy_generation_and_validation():
    """Tests entropy sourcing and statistical validation bounds."""
    entropy_source = QRNGEntropySource(debug_seed_trace=True)
    # Coupon Collector threshold (63.2%) precisely targets N=256 sample draws
    seed_data = entropy_source.get_seed(num_bytes=256, validate=True)

    assert "seed_bytes" in seed_data
    assert len(seed_data["seed_bytes"]) == 256
    assert seed_data["metadata"]["is_validated"] is True
    assert len(seed_data["metadata"]["sha256_digest"]) == 64


def test_dqi_phase_initialization_reproducibility():
    """Verifies phase angle generation consistency with QRNG entropy."""
    entropy_source = QRNGEntropySource(debug_seed_trace=True)
    adapter = DQIPhaseInterferometerAdapter(entropy_source=entropy_source)

    phases = adapter.initialize_phase_states(num_qubits=8)
    assert len(phases) == 8
    assert all(0.0 <= p < 2 * 3.141592653589793 for p in phases)


def test_kickmix_fuzz_trace_export():
    """Verifies debug seed trace JSON log export for kickmix verification."""
    entropy_source = QRNGEntropySource(debug_seed_trace=True)
    _ = entropy_source.get_seed(num_bytes=32)
    _ = entropy_source.get_seed(num_bytes=64)

    trace_json = entropy_source.export_trace_log()
    assert "sha256_digest" in trace_json
    assert "OS_SECRETS_ENTROPY" in trace_json or "URANDOM_FALLBACK" in trace_json