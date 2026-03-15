# SmallTalk 🗣️

> 일상 생활 영역의 AI 에이전트를 소형 모델로 안전하게 재구현하는 커뮤니티 프로젝트

## 개요

SmallTalk은 코딩이 아닌 **일상 생활 영역**에서 사용되는 AI 에이전트를 안전한 방향으로 재구현하는 프로젝트입니다. Qwen3.5 4B~30B 급의 소형 모델을 사용하며, LMStudio, Ollama, OpenRouter 등 OpenAI-호환 API를 지원하는 모든 백엔드에서 동작합니다.

## 아키텍처

```
사용자 ←→ Interface (CLI/Telegram/Discord)
              ↕
         Orchestrator (플래너 겸 오케스트레이터)
           ↕         ↕
    search_workers  dispatch_worker
           ↕         ↕
     KeywordSearch  Worker (서브 에이전트)
```

- **Orchestrator**: 사용자 요청을 분석, 작업을 분해하고 적절한 Worker를 검색/호출
- **Worker**: 특정 작업에 특화된 서브 에이전트, 독립된 컨텍스트에서 동작
- **Interface**: 수신/발송 채널 (CLI, Telegram, Discord 등)

## 설치

```bash
# uv 설치 (없다면)
pip install uv

# 프로젝트 의존성 설치
uv sync

# 설정 파일 생성
cp config.example.yaml config.yaml
# config.yaml을 열어 API 키와 모델 설정을 채워주세요
```

## 사용법

```bash
# CLI 모드로 실행
uv run python main.py

# 또는
uv run smalltalk
```

## 설정

`config.yaml`에서 Orchestrator와 Worker의 LLM 설정을 분리하여 관리합니다:

```yaml
orchestrator:
  base_url: "https://openrouter.ai/api/v1"
  api_key: "sk-or-..."
  model: "qwen/qwen3.5-30b-a3b"
  temperature: 0.7
  max_tokens: 4096

worker:
  base_url: "http://localhost:1234/v1"
  model: "qwen3.5-4b"
  temperature: 0.5
  max_tokens: 2048

agent:
  max_loop_iterations: 10

interfaces:
  - type: cli
  # - type: telegram
  #   token: "your-bot-token"
```

## 프로젝트 구조

```
src/smalltalk/
├── config.py          # 설정 로드/검증
├── client.py          # OpenAI-호환 LLM 클라이언트
├── app.py             # 앱 부트스트랩
├── tool_registry.py   # @tool 데코레이터 및 Tool 관리
├── agent/
│   ├── base.py        # 에이전트 기본 클래스
│   ├── orchestrator.py # 오케스트레이터
│   └── worker.py      # 워커 + WorkerRegistry
├── search/
│   └── keyword_search.py  # TF-IDF 키워드 검색
├── tools/
│   └── datetime_tool.py   # 예시 도구
└── interface/
    ├── base.py        # 인터페이스 추상 클래스
    ├── cli.py         # CLI REPL
    ├── telegram.py    # 텔레그램 (스텁)
    └── discord.py     # 디스코드 (스텁)
```

## 기여 가이드

### 워커(서브 에이전트) 추가

`WorkerInfo`를 정의하고 `WorkerRegistry`에 등록하면 됩니다:

```python
from smalltalk.agent.worker import WorkerInfo
from smalltalk.tool_registry import ToolRegistry

weather_worker = WorkerInfo(
    name="weather_assistant",
    description="날씨 정보를 조회하고 안내하는 어시스턴트",
    system_prompt="당신은 날씨 정보 전문가입니다...",
    tool_registry=ToolRegistry(),  # 워커 전용 도구
)
```

### 인터페이스 추가

`BaseInterface`를 구현하고 `config.yaml`에 등록하면 됩니다.

### 도구 추가

`@tool` 데코레이터를 사용합니다:

```python
from smalltalk.tool_registry import ToolRegistry, tool

my_tools = ToolRegistry()

@tool(my_tools)
def search_web(query: str) -> str:
    """웹에서 정보를 검색합니다.

    Args:
        query: 검색할 키워드.
    """
    ...
```

## 라이선스

MIT License
