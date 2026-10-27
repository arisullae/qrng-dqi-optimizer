"""
benchmarks/metrics_evaluator.py
QRNG-DQI-Optimizer 성능 평가 및 동적 메트릭 계측 모듈
"""

import argparse
import os
import sys
import time
from typing import Any, Dict, Optional
import numpy as np

from qrng_dqi_optimizer.dqi_adapter import DQIPhaseInterferometerAdapter

class CircuitMetricsEvaluator:
  """어댑터 실행 성능 및 회로 바이너리 압축률을 동적으로 계측 및 평가하는 클래스"""

  def __init__(self, adapter: Optional[Any] = None):
    self.adapter = adapter

  def evaluate(
      self, raw_bytes: bytes, seed: Optional[bytes] = None
  ) -> Dict[str, Any]:
    """입력 회로 바이너리와 시드를 기반으로 어댑터를 구동하고 정직한 동적 지표를 산출합니다."""
    if self.adapter is None:
      raise ValueError("어댑터 인스턴스가 설정되지 않았습니다.")

    # 1. 환경변수(NUM_QUBITS, SAMPLE_SIZE)를 최우선 동적 반영
    env_qubits = os.environ.get("NUM_QUBITS")
    if env_qubits is not None:
      try:
        target_qubits = int(env_qubits)
        if hasattr(self.adapter, "num_qubits"):
          self.adapter.num_qubits = target_qubits
      except ValueError:
        target_qubits = getattr(self.adapter, "num_qubits", 16)
    else:
      target_qubits = getattr(self.adapter, "num_qubits", 16)

    env_sample_size = os.environ.get("SAMPLE_SIZE")
    if env_sample_size is not None:
      try:
        target_sample_size = int(env_sample_size)
        if hasattr(self.adapter, "sample_size"):
          self.adapter.sample_size = target_sample_size
      except ValueError:
        target_sample_size = getattr(self.adapter, "sample_size", 1024)
    else:
      target_sample_size = getattr(self.adapter, "sample_size", 1024)
          
    start_time = time.perf_counter()

    # 2. 어댑터 구동 및 실제 최적화 회로 바이너리(bytes) 수신
    opt_bytes = self.adapter.optimize_circuit(raw_bytes, seed=seed)

    elapsed_time_ms = (time.perf_counter() - start_time) * 1000.0

    # 3. 어댑터 내부 메트릭 수집 및 동적 압축률 계산
    adapter_metrics = getattr(self.adapter, "last_metrics", {})
    input_len = len(raw_bytes)
    output_len = len(opt_bytes)

    if input_len > 0:
      bytes_reduction_ratio = round(
          ((input_len - output_len) / input_len) * 100.0, 2
      )
    else:
      bytes_reduction_ratio = 0.0

    return {
        "status": "SUCCESS",
        "input_bytes_len": input_len,
        "output_bytes_len": output_len,
        "bytes_reduction_ratio": bytes_reduction_ratio,
        "execution_time_ms": round(elapsed_time_ms, 3),
        "kickmix_used": adapter_metrics.get("kickmix_used", False),
        "num_qubits": adapter_metrics.get("num_qubits", target_qubits),
        "sample_size": adapter_metrics.get("sample_size", target_sample_size),
        "phase_angles_sample": adapter_metrics.get("phase_angles_sample", []),
    }

def print_evaluation_report(metrics: Dict[str, Any]) -> None:
  """CI 콘솔 및 터미널 검증 시 가독성 높은 성능 평가 리포트 출력"""
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
  print(f"  - Sample Size          : {metrics.get('sample_size')}")
  print("==================================================")

if __name__ == "__main__":
  parser = argparse.ArgumentParser(
      description="QRNG-DQI Metrics Evaluator CLI"
  )
  parser.add_argument(
      "--qubits", type=int, default=16, help="Number of active qubits"
  )
  parser.add_argument(
      "--sample-size", type=int, default=1024, help="Sample size"
  )
  args = parser.parse_args()

  # 환경변수(NUM_QUBITS, SAMPLE_SIZE)를 최우선으로 반영하여 어댑터 및 평가기 구동
  final_qubits = int(os.environ.get("NUM_QUBITS", args.qubits))
  final_sample_size = int(os.environ.get("SAMPLE_SIZE", args.sample_size))
  
  # 매트릭스나 인자로 전달받은 (NUM_QUBITS, SAMPLE_SIZE) 적용
  adapter = DQIPhaseInterferometerAdapter(num_qubits=final_qubits)
  if hasattr(adapter, "sample_size"):
    adapter.sample_size = final_sample_size
  evaluator = CircuitMetricsEvaluator(adapter)

  dummy_kmb = b"KMB_HEADER_DUMMY_CIRCUIT_DATA_FOR_TESTING"
  dummy_seed = b"\x00" * final_sample_size

  res = evaluator.evaluate(dummy_kmb, seed=dummy_seed)
  print_evaluation_report(res)
