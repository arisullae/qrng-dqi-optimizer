"""
Silicon-28 QRNG Entropy Source & Validator Interface Module
Path: src/qrng_dqi_optimizer/qrng_source.py
"""

import os
import sys
import math
import json
import hashlib
import numpy as np
from typing import Tuple, Dict, Any, Optional


class QRNGEntropyValidator:
    """양자 엔트로피 시드 및 쿠폰 수집가(Coupon Collector) 신뢰성 검증 클래스"""

    @staticmethod
    def validate_coupon_score(raw_bytes: bytes) -> Dict[str, Any]:
        if not raw_bytes or len(raw_bytes) == 0:
            return {"unique_bytes_count": 0, "coupon_score": 0.0, "is_valid": False}

        unique_bytes_count = len(set(raw_bytes))
        max_possible_unique = min(256, len(raw_bytes))
        coupon_score = unique_bytes_count / float(max_possible_unique)

        return {
            "unique_bytes_count": unique_bytes_count,
            "coupon_score": coupon_score,
            "is_valid": coupon_score >= 0.50
        }

    @staticmethod
    def validate_seed(raw_bytes: bytes) -> bool:
        res = QRNGEntropyValidator.validate_coupon_score(raw_bytes)
        return res["is_valid"]


class QRNGEntropySource:
    """Si-28 포논 양자 엔트로피 수급기 및 신뢰성 검증 모듈"""

    def __init__(
        self,
        seed_path: str = "data/verified_si28_bits.npy",
        debug_seed_trace: bool = False,
        **kwargs
    ):
        self.seed_path = seed_path
        self.debug_seed_trace = debug_seed_trace
        self.last_trace: Dict[str, Any] = {}

    def _trigger_seed_generation(self) -> bool:
        try:
            sys.path.append(os.getcwd())
            from generate_seed import generate_and_save_si28_seed
            generate_and_save_si28_seed(bit_length=1000000, num_runs=1)
            return True
        except Exception:
            return False

    def export_fuzz_trace(self, output_path: str = "data/kickmix_fuzz_trace.json") -> bool:
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(self.last_trace, f, indent=2)
            return True
        except Exception:
            return False

    def get_entropy_seed(self, num_bytes: int = 256) -> Tuple[bytes, Dict[str, Any]]:
        raw_bytes = None
        source_type = "Unknown"

        if not os.path.exists(self.seed_path):
            self._trigger_seed_generation()

        if os.path.exists(self.seed_path):
            try:
                bit_array = np.load(self.seed_path)
                if bit_array.ndim > 1:
                    bit_array = bit_array.flatten()

                req_bits = num_bytes * 8
                if len(bit_array) < req_bits:
                    bit_array = np.pad(bit_array, (0, req_bits - len(bit_array)), mode='wrap')
                
                selected_bits = bit_array[:req_bits]
                raw_bytes = np.packbits(selected_bits).tobytes()
                source_type = "Si28_Phonon_Quantum_QPU"
            except Exception as e:
                raw_bytes = os.urandom(num_bytes)
                source_type = f"OS_Physical_Entropy_Fallback (Error: {str(e)})"
        else:
            raw_bytes = os.urandom(num_bytes)
            source_type = "OS_Physical_Entropy_Fallback"

        val_res = QRNGEntropyValidator.validate_coupon_score(raw_bytes)
        sha256_hash = hashlib.sha256(raw_bytes).hexdigest()

        stats = {
            "source_type": source_type,
            "seed_bytes_len": len(raw_bytes),
            "unique_bytes_count": val_res["unique_bytes_count"],
            "coupon_score": val_res["coupon_score"],
            "is_valid": val_res["is_valid"],
            "sha256_fingerprint": sha256_hash,
            "seed_path_used": self.seed_path if "Si28" in source_type else "N/A",
            "debug_seed_trace": self.debug_seed_trace
        }

        if self.debug_seed_trace:
            self.last_trace = {
                "source_type": source_type,
                "seed_bytes_len": len(raw_bytes),
                "sha256_fingerprint": sha256_hash,
                "coupon_score": val_res["coupon_score"],
                "is_valid": val_res["is_valid"]
            }

        return raw_bytes, stats

    def get_seed(self, num_bytes: int = 256, validate: bool = True, **kwargs) -> bytes:
        """pytest test_fuzz_reproducibility.py 인터페이스 호환용 시드 인출 메서드"""
        raw_bytes, _ = self.get_entropy_seed(num_bytes=num_bytes)
        return raw_bytes
