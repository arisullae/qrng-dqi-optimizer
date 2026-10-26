"""
benchmarks/metrics_evaluator.py
QRNG-DQI-Optimizer 성능 평가 및 동적 메트릭 계측 모듈
"""

import time
from typing import Any, Dict, Optional
import numpy as np


class CircuitMetricsEvaluator:
  """DQI 최적화 어댑터의 실행 성능과 실제 회로 바이너리 압축률을

  하드코딩 수치 없이 동적으로 계측 및 평가하는 클래스.
  """

  def __init__(self, adapter: Optional[Any] = None):
    self.adapter = adapter

  def evaluate(
      self, raw_bytes: bytes, seed: Optional[bytes] = None
  ) -> Dict[str, Any]:
    """입력 회로 바이너리(raw_bytes)와 시드를 기반으로 어댑터를 구동하고,

    실제 측정된 정직한 동적 지표를 산출합니다.
    """
    if self.adapter is None:
      raise ValueError(
          "어댑터 인스턴스가 설정되지 않았습니다. (Adapter instance is required)"
      )

    start_time = time.perf_counter()

    # 1. 어댑터 구동 및 실제 최적화 회로 바이너리(bytes) 수신
    opt_bytes = self.adapter.optimize_circuit(raw_bytes, seed=seed)

    elapsed_time_ms = (time.perf_counter() - start_time) * 1000.0

    # 2. 어댑터 내부 기록 메트릭 수집
    adapter_metrics = getattr(self.adapter, "last_metrics", {})

    # 3. [하드코딩 보정 제거] 실제 입출력 바이트 크기 기반 동적 압축률 직접 계산
    input_len = len(raw_bytes)
    output_len = len(opt_bytes)

    if input_len > 0:
      bytes_reduction_ratio = round(
          ((input_len - output_len) / input_len) * 100.0, 2
      )
    else:
      bytes_reduction_ratio = 0.0

    # 4. 최종 정직한 동적 평가 메트릭 딕셔너리 생성
    evaluation_result = {
        "status": "SUCCESS",
        "input_bytes_len": input_len,
        "output_bytes_len": output_len,
        "bytes_reduction_ratio": bytes_reduction_ratio,  # 동적 계산 수치
        "execution_time_ms": round(elapsed_time_ms, 3),  # 실시간 소요 시간
        "kickmix_used": adapter_metrics.get("kickmix_used", False),
        "num_qubits": adapter_metrics.get(
            "num_qubits", getattr(self.adapter, "num_qubits", 16)
        ),
        "phase_angles_sample": adapter_metrics.get("phase_angles_sample", []),
    }

    return evaluation_result


def print_evaluation_report(metrics: Dict[str, Any]) -> None:
  """CI 콘솔 및 터미널 검증 시 가독성 높은 성능 평가 리포트를 출력하는 함수"""
  print("==================================================")
  print(" 📊 QRNG-DQI-Optimizer Real-Time Performance Report")
  print("==================================================")
  print(f"  - Execution Status     : {metrics.get('status')}")
  print(
      "  - Kickmix Framework    :"
      f" {'Active' if metrics.get('kickmix_used') else 'Fallback Mode'}"
  )
  print(f"  - Input Circuit Size   : {metrics.get('input_bytes_len')} bytes")
  print(f"  - Output Circuit Size  : {metrics.get('output_bytes_len')} bytes")
  print(
      "  - Dynamic Reduction    :"
      f" {metrics.get('bytes_reduction_ratio')}%"
  )
  print(f"  - Execution Time       : {metrics.get('execution_time_ms')} ms")
  print(f"  - Qubits               : {metrics.get('num_qubits')}")
  print("==================================================")


if __name__ == "__main__":
  # 모듈 단독 실행 시 테스트 스투브
  from qrng_dqi_optimizer.dqi_adapter import DQIPhaseInterferometerAdapter

  test_adapter = DQIPhaseInterferometerAdapter()
  evaluator = CircuitMetricsEvaluator(test_adapter)

  dummy_kmb = b"KMB_HEADER_DUMMY_CIRCUIT_DATA_FOR_TESTING"
  dummy_seed = b"\x00" * 256

  res = evaluator.evaluate(dummy_kmb, seed=dummy_seed)
  print_evaluation_report(res)
