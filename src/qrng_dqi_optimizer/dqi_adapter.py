"""
dqi_adapter.py
==============
Framework Adapter for Decoded Quantum Interferometry (DQI) & Google Qualtran / Cirq.

Integrates QRNG entropy sources into DQI phase interferometer initialization
and kickmix compilation pipelines for circuit compression.
"""

import logging
from typing import Dict, Any, Optional, List
import numpy as np

# Cirq and Qualtran optional import check
try:
    import cirq
    CIRQ_AVAILABLE = True
except ImportError:
    CIRQ_AVAILABLE = False

from qrng_dqi_optimizer.qrng_source import QRNGEntropySource

logger = logging.getLogger("qrng_dqi_optimizer.dqi_adapter")


class DQIPhaseInterferometerAdapter:
    """
    Adapter bridging QRNG seeds with DQI initial phase state distribution
    and fault-tolerant Qualtran / Cirq compilation graphs.
    """

    def __init__(self, entropy_source: Optional[QRNGEntropySource] = None):
        self.entropy_source = entropy_source or QRNGEntropySource(debug_seed_trace=True)

    def initialize_phase_states(self, num_qubits: int) -> np.ndarray:
        """
        Generates initial phase angle distribution for DQI interferometer
        using validated QRNG entropy stream.

        Args:
            num_qubits (int): Number of qubits in target DQI circuit block.

        Returns:
            np.ndarray: Array of initial phase angles in range [0, 2*pi).
        """
        # Fetch 32-byte seed from QRNG source
        seed_info = self.entropy_source.get_seed(num_bytes=32)
        seed_bytes = seed_info["seed_bytes"]

        # Convert seed bytes into deterministic numpy random generator
        seed_int = int.from_bytes(seed_bytes[:4], byteorder="big")
        rng = np.random.default_rng(seed_int)

        # Generate phase distribution
        phases = rng.uniform(0, 2 * np.pi, size=num_qubits)
        logger.info(f"Initialized DQI phase states for {num_qubits} qubits using QRNG seed digest: {seed_info['metadata']['sha256_digest'][:12]}...")
        return phases

    def prepare_kickmix_pipeline_input(self, circuit_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formats circuit metadata and entropy seeds for kickmix compiler interface.

        Args:
            circuit_metadata (dict): Metadata containing circuit depth, target QROM footprint, etc.

        Returns:
            dict: Structured configuration ready for kickmix compiler execution.
        """
        seed_data = self.entropy_source.get_seed(num_bytes=64)

        kickmix_config = {
            "target_gate_depth_reduction": circuit_metadata.get("target_depth_reduction", 0.30),
            "qrom_footprint_limit": circuit_metadata.get("qrom_limit", 1024),
            "seed_hash": seed_data["metadata"]["sha256_digest"],
            "fuzz_reproducibility_trace": seed_data["metadata"]["seed_hex"],
            "cirq_compatibility": CIRQ_AVAILABLE,
        }

        return kickmix_config