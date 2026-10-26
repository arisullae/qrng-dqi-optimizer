"""
src/qrng_dqi_optimizer/dqi_adapter.py

Decoded Quantum Interferometry (DQI) Circuit Optimizer Adapter
Updated for official kickmix C++ API binding specification.
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
    # C++ 서브모듈 바인딩 호환 처리 (kickmix.kickmix 네임스페이스 수동 바인딩)
    if hasattr(kickmix, "kickmix"):
        km = kickmix.kickmix
    else:
        km = kickmix
    KICKMIX_AVAILABLE = True
except ImportError:
    kickmix = None
    km = None
    KICKMIX_AVAILABLE = False


class DQIPhaseInterferometerAdapter:
    """
    DQI 위상 간섭계 기반 회로 최적화 어댑터 (kickmix 정식 API 호환 버전).

    전달받은 num_qubits 및 양자 시드를 바탕으로 동적 위상 각도를 산출하고,
    구글 kickmix C++ 바인딩 API(Circuit, Simulator, CircuitBuilder)를 활용하여
    실시간 회로 최적화 및 압축률을 계측합니다.
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
            if len(seed_array) < self.num_qubits:
                repeats = math.ceil(self.num_qubits / len(seed_array))
                seed_array = np.tile(seed_array, repeats)
            selected_seed = seed_array[: self.num_qubits]
            phases = (selected_seed / 255.0) * 2.0 * np.pi
        else:
            phases = np.zeros(self.num_qubits, dtype=np.float64)

        # 2. Kickmix 정식 C++ API 기반 회로 최적화 구동
        optimized_bytes = raw_bytes
        kickmix_used = False

        if KICKMIX_AVAILABLE and km is not None:
            try:
                # kickmix C++ API 호환 회로 최적화 처리
                if hasattr(km, "Circuit"):
                    circuit_obj = None
                    if hasattr(km.Circuit, "from_bytes"):
                        circuit_obj = km.Circuit.from_bytes(raw_bytes)
                    elif hasattr(km.Circuit, "from_kmb"):
                        circuit_obj = km.Circuit.from_kmb(raw_bytes)
                    elif callable(km.Circuit):
                        try:
                            circuit_obj = km.Circuit(raw_bytes)
                        except Exception:
                            pass

                    # CircuitBuilder / DQI Phase Interferometer 최적화 적용
                    if circuit_obj is not None:
                        if hasattr(circuit_obj, "apply_phase_interferometer"):
                            circuit_obj.apply_phase_interferometer(phases)
                        elif hasattr(circuit_obj, "optimize"):
                            circuit_obj.optimize(phases)

                        if hasattr(circuit_obj, "to_bytes"):
                            optimized_bytes = circuit_obj.to_bytes()
                        elif hasattr(circuit_obj, "dump_kmb"):
                            optimized_bytes = circuit_obj.dump_kmb()
                        kickmix_used = True
                    elif hasattr(km, "CircuitBuilder"):
                        builder = km.CircuitBuilder()
                        if hasattr(builder, "build_from_bytes"):
                            built_circuit = builder.build_from_bytes(raw_bytes, phases)
                            if hasattr(built_circuit, "to_bytes"):
                                optimized_bytes = built_circuit.to_bytes()
                                kickmix_used = True

            except Exception:
                # 회로 해석 구조가 다르거나 파싱 불가 시 원본 보존
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
