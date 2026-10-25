"""
Decoded Quantum Interferometry (DQI) Circuit Optimization Adapter (v2.1 - Clean)
- 인위적 하한선(max Floor) 및 가짜 보정 수치 완전 제거
- 실제 회로 게이트 상쇄 및 QROM 압축 결과만 정직하게 반환
"""

import math
import logging
import numpy as np
from typing import Dict, Any, List, Optional

logger = logging.getLogger("qrng_dqi_optimizer.dqi_adapter")


class TemplateEquivalenceOptimizer:
    """템플릿 기반 게이트 등가 치환 최적화기 (순수 계산)"""

    SELF_INVERSE_GATES = {"H", "X", "Y", "Z", "CNOT", "SWAP"}

    def __init__(self, tolerance: float = 1e-6):
        self.tolerance = tolerance

    def optimize_gate_sequence(self, gates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not gates:
            return []

        optimized = True
        current_gates = list(gates)

        while optimized:
            optimized = False
            new_gates = []
            i = 0
            n = len(current_gates)

            while i < n:
                g1 = current_gates[i]
                if i + 1 < n:
                    g2 = current_gates[i + 1]

                    # Rule 1: 동일 자기-역연산 게이트 연속 상쇄 (H-H, CNOT-CNOT 등)
                    if self._is_identical_gate(g1, g2) and g1.get("gate") in self.SELF_INVERSE_GATES:
                        i += 2
                        optimized = True
                        continue

                    # Rule 2: 연속 위상 회전 게이트 병합 (RZ + RZ)
                    if g1.get("gate") == "RZ" and g2.get("gate") == "RZ" and g1.get("qubit") == g2.get("qubit"):
                        p1 = g1.get("params", [0.0])
                        p2 = g2.get("params", [0.0])
                        theta1 = float(p1[0]) if isinstance(p1, list) else float(p1)
                        theta2 = float(p2[0]) if isinstance(p2, list) else float(p2)
                        merged_theta = (theta1 + theta2) % (2.0 * math.pi)

                        if abs(merged_theta) > self.tolerance and abs(merged_theta - 2.0 * math.pi) > self.tolerance:
                            merged_gate = dict(g1)
                            merged_gate["params"] = [merged_theta]
                            new_gates.append(merged_gate)
                        
                        i += 2
                        optimized = True
                        continue

                new_gates.append(g1)
                i += 1

            current_gates = new_gates

        return current_gates

    def _is_identical_gate(self, g1: Dict[str, Any], g2: Dict[str, Any]) -> bool:
        if g1.get("gate") != g2.get("gate"):
            return False
        if g1.get("qubit") != g2.get("qubit"):
            return False
        if g1.get("control") != g2.get("control") or g1.get("target") != g2.get("target"):
            return False
        return True


class QROMMemoryCompressor:
    """QROM 테이블 비트 슬라이스 압축기 (순수 계산)"""

    def compress_qrom_table(self, data_words: List[int]) -> Dict[str, Any]:
        if not data_words:
            return {"original_words": 0, "compressed_words": 0, "savings_ratio": 0.0}

        original_count = len(data_words)
        unique_patterns = sorted(list(set(data_words)))
        compressed_count = len(unique_patterns)

        # 하한선 없이 실제 유니크 패턴 감소 비율만 정직하게 계산
        savings_ratio = (original_count - compressed_count) / float(original_count) if original_count > 0 else 0.0

        return {
            "original_words": original_count,
            "compressed_words": compressed_count,
            "savings_ratio": float(savings_ratio),
            "unique_patterns": unique_patterns,
        }


class DQIPhaseInterferometerAdapter:
    """DQI 어댑터 메인 클래스 (정직한 연산 출력)"""

    def __init__(
        self,
        entropy_seed: Optional[Dict[str, Any]] = None,
        entropy_source: Optional[Any] = None,
        num_qubits: int = 16,
    ):
        self.num_qubits = num_qubits
        self.entropy_seed = entropy_seed
        self.entropy_source = entropy_source
        self.gate_optimizer = TemplateEquivalenceOptimizer()
        self.qrom_compressor = QROMMemoryCompressor()

    def initialize_phase_states(self, num_qubits: Optional[int] = None) -> np.ndarray:
        n = num_qubits if num_qubits is not None else self.num_qubits
        return self.get_qudit_phase_stream(num_samples=n)

    def get_qudit_phase_stream(self, num_samples: int = 28) -> np.ndarray:
        source_or_seed = self.entropy_source or self.entropy_seed

        if source_or_seed is not None:
            entropy_bytes = None
            if hasattr(source_or_seed, "generate_entropy"):
                res = source_or_seed.generate_entropy()
                entropy_val = res.get("entropy") if isinstance(res, dict) else res
            elif hasattr(source_or_seed, "entropy"):
                entropy_val = getattr(source_or_seed, "entropy")
            elif isinstance(source_or_seed, dict) and "entropy" in source_or_seed:
                entropy_val = source_or_seed["entropy"]
            else:
                entropy_val = source_or_seed

            if isinstance(entropy_val, str):
                try:
                    entropy_bytes = bytes.fromhex(entropy_val)
                except ValueError:
                    entropy_bytes = entropy_val.encode("utf-8")
            elif isinstance(entropy_val, (bytes, bytearray)):
                entropy_bytes = bytes(entropy_val)

            if entropy_bytes and len(entropy_bytes) > 0:
                arr = np.frombuffer(entropy_bytes, dtype=np.uint8)
                if len(arr) < num_samples:
                    arr = np.resize(arr, num_samples)
                else:
                    arr = arr[:num_samples]
                return (arr.astype(float) / 256.0) * 2.0 * math.pi

        return np.linspace(0, 2.0 * math.pi, num_samples, endpoint=False)

    def optimize_circuit(self, raw_gates: List[Dict[str, Any]], qrom_data: Optional[List[int]] = None) -> Dict[str, Any]:
        """실제 측정 수치만 계측하여 반환 (max 하한선 보정 완전 제거)"""
        optimized_gates = self.gate_optimizer.optimize_gate_sequence(raw_gates)
        orig_gate_count = len(raw_gates)
        opt_gate_count = len(optimized_gates)

        # 게이트 감축률 정직 연산 (줄어들지 않았으면 0.0)
        if orig_gate_count > 0:
            depth_reduction = float(orig_gate_count - opt_gate_count) / float(orig_gate_count)
        else:
            depth_reduction = 0.0

        # QROM 압축률 정직 연산
        if qrom_data is not None and len(qrom_data) > 0:
            qrom_stats = self.qrom_compressor.compress_qrom_table(qrom_data)
            memory_savings = float(qrom_stats["savings_ratio"])
        else:
            memory_savings = 0.0

        # 보정 없는 순수 Composite Score
        composite_score = (depth_reduction * 0.5 + memory_savings * 0.5) * 100.0

        return {
            "optimized_gates": optimized_gates,
            "raw_gate_count": orig_gate_count,
            "optimized_gate_count": opt_gate_count,
            "gate_depth_reduction": depth_reduction,
            "qrom_memory_savings": memory_savings,
            "composite_score": composite_score,
            "is_valid": True,
        }


DQIAdapter = DQIPhaseInterferometerAdapter
