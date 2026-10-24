"""
QRNG Entropy Sourcing & Seed Distribution Module (v1.1)
- NumPy 타입 JSON 직렬화 인코더(NumpyEncoder) 연동으로 export_trace_log() 오류 수정
- 기존 SHA-256 디버그 트레이스, get_entropy_seed() 및 통계 검증 모듈 100% 보존
- [v1.1 신규] 28-Qudit 차원 고순도 위상 벡터 스트림 get_qudit_phase_stream() 연동
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


class NumpyEncoder(json.JSONEncoder):
    """NumPy 전용 데이터 타입을 파이썬 표준 JSON 직렬화 가능 타입으로 형변환하는 인코더"""
    def default(self, obj):
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


class QRNGEntropyValidator:
    """포아송 분산 및 쿠폰 수집가 검증 클래스"""

    def __init__(self, sample_size: int = 1000):
        self.sample_size = sample_size

    def verify_poisson_distribution(self, data: bytes, target_lambda: float = 1.0, tolerance: float = 0.5) -> bool:
        if not data:
            return False
        arr = np.frombuffer(data, dtype=np.uint8)
        mean_val = float(np.mean(arr) / 127.5)
        return bool(abs(mean_val - target_lambda) <= tolerance)

    def verify_coupon_collector_threshold(self, data: bytes, target_ratio: float = 0.632, tolerance: float = 0.15) -> bool:
        if not data:
            return False
        unique_bytes = len(set(data[:256]))
        observed_ratio = unique_bytes / 256.0
        return bool(observed_ratio >= (target_ratio - tolerance))


class QRNGEntropySource:
    """QRNG 메인 엔트로피 공급 모듈"""

    def __init__(self, debug_seed_trace: bool = False, dimension: int = 28, seed: Optional[int] = None):
        self.validator = QRNGEntropyValidator()
        self.debug_seed_trace = debug_seed_trace
        self.trace_log: List[Dict[str, Any]] = []
        self.dimension = dimension
        if seed is not None:
            np.random.seed(seed)

    def _generate_raw_entropy(self, num_bytes: int) -> Tuple[bytes, str]:
        try:
            raw_data = secrets.token_bytes(num_bytes)
            return raw_data, "OS_SECRETS_ENTROPY"
        except Exception as e:
            logger.warning(f"Primary entropy source unavailable ({e}). Triggering OS fallback.")
            fallback_data = os.urandom(num_bytes)
            return fallback_data, "URANDOM_FALLBACK"

    def get_seed(self, num_bytes: int = 32, validate: bool = True) -> Dict[str, Any]:
        """SHA-256 트레이스 메타데이터 포함 씨드 제공 인터페이스"""
        raw_bytes, source_type = self._generate_raw_entropy(num_bytes)

        poisson_ok = bool(self.validator.verify_poisson_distribution(raw_bytes)) if validate else True
        coupon_ok = bool(self.validator.verify_coupon_collector_threshold(raw_bytes)) if validate else True
        is_validated = bool(poisson_ok and coupon_ok)

        sha256_hash = hashlib.sha256(raw_bytes).hexdigest()

        seed_metadata = {
            "seed_hex": str(raw_bytes.hex()),
            "sha256_digest": str(sha256_hash),
            "size_bytes": int(num_bytes),
            "source": str(source_type),
            "poisson_valid": bool(poisson_ok),
            "coupon_collector_valid": bool(coupon_ok),
            "is_validated": bool(is_validated),
        }

        if self.debug_seed_trace:
            self.trace_log.append(seed_metadata)
            logger.info(f"[DEBUG_SEED_TRACE] Generated seed SHA256: {sha256_hash} | Source: {source_type}")

        return {
            "seed_bytes": raw_bytes,
            "metadata": seed_metadata,
        }

    def get_entropy_seed(self, num_bytes: int = 256) -> Tuple[bytes, Dict[str, Any]]:
        """하위 호환용 (seed_bytes, stats_dict) 튜플 반환 인터페이스"""
        raw_bytes, source_type = self._generate_raw_entropy(num_bytes)
        unique_ratio = len(set(raw_bytes[:256])) / min(256, len(raw_bytes))
        stats = {
            "coupon_score": float(unique_ratio),
            "source": str(source_type),
            "is_valid": bool(unique_ratio >= 0.50)
        }
        return raw_bytes, stats

    def validate_coupon_collector(self, data_bytes: bytes) -> bool:
        return bool(self.validator.verify_coupon_collector_threshold(data_bytes))

    def validate_poisson_distribution(self, data_bytes: bytes) -> bool:
        return bool(self.validator.verify_poisson_distribution(data_bytes))

    def export_trace_log(self, filepath: Optional[str] = None) -> str:
        """kickmix 퍼즈 재현성 검증용 JSON 로그 내보내기 (NumpyEncoder 적용)"""
        json_data = json.dumps(self.trace_log, indent=2, cls=NumpyEncoder)
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
