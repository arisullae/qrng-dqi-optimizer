"""
benchmarks/metrics_evaluator.py
QRNG-DQI-Optimizer 성능 평가 및 동적 메트릭 계측 모듈
"""

import os
import sys
import time
from typing import Any, Dict, Optional


class CircuitMetricsEvaluator:
    """DQI 최적화 어댑터의 실행 성능과 실제 회로 바이너리 압축률을
    하드코딩 수치 없이 동적으로 계측 및 평가하는 클래스.
    """

    def __init__(self, adapter: Optional[Any] = None):
        self.adapter = adapter

    def evaluate(
        self,
        raw_bytes: bytes,
        seed: Optional[bytes] = None,
        seed_stats: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if self.adapter is None:
            raise ValueError("어댑터 인스턴스가 설정되지 않았습니다.")

        start_time = time.perf_counter()

        # 1. 어댑터 구동 및 실제 최적화 회로 바이너리(bytes) 수신
        opt_bytes = self.adapter.optimize_circuit(raw_bytes, seed=seed)
        elapsed_time_ms = (time.perf_counter() - start_time) * 1000.0

        adapter_metrics = getattr(self.adapter, "last_metrics", {})

        input_len = len(raw_bytes)
        output_len = len(opt_bytes)
        bytes_reduction_ratio = (
            round(((input_len - output_len) / input_len) * 100.0, 2)
            if input_len > 0
            else 0.0
        )

        return {
            "status": "SUCCESS",
            "input_bytes_len": input_len,
            "output_bytes_len": output_len,
            "bytes_reduction_ratio": bytes_reduction_ratio,
            "execution_time_ms": round(elapsed_time_ms, 3),
            "kickmix_used": adapter_metrics.get("kickmix_used", False),
            "num_qubits": adapter_metrics.get(
                "num_qubits", getattr(self.adapter, "num_qubits", 16)
            ),
            "phase_angles_sample": adapter_metrics.get("phase_angles_sample", []),
            "seed_stats": seed_stats or {},
        }


def print_evaluation_report(metrics: Dict[str, Any]) -> None:
    print("==================================================")
    print(" 📊 QRNG-DQI-Optimizer Real-Time Performance Report")
    print("==================================================")
    print(f" - Execution Status     : {metrics.get('status')}")
    print(
        f" - Kickmix Framework    : {'Active' if metrics.get('kickmix_used') else 'Fallback Mode'}"
    )
    print(f" - Input Circuit Size   : {metrics.get('input_bytes_len')} bytes")
    print(f" - Output Circuit Size  : {metrics.get('output_bytes_len')} bytes")
    print(f" - Dynamic Reduction    : {metrics.get('bytes_reduction_ratio')}%")
    print(f" - Execution Time       : {metrics.get('execution_time_ms')} ms")
    print(f" - Qubits               : {metrics.get('num_qubits')}")

    seed_stats = metrics.get("seed_stats", {})
    if seed_stats:
        print("--------------------------------------------------")
        print(" ⚛️ Quantum Seed & Entropy Verification Status")
        print("--------------------------------------------------")
        print(f" - Seed Source Type     : {seed_stats.get('source_type', 'N/A')}")
        print(f" - Coupon Score         : {seed_stats.get('coupon_score', 0.0):.4f}")
        print(f" - Entropy Validated    : {seed_stats.get('is_validated', False)}")
        print(f" - SHA-256 Fingerprint  : {seed_stats.get('sha256_fingerprint', 'N/A')[:16]}...")
    print("==================================================")


if __name__ == "__main__":
    # 1. CI 매트릭스 환경변수 파싱
    num_qubits = int(os.environ.get("NUM_QUBITS", 16))
    sample_size = int(os.environ.get("SAMPLE_SIZE", 256))
    circuit_file_path = os.environ.get("CIRCUIT_FILE_PATH", "data/target_circuit.kmb")

    try:
        from qrng_dqi_optimizer.dqi_adapter import DQIPhaseInterferometerAdapter
        from qrng_dqi_optimizer.qrng_source import QRNGEntropySource
    except ImportError:
        from src.qrng_dqi_optimizer.dqi_adapter import DQIPhaseInterferometerAdapter
        from src.qrng_dqi_optimizer.qrng_source import QRNGEntropySource

    # 2. 실제 회로 파일(.kmb / .kmx) 로드 (임시 가짜 더미 바이트 완전 제거)
    if os.path.exists(circuit_file_path):
        with open(circuit_file_path, "rb") as f:
            raw_circuit_bytes = f.read()
    else:
        # 회로 파일이 존재하지 않을 경우 파일 경로 탐색 안내 후 종료
        print(f"[Notice] Circuit file not found at '{circuit_file_path}'.")
        print("Place a valid .kmb or .kmx circuit file in the target directory.")
        sys.exit(0)

    # 3. 양자 난수 시드 공급 및 어댑터 평가 구동
    qrng_source = QRNGEntropySource()
    raw_seed, seed_stats = qrng_source.get_entropy_seed(num_bytes=sample_size)

    test_adapter = DQIPhaseInterferometerAdapter(num_qubits=num_qubits)
    evaluator = CircuitMetricsEvaluator(test_adapter)

    res = evaluator.evaluate(raw_circuit_bytes, seed=raw_seed, seed_stats=seed_stats)
    print_evaluation_report(res)
