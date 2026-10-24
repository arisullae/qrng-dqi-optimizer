"""
QRNG Entropy Sourcing & Seed Distribution Module (v1.1)
- 기존 SHA-256 디버그 트레이스 및 통계 검증 모듈 100% 보존
- [v1.1 신규] 28-Qudit 차원 고순도 위상 벡터 스트림 추가
"""

import math
import os
import secrets
import hashlib
import json
import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger("qrng_dqi_optimizer.qrng_source")


class QRNGEntropyValidator:
    """[기존 보존] 포아송 분산 및 쿠폰 수집가 검증 클래스"""

    def __init__(self, sample_size: int = 1000):
        self.sample_size = sample_size

    def verify_poisson_distribution(self, data: bytes, target_lambda: float = 1.0, tolerance: float = 0.5) -> bool:
        if not data:
            return False
        arr = np.frombuffer(data, dtype=np.uint8)
        mean_val = np.mean(arr)
        var_val = np.var(arr)
        if mean_val == 0:
            return False
        return abs((var_val / mean_val) - target_lambda) <= tolerance

    def verify_coupon_collector_threshold(self, data: bytes, target_ratio: float = 0.632, tolerance: float = 0.10) -> bool:
        if not data:
            return False
        unique_bytes = len(set(data[:256]))
        observed_ratio = unique_bytes / 256.0
        return observed_ratio >= (target_ratio - tolerance)


class QRNGEntropySource:
    """[기존 보존 + v1.1 신규] 엔트로피 메인 소스 공급자"""

    def __init__(self, debug_seed_trace: bool = False, dimension: int = 28):
        self.validator = QRNGEntropyValidator()
        self.debug_seed_trace = debug_seed_trace
        self.trace_log: List[Dict[str, Any]] = []
        self.dimension = dimension

    def _generate_raw_entropy(self, num_bytes: int) -> Tuple[bytes, str]:
        try:
            raw_data = secrets.token_bytes(num_bytes)
            return raw_data, "OS_SECRETS_ENTROPY"
        except Exception as e:
            logger.warning(f"Primary entropy source unavailable ({e}). Triggering OS fallback.")
            fallback_data = os.urandom(num_bytes)
            return fallback_data, "URANDOM_FALLBACK"

    def get_seed(self, num_bytes: int = 32, validate: bool = True) -> Dict[str, Any]:
        """[기존 보존] SHA-256 트레이스 메타데이터를 포함한 씨드 제공 메서드"""
        raw_bytes, source_type = self._generate_raw_entropy(num_bytes)

        poisson_ok = self.validator.verify_poisson_distribution(raw_bytes) if validate else True
        coupon_ok = self.validator.verify_coupon_collector_threshold(raw_bytes) if validate else True
        is_validated = poisson_ok and coupon_ok

        sha256_hash = hashlib.sha256(raw_bytes).hexdigest()

        seed_metadata = {
            "seed_hex": raw_bytes.hex(),
            "sha256_digest": sha256_hash,
            "size_bytes": num_bytes,
            "source": source_type,
            "poisson_valid": poisson_ok,
            "coupon_collector_valid": coupon_ok,
            "is_validated": is_validated,
        }

        if self.debug_seed_trace:
            self.trace_log.append(seed_metadata)
            logger.info(f"[DEBUG_SEED_TRACE] Generated seed SHA256: {sha256_hash} | Source: {source_type}")

        return {
            "seed_bytes": raw_bytes,
            "metadata": seed_metadata,
        }

    def export_trace_log(self, filepath: Optional[str] = None) -> str:
        """[기존 보존] kickmix 퍼즈 재현성 검증용 JSON 로그 내보내기"""
        json_data = json.dumps(self.trace_log, indent=2)
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(json_data)
        return json_data

    def get_qudit_phase_stream(self, num_samples: int = 1024) -> np.ndarray:
        """[v1.1 신규] 28-Qudit 차원 고순도 엔트로피 각도 섹터 벡터 생성"""
        raw_bytes, _ = self._generate_raw_entropy(num_samples)
        qudit_indices = np.frombuffer(raw_bytes, dtype=np.uint8) % self.dimension
        qudit_phases = (2.0 * np.pi / self.dimension) * qudit_indices
        return qudit_phases
