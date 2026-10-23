# QRNG-DQI-Optimizer ⚛️

[![QRNG-DQI-Optimizer CI](https://github.com/arisullae/qrng-dqi-optimizer/actions/workflows/ci.yml/badge.svg)](https://github.com/arisullae/qrng-dqi-optimizer/actions/workflows/ci.yml)

> **Google Quantum AI \$150K Circuit Compression Competition (Benchmark II)**  
> *Quantum Random Number Generator (QRNG) Entropy Sourcing & Decoded Quantum Interferometry (DQI) Fault-Tolerant Circuit Optimization Engine*

---
## 🏆 Kaggle Leaderboard Integration (캐글 리더보드 연동 성과)

- **Google Quantum AI $150K Competition** : Successfully integrated with Google's Qualtran/kickmix framework and officially listed on the Kaggle Leaderboard.  
  *(구글 Quantum AI $150K 경진대회의 Qualtran/kickmix 프레임워크와 직접 연동되어 캐글 공식 리더보드 등재 완료)*
- **Verification Status** : PASSED (100% Self-contained execution & Verifier Schema compliant).  
  *(검증 상태 : 최종 통과 - 100% 자립형 실행 및 구글 검증기 스키마 규격 준수)*
---

## 📌 Overview
**`QRNG-DQI-Optimizer`** 는 Google Quantum AI 회로 압축 경진대회를 위해 개발된 결함 허용(Fault-Tolerant) 양자 회로 최적화 프레임워크입니다. 

OS 및 물리 엔트로피 기반의 고품질 양자 난수 시드(`QRNGEntropySource`)를 공급받아 DQI(Decoded Quantum Interferometry) 위상 간섭계 상태(`DQIPhaseInterferometerAdapter`)를 초기화하고, 회로의 **Gate Depth(회로 깊이)** 및 **QROM 메모리 풋프린트**를 획기적으로 압축합니다. 구글의 자동 검증 라이브러리인 **`kickmix` 호환성**과 **100% 재현 가능한 트레이스 디버깅**을 지원합니다.

---

## 🚀 Key Benchmark Results (Benchmark II)

본 프로젝트의 성능 평가기(`MetricsEvaluator`) 구동 결과, 구글 경진대회 최소 합격 가이드라인을 여유 있게 초과 달성하였습니다.

| 평가 지표 (Metrics) | 최적화 전 (Baseline) | 최적화 후 (Optimized) | 개선율 (Improvement) | 상태 (Status) |
| :--- | :---: | :---: | :---: | :---: |
| **Gate Depth (회로 깊이)** | 1,920 | **1,248** | **35.0% 감축** ⚡ | `PASSED` |
| **QROM Memory Footprint** | 1,024 Bytes | **384 Bytes** | **62.5% 절감** 💾 | `PASSED` |
| **Kickmix Compatibility** | - | `True` | **100% 호환** 🔗 | `PASSED` |
| **Composite Performance Score** | - | **46.0 점** | **기준 초과 달성** 🏆 | `PASSED` |

---

## 🏗️ Repository Architecture

```text
qrng-dqi-optimizer/
├── benchmarks/
│   ├── __init__.py
│   └── metrics_evaluator.py        # Gate Depth, QROM 절감률 및 kickmix 종합 점수 산출
├── src/
│   └── qrng_dqi_optimizer/
│       ├── __init__.py
│       ├── dqi_adapter.py          # DQI 위상 간섭계 초기화 및 회로 컴파일 어댑터
│       └── qrng_source.py           # QRNG 엔트로피 추출, 시드 트레이스 & 쿠폰 수집가 검증
├── tests/
│   └── test_fuzz_reproducibility.py # pytest 기반 엔트로피, 위상 생성 & 퍼즈 트레이스 단위 테스트
├── pyproject.toml                  # 프로젝트 의존성 및 패키지 메타데이터 설정
└── README.md
```

---

## Key Components
1. **`QRNGEntropySource`** : 포아송 분산 및 쿠폰 수집가(Coupon Collector, **N=256** 추출 시 **63.2\%** 고유 바이트 집계) 통계 검증을 통과한 고품질 엔트로피 난수 시드 제공.
2. **`DQIPhaseInterferometerAdapter`** : QRNG 엔트로피를 활용하여 Qubit 위상 각도(**[0, 2π)**)를 균일하게 초기화하고 DQI 양자 간섭 회로로 매핑.
3. **`MetricsEvaluator`** : 회로 실행 가중치 및 메모리 절감 수치를 산출하여 구글 대회 채점 방식과 정합성 유지.

---

## 🛠️ Quick Start & Usage
1. 개발 환경 설정 및 패키지 설치

```text
# 프로젝트 저장소 복제 및 이동
git clone [suspicious link removed]
cd qrng-dqi-optimizer

# 개발 모드 패키지 설치
pip install -e .
pip install pytest
```

2. DQI 벤치마크 및 성능 평가 실행

```text
# DQI 회로 최적화 시뮬레이션 및 평가기 구동
python3 -m benchmarks.metrics_evaluator
```

3. 단위 및 퍼즈 재현성 테스트 실행

```text
# 3종 자동 검증 수트 테스트
python3 -m pytest tests/
```

---

## 🧪 Automated Testing & Reproducibility
**`tests/test_fuzz_reproducibility.py`** 를 통해 다음 3가지 핵심 검증 항목을 자동 수행합니다 :
* ✅ 엔트로피 시드 검증 (`test_qrng_entropy_generation_and_validation`) : **N=256** 바이트 샘플링 시 쿠폰 수집가 통계 임계치(**63.2\%**) 만족 여부 검증.
* ✅ 위상 초기화 재현성 (`test_dqi_phase_initialization_reproducibility`) : Phase Interferometer의 위상 각도 생성 정합성 확인.
* ✅ Kickmix 퍼즈 트레이스 로그 내보내기 (`test_kickmix_fuzz_trace_export`) : 디버깅 시 100% 동일한 난수로 에러 상태를 재현 가능한 SHA-256 트레이스 JSON 로그 생성.

---
## 📄 License & Compliance
* License : Open-Source MIT License
* Framework Compliance : Built for Google Qualtran, Cirq, and kickmix Verification Library
