"""
benchmarks/metrics_evaluator.py
QRNG-DQI-Optimizer 성능 평가 및 동적 메트릭 계측 모듈 (CLI 매트릭스 인자 동적 연동)
"""

import argparse
import sys
import time
from typing import Any, Dict, Optional
import numpy as np

from qrng_dqi_optimizer.dqi_adapter import DQIPhaseInterferometerAdapter


class CircuitMetricsEvaluator:

  def __init__(self, adapter: Optional[Any] = None):
    self.adapter = adapter

  def evaluate(
      self, raw_bytes: bytes, seed: Optional[bytes] = None
  ) -> Dict[str, Any]:
    if self.adapter is None:
      raise ValueError("어댑터 인스턴스가 설정되지 않았습니다.")

  # 어댑터 존재 검증 직후에 환경변수 동기화 코드 삽입
    env_qubits = os.environ.get("NUM_QUBITS")
    if env_qubits is not None:
      try:
        target_qubits = int(env_qubits)
        if hasattr(self.adapter, "num_qubits"):
          self.adapter.num_qubits = target_qubits
      except ValueError:
        pass

    start_time = time.perf_counter()
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
            "num_qubits",
            getattr(self.adapter, "num_qubits", int(os.environ.get("NUM_QUBITS", 16)))
        ),
        "phase_angles_sample": adapter_metrics.get("phase_angles_sample", []),
    }


def print_evaluation_report(metrics: Dict[str, Any]) -> None:
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
  print(f"  - Active Qubits        : {metrics.get('num_qubits')}")
  print("==================================================")


def main():
  # CI 매트릭스 파라미터(--qubits) 동적 파싱 설정
  parser = argparse.ArgumentParser(
      description="QRNG-DQI Real-time Metrics Evaluator"
  )
  parser.add_argument(
      "--qubits",
      type=int,
      default=16,
      help="Number of active qubits from CI matrix (e.g., 32)",
  )
  parser.add_argument(
      "--seed-size", type=int, default=256, help="Seed size in bytes"
  )
  args = parser.parse_args()

  # 매트릭스로 전달받은 큐비트 수치(예: 32)를 어댑터에 동적 바인딩
  adapter = DQIPhaseInterferometerAdapter(num_qubits=args.qubits)
  evaluator = CircuitMetricsEvaluator(adapter)

  dummy_kmb = b"KMB_HEADER_DUMMY_CIRCUIT_DATA_FOR_TESTING"
  dummy_seed = b"\x00" * args.seed_size

  res = evaluator.evaluate(dummy_kmb, seed=dummy_seed)
  print_evaluation_report(res)


if __name__ == "__main__":
  main()
