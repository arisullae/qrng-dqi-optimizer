"""
QRNG-DQI-Optimizer Benchmark Evaluator
Path: benchmarks/metrics_evaluator.py

Google Quantum AI $150K Circuit Compression Competition & kickmix schema compatible.
Evaluates genuine quantum entropy seeding and DQI circuit optimization performance metrics.
"""

import os
import sys
import json
from typing import Dict, Any, Optional

# src/ 및 프로젝트 루트 경로를 sys.path에 추가하여 모듈 임포트 보장
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from qrng_dqi_optimizer.qrng_source import QRNGEntropySource
    from qrng_dqi_optimizer.dqi_adapter import DQIPhaseInterferometerAdapter
except ImportError:
    # 패키지 구조에 따른 직접 모듈 임포트 폴백
    from qrng_source import QRNGEntropySource
    from dqi_adapter import DQIPhaseInterferometerAdapter


class MetricsEvaluator:
    """
    Google Quantum AI $150K Competition 규격 벤치마크 평가기
    """

    def __init__(self, pass_threshold: float = 30.0):
        """
        :param pass_threshold: CI 통과를 위한 최소 종합 점수 임계치 (기본 30.0점)
        """
        self.pass_threshold = pass_threshold

    def evaluate(self, compiled_result: Dict[str, Any], entropy_stats: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        DQIPhaseInterferometerAdapter의 최적화 결과를 검증하고 최종 벤치마크 점수 산출
        """
        g_red = compiled_result.get("gate_depth_reduction", 0.0)
        q_sav = compiled_result.get("qrom_memory_savings", 0.0)
        comp = compiled_result.get("composite_score", 0.0)
        kickmix = compiled_result.get("kickmix_compatible", True)

        # 합격 여부 검증 (종합 점수가 임계치 이상이고 kickmix 호환 규격 일치 시 PASS)
        is_passed = (comp >= self.pass_threshold) and kickmix

        report = {
            "gate_depth_reduction": g_red,
            "qrom_memory_savings": q_sav,
            "composite_score": comp,
            "kickmix_compatible": kickmix,
            "is_passed": is_passed,
            "pass_threshold": self.pass_threshold,
            "entropy_stats": entropy_stats or {}
        }
        return report

    def run_full_evaluation(self, num_bytes: int = 256, num_qubits: int = 16) -> Dict[str, Any]:
        """
        양자 엔트로피 수급부터 DQI 위상 최적화 및 최종 벤치마크 평가까지 전체 파이프라인 수행
        """
        # 1. QRNG 양자 엔트로피 수급
        qrng = QRNGEntropySource()
        seed_bytes, stats = qrng.get_entropy_seed(num_bytes=num_bytes)

        # 2. DQI 위상 간섭계 회로 최적화 수행
        adapter = DQIPhaseInterferometerAdapter(num_qubits=num_qubits)
        compiled = adapter.optimize_circuit(entropy_seed=seed_bytes)

        # 3. 최종 성능 평가 및 리포트 작성
        eval_report = self.evaluate(compiled, entropy_stats=stats)
        return eval_report


def main():
    print("==================================================")
    print(" ⚛️  QRNG-DQI-Optimizer Benchmark II Evaluation ")
    print("==================================================")

    evaluator = MetricsEvaluator(pass_threshold=30.0)
    report = evaluator.run_full_evaluation(num_bytes=256, num_qubits=16)

    entropy_stats = report.get("entropy_stats", {})

    print("\n [1] QRNG 엔트로피 시드 수급 상태")
    print(f"  - 소스 유형    : {entropy_stats.get('source_type', 'N/A')}")
    print(f"  - 시드 길이    : {entropy_stats.get('seed_bytes_len', 0)} bytes")
    print(f"  - 쿠폰 점수    : {entropy_stats.get('coupon_score', 0.0):.1%}")
    print(f"  - SHA256 서명 : {entropy_stats.get('sha256_fingerprint', 'N/A')[:16]}...")

    print("\n [2] DQI 회로 최적화 벤치마크 결과")
    print(f"  - Gate Depth Reduction : {report['gate_depth_reduction']}%")
    print(f"  - QROM Memory Savings  : {report['qrom_memory_savings']}%")
    print(f"  - Composite Score      : {report['composite_score']} 점")
    print(f"  - kickmix Framework    : {'COMPATIBLE' if report['kickmix_compatible'] else 'INCOMPATIBLE'}")

    print("\n [3] 최종 CI 검증 결과")
    if report["is_passed"]:
        print(f"  ✅ [PASS] 종합 점수 ({report['composite_score']})가 합격 기준({report['pass_threshold']})을 충족했습니다.")
    else:
        print(f"  ❌ [FAIL] 종합 점수 ({report['composite_score']})가 합격 기준({report['pass_threshold']})에 미달했습니다.")
    print("==================================================")

    # CI 파이프라인 종료 코드 반환 (합격 시 0, 불합격 시 1)
    if not report["is_passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
