# coolingjacket

Streamlit 기반 Jacketed Vessel Engineering 계산 앱입니다.

주요 기능
- 내부/외부 대류 열전달 계수 계산
- 총괄 열전달계수(U) 계산
- 가열/냉각 동적 시뮬레이션
- 목표 온도 도달 시간 예측
- HTML/PDF 리포트 다운로드
- URL 기반 상태 공유

이번 정비 내용
- 입력 검증 추가
- 비물리적 heating/cooling target 방향 검증 추가
- 목표 온도 도달 시간 계산 로직을 순수 함수로 분리
- 공유 링크에 reaction/fouling/custom fluid/language 정보 보존
- 테스트 추가
- README/pyproject/CI 추가

실행
```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pytest
streamlit run app.py
```

테스트
```bash
. .venv/bin/activate
PYTHONPATH=. pytest tests -q
```
