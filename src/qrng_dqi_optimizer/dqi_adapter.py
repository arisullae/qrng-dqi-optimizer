"""
src/qrng_dqi_optimizer/dqi_adapter.py

Decoded Quantum Interferometry (DQI) Circuit Optimizer Adapter
Updated to use official kickmix `Circuit.from_file` API.
"""

import os
import math
import tempfile
from typing import Any, Dict, Optional
import numpy as np

try:
    import kickmix
    km = getattr(kickmix, "kickmix", kickmix)
    KICKMIX_AVAILABLE = True
except ImportError:
    kickmix = None
    km = None
    KICKMIX_AVAILABLE = False


class DQIPhaseInterferometerAdapter:
    def __init__(self, num_qubits: int = 16):
        self.num_qubits = int(num_qubits)
        self.last_metrics: Dict[str, Any] = {}

    def optimize_circuit(self, raw_bytes: bytes, seed: Optional[bytes] = None) -> bytes:
        if not isinstance(raw_bytes, bytes):
            raise TypeError(f"Input raw_bytes must be of type bytes, got {type(raw_bytes)}")

        # 1. 동적 위상 각도 산출 ([0, 2π) 스케일링)
        if seed is not None and len(seed) > 0:
            seed_array = np.frombuffer(seed, dtype=np.uint8)
            if len(seed_array) < self.num_qubits:
                repeats = math.ceil(self.num_qubits / len(seed_array))
                seed_array = np.tile(seed_array, repeats)
            selected_seed = seed_array[: self.num_qubits]
            phases = (selected_seed / 255.0) * 2.0 * np.pi
        else:
            phases = np.zeros(self.num_qubits, dtype=np.float64)

        optimized_bytes = raw_bytes
        kickmix_used = False

        # 2. kickmix.Circuit.from_file 로딩 및 처리
        if KICKMIX_AVAILABLE and km is not None and hasattr(km, "Circuit"):
            tmp_in = None
            tmp_out = None
            try:
                # 임시 파일 생성 후 C++ from_file 로드
                with tempfile.NamedTemporaryFile(suffix=".kmb", delete=False) as f_in:
                    f_in.write(raw_bytes)
                    tmp_in = f_in.name

                if hasattr(km.Circuit, "from_file"):
                    circuit_obj = km.Circuit.from_file(tmp_in)
                    
                    # 위상 최적화 수행 (제공 메서드 존재 시)
                    if hasattr(circuit_obj, "apply_phase_interferometer"):
                        circuit_obj.apply_phase_interferometer(phases)

                    # 결과 내보내기
                    with tempfile.NamedTemporaryFile(suffix=".kmb", delete=False) as f_out:
                        tmp_out = f_out.name

                    if hasattr(circuit_obj, "to_file"):
                        circuit_obj.to_file(tmp_out)
                        with open(tmp_out, "rb") as rf:
                            optimized_bytes = rf.read()
                        kickmix_used = True
            except Exception as e:
                # 파싱 에러 시 원본 보존
                optimized_bytes = raw_bytes
                kickmix_used = False
            finally:
                if tmp_in and os.path.exists(tmp_in):
                    os.remove(tmp_in)
                if tmp_out and os.path.exists(tmp_out):
                    os.remove(tmp_out)

        # 3. 실측 메트릭 산출
        input_len = len(raw_bytes)
        output_len = len(optimized_bytes)
        bytes_reduction_ratio = (
            round(((input_len - output_len) / input_len) * 100.0, 2)
            if input_len > 0
            else 0.0
        )

        self.last_metrics = {
            "num_qubits": self.num_qubits,
            "phase_angles_sample": phases[:4].tolist() if len(phases) >= 4 else phases.tolist(),
            "input_bytes_len": input_len,
            "output_bytes_len": output_len,
            "bytes_reduction_ratio": bytes_reduction_ratio,
            "kickmix_used": kickmix_used,
        }

        return optimized_bytes
