"""
DQI Phase Interferometer Adapter (v1.1)
- 기존 map_entropy_to_phases 및 optimize_circuit 인터페이스 100% 보존
- [v1.1 신규] synthesize_qudit_phases 큐디트 위상 합성 알고리즘 추가
"""

import numpy as np
from typing import Dict, Any, List, Union

class DQIPhaseInterferometerAdapter:

    def __init__(self, num_qubits: int = 16, dimension: int = 28):
        self.num_qubits = num_qubits
        self.dimension = dimension

    def map_entropy_to_phases(self, entropy_bytes: bytes) -> np.ndarray:
        """[기존 보존] 이진 엔트로피 바이트를 위상 각도로 변환"""
        arr = np.frombuffer(entropy_bytes, dtype=np.uint8)
        return (2.0 * np.pi / 256.0) * arr

    def synthesize_qudit_phases(self, qudit_phases: np.ndarray) -> np.ndarray:
        """[v1.1 신규] 고차원 대칭성을 활용한 연속 위상 회전 게이트 등가 상쇄/통합"""
        synthesized = []
        accumulated_phase = 0.0
        
        for phase in qudit_phases:
            accumulated_phase += phase
            accumulated_phase = np.mod(accumulated_phase, 2.0 * np.pi)
            
            if np.isclose(accumulated_phase, 0.0, atol=1e-5) or np.isclose(accumulated_phase, 2.0 * np.pi, atol=1e-5):
                accumulated_phase = 0.0
            else:
                synthesized.append(accumulated_phase)
                
        return np.array(synthesized) if synthesized else np.array([0.0])

    def optimize_circuit(self, raw_phases: Union[np.ndarray, bytes]) -> Dict[str, Any]:
        """[기존 보존 + v1.1 신규 연동] 회로 압축 실행 및 지표 산출"""
        if isinstance(raw_phases, bytes):
            raw_phases = self.map_entropy_to_phases(raw_phases)

        optimized_phases = self.synthesize_qudit_phases(raw_phases)
        
        raw_count = len(raw_phases)
        optimized_count = max(len(optimized_phases), 1)
        depth_reduction = ((raw_count - optimized_count) / max(raw_count, 1)) * 100.0
        
        return {
            "raw_gate_count": raw_count,
            "optimized_gate_count": optimized_count,
            "depth_reduction_ratio": max(depth_reduction, 0.0),
            "optimized_phases": optimized_phases
        }
