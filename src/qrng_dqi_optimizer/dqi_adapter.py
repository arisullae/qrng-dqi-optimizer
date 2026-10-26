"""
src/qrng_dqi_optimizer/dqi_adapter.py
Decoded Quantum Interferometry (DQI) Circuit Optimizer Adapter
"""

import math
from typing import Any, Dict, List, Optional
import numpy as np

try:
    import cirq
    CIRQ_AVAILABLE = True
except ImportError:
    cirq = None
    CIRQ_AVAILABLE = False

try:
    import kickmix
    from qualtran import Bloq
    KICKMIX_AVAILABLE = True
except ImportError:
    kickmix = None
    KICKMIX_AVAILABLE = False


class DQIPhaseInterferometerAdapter:
    """
    DQI 위상 간섭계 기반 회로 최적화 어댑터.
    하드코딩 수치 없이 전달받은 num_qubits 및 양자 시드를 바탕으로
    동적 위상 각도를 산출하고 실제 입출력 바이트 크기를 비교하여 실측 압축률을 집계합니다.
    """

    def __init__(self, num_qubits: int = 16):
        self.num_qubits = int(num_qubits)
        self.last_metrics: Dict[str, Any] = {}

    def optimize_circuit(self, raw_bytes: bytes, seed: Optional[bytes] = None) -> bytes:
        if not isinstance(raw_bytes, bytes):
            raise TypeError(f"Input raw_bytes must be of type bytes, got {type(raw_bytes)}")

        # 1. 동적 위상 각도 산출 ([0, 2π) 스케일링)
        if seed is not None and len(seed) > 0:
            seed_array = np.frombuffer(seed, dtype=np.uint8)
            # 전달받은 num_qubits 개수만큼 시드 바이트 슬라이싱 및 확장
            if len(seed_array) < self.num_qubits:
                repeats = math.ceil(self.num_qubits / len(seed_array))
                seed_array = np.tile(seed_array, repeats)
            selected_seed = seed_array[: self.num_qubits]
            phases = (selected_seed / 255.0) * 2.0 * np.pi
        else:
            phases = np.zeros(self.num_qubits, dtype=np.float64)

        # 2. Kickmix 회로 최적화 수행 (Kaggle/Colab의 Active 및 일반 CI의 Fallback 동적 처리)
        if KICKMIX_AVAILABLE and kickmix is not None:
            try:
                circuit_bloq = kickmix.load_kmb_from_bytes(raw_bytes)
                optimized_bloq = kickmix.apply_dqi_phase_interferometer(circuit_bloq, phases)
                optimized_bytes = kickmix.dump_kmb_to_bytes(optimized_bloq)
                kickmix_used = True
            except Exception:
                # 회로 해석 구조가 다를 경우 데이터 손상을 막기 위한 원본 보존
                optimized_bytes = raw_bytes
                kickmix_used = False
        else:
            optimized_bytes = raw_bytes
            kickmix_used = False

        # 3. 실측 입출력 바이트 비교 기반 동적 압축률 계산
        input_len = len(raw_bytes)
        output_len = len(optimized_bytes)

        bytes_reduction_ratio = (
            round(((input_len - output_len) / input_len) * 100.0, 2)
            if input_len > 0
            else 0.0
        )

        # 4. 실측 메트릭 집계
        self.last_metrics = {
            "num_qubits": self.num_qubits,
            "phase_angles_sample": phases[:4].tolist() if len(phases) >= 4 else phases.tolist(),
            "input_bytes_len": input_len,
            "output_bytes_len": output_len,
            "bytes_reduction_ratio": bytes_reduction_ratio,
            "kickmix_used": kickmix_used,
        }

        return optimized_bytes
