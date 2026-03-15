# Contributing to SmallTalk 🤝

SmallTalk에 기여해주셔서 감사합니다! 이 문서에서는 PR 작성법, 서브 에이전트(워커), 도구 작성법 및 등록 방법을 안내합니다.

---

## 1. PR (Pull Request) 작성법

### 브랜치 전략

```
main ← feature/워커이름
main ← feature/도구이름
main ← fix/이슈번호-설명
```

### PR 작성 순서

1. **이슈 확인** — 작업하려는 이슈가 있으면 할당, 없으면 새로 생성
2. **브랜치 생성** — `feature/`, `fix/`, `docs/` 접두사 사용
3. **개발 & 테스트** — 아래 가이드에 따라 구현
4. **PR 생성** — 아래 템플릿에 따라 작성

### PR 템플릿

```markdown
## 변경 사항

<!-- 무엇을 추가/변경/수정했는지 간결하게 -->
- 워커 `weather_assistant` 추가
- OpenWeatherMap API를 통한 날씨 조회 도구 구현

## 변경 유형

- [ ] 새 워커 (서브 에이전트)
- [ ] 새 도구 (Tool)
- [ ] 새 인터페이스
- [ ] 버그 수정
- [ ] 문서 업데이트
- [ ] 기타

## 테스트

<!-- 어떻게 테스트했는지 -->
- CLI에서 "오늘 서울 날씨 알려줘" → 정상 응답 확인
- 워커 검색 "날씨" → weather_assistant 검색 확인

## 의존성 변경

<!-- 새로 추가한 의존성이 있다면 -->
- `requests` (OpenWeatherMap API 호출용)
```

### 주의사항

- **커밋 메시지**: 한글 또는 영어 모두 OK. `feat:`, `fix:`, `docs:` 접두사 권장
- **타입 힌트**: 모든 함수에 타입 힌트 추가
- **Docstring**: Google 스타일 docstring 사용
- **`max_tokens` 주의**: 이것은 **출력 최대 길이**이지 컨텍스트 윈도우 크기가 아닙니다

---

## 2. 서브 에이전트 (워커) 작성 방법

워커는 **특정 작업에 특화된 서브 에이전트**입니다. 오케스트레이터가 자동으로 검색하고 호출합니다.

### 워커 파일 구조

`src/smalltalk/workers/` 디렉토리에 워커별 파일을 만듭니다:

```
src/smalltalk/workers/
├── __init__.py
├── weather.py         # 날씨 워커
├── translator.py      # 번역 워커
└── scheduler.py       # 일정 관리 워커
```

### 워커 작성 예시

```python
# src/smalltalk/workers/weather.py

"""날씨 정보 워커"""

from smalltalk.agent.worker import WorkerInfo
from smalltalk.tool_registry import ToolRegistry, tool

# 1) 워커 전용 도구 정의
weather_tools = ToolRegistry()

@tool(weather_tools)
def get_weather(city: str) -> str:
    """특정 도시의 현재 날씨를 조회합니다.

    Args:
        city: 날씨를 조회할 도시명.
    """
    # 실제 API 호출 로직
    import requests
    resp = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"q": city, "appid": "YOUR_API_KEY", "units": "metric", "lang": "kr"}
    )
    data = resp.json()
    return f"{data['name']}: {data['main']['temp']}°C, {data['weather'][0]['description']}"


# 2) WorkerInfo 정의
weather_worker = WorkerInfo(
    name="weather_assistant",
    description="날씨 정보를 조회하고 안내하는 어시스턴트. 특정 도시의 현재 날씨, 기온, 날씨 상태를 알려줍니다.",
    system_prompt=(
        "당신은 날씨 정보 전문가입니다. "
        "사용자가 요청한 도시의 날씨를 조회하고, "
        "친절하고 간결하게 안내해주세요."
    ),
    tool_registry=weather_tools,
)
```

### 작성 시 주의사항

| 항목 | 설명 |
|------|------|
| `name` | 고유한 영문 식별자. 오케스트레이터가 이 이름으로 호출합니다 |
| `description` | **검색에 사용됩니다!** 키워드가 풍부하게 작성해야 검색에 잘 걸립니다 |
| `system_prompt` | 워커의 행동을 정의하는 프롬프트. 코드에 직접 작성합니다 |
| `tool_registry` | 워커 전용 도구. 없으면 빈 `ToolRegistry()` |

---

## 3. 도구 (Tool) 작성 방법

도구는 `@tool` 데코레이터로 일반 Python 함수를 LLM이 호출 가능한 도구로 변환합니다.

### 도구 파일 구조

`src/smalltalk/tools/` 디렉토리에 도구별 파일을 만듭니다:

```
src/smalltalk/tools/
├── __init__.py
├── datetime_tool.py   # 날짜/시간 도구
├── web_search.py      # 웹 검색 도구
└── calculator.py      # 계산기 도구
```

### 도구 작성 예시

```python
# src/smalltalk/tools/calculator.py

"""계산기 도구"""

from smalltalk.tool_registry import ToolRegistry, tool

calculator_tools = ToolRegistry()

@tool(calculator_tools)
def calculate(expression: str) -> str:
    """수학 표현식을 계산합니다.

    Args:
        expression: 계산할 수식 문자열 (예: "2 + 3 * 4").
    """
    try:
        # 안전한 수식 평가
        result = eval(expression, {"__builtins__": {}})
        return f"{expression} = {result}"
    except Exception as e:
        return f"계산 오류: {e}"


@tool(calculator_tools)
def convert_unit(value: float, from_unit: str, to_unit: str) -> str:
    """단위를 변환합니다.

    Args:
        value: 변환할 값.
        from_unit: 원래 단위 (예: "km").
        to_unit: 변환할 단위 (예: "mile").
    """
    # 단위 변환 로직
    ...
```

### 작성 규칙

1. **함수 이름** = 도구 이름 (LLM이 호출할 이름)
2. **docstring 첫 줄** = 도구 설명 (LLM에게 보여지는 설명)
3. **`Args:` 섹션** = 각 파라미터 설명 (LLM이 인자를 채울 때 참고)
4. **타입 힌트 필수** = `str`, `int`, `float`, `bool` → JSON Schema 타입으로 자동 변환
5. **반환값은 `str`** = LLM에게 전달되는 결과

```python
# ✅ 좋은 예
@tool(my_tools)
def search_news(query: str, max_results: int) -> str:
    """최신 뉴스를 검색합니다.

    Args:
        query: 검색할 키워드.
        max_results: 최대 결과 수.
    """

# ❌ 나쁜 예 — docstring 없음, 타입 힌트 없음
@tool(my_tools)
def search(q):
    return do_search(q)
```

---

## 4. 등록 방법

작성한 워커와 도구를 앱에 등록하는 방법입니다.

### 4-1. 도구 등록

`src/smalltalk/app.py`의 `App.__init__`에서 도구 레지스트리를 병합합니다:

```python
# app.py — App.__init__ 내부

from smalltalk.tools.datetime_tool import datetime_tools
from smalltalk.tools.calculator import calculator_tools   # ← 추가

# 기본 도구 레지스트리 구성
self._tools = ToolRegistry()
self._tools.merge(datetime_tools)
self._tools.merge(calculator_tools)  # ← 추가
```

### 4-2. 워커 등록

같은 `App.__init__`에서 워커 레지스트리에 등록합니다:

```python
# app.py — App.__init__ 내부

from smalltalk.workers.weather import weather_worker   # ← 추가

# 워커 레지스트리 초기화
self._worker_registry = WorkerRegistry()
self._worker_registry.register(weather_worker)  # ← 추가
```

### 4-3. 등록 확인

등록이 완료되면 오케스트레이터가 자동으로:

1. **도구** → 오케스트레이터의 tool 목록에 포함 → LLM이 직접 호출 가능
2. **워커** → 키워드 검색 인덱스에 등록 → `search_workers`로 검색 → `dispatch_worker`로 호출

```bash
# 등록 확인 (Python)
uv run python -c "
from smalltalk.app import create_app
app = create_app()
print('도구:', app._orchestrator.tool_registry.names)
print('워커:', app._worker_registry.names)
"
```

---

## 개발 환경

```bash
# 의존성 설치 (개발 포함)
uv sync

# 테스트 실행
uv run pytest tests/ -v

# 패키지 리빌드 (코드 변경 후)
uv sync --reinstall-package smalltalk
```

## 질문이 있으시면

이슈를 생성하거나 오픈톡에서 문의해주세요!
