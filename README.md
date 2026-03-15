# SmallTalk 🗣️

> 일상 생활 영역의 AI 에이전트를 소형 모델로 안전하게 재구현하는 커뮤니티 프로젝트

## 개요

SmallTalk은 코딩이 아닌 **일상 생활 영역**에서 사용되는 AI 에이전트를 안전한 방향으로 재구현하는 프로젝트입니다. Qwen3.5 4B~30B 급의 소형 모델을 사용하고, LMStudio, Ollama, OpenRouter 등 OpenAI-호환 API를 지원하는 모든 백엔드에서 동작합니다.

## 아키텍처

```
사용자 ←→ Interface (CLI / Telegram / Discord)
              ↕
         Orchestrator (플래너 겸 오케스트레이터)
         ┌────┼────┬────────────┐
     set_plan  │  report_status  send_final_response
               ↕
        ┌──────┴──────┐
  search_workers  dispatch_worker
        ↕                ↕
  KeywordSearch    Worker (서브 에이전트)
```

### 핵심 흐름

1. **인터페이스**가 사용자 메시지를 수신
2. **오케스트레이터**가 `set_plan`으로 작업 계획을 수립 → 사용자에게 표시
3. 각 단계마다 `report_status`로 진행 상황 실시간 표시
4. 필요 시 `search_workers` → `dispatch_worker`로 워커 검색/호출
5. `send_final_response`로 최종 응답 전달
6. **같은 인터페이스**를 통해 응답 발송

### 주요 구성 요소

| 구성 요소 | 역할 |
|-----------|------|
| **Orchestrator** | 플래너 겸 오케스트레이터. 요청 분석, 작업 분해, Worker 검색/호출 |
| **Worker** | 특정 작업 특화 서브 에이전트. 독립 컨텍스트에서 동작 |
| **ToolRegistry** | `@tool` 데코레이터로 도구 등록. OpenAI function schema 자동 생성 |
| **Interface** | 수신/발송 채널 (CLI, Telegram, Discord). 공통 필터링 내장 |
| **KeywordSearch** | TF-IDF 기반 워커 검색 엔진 |
| **TomlLogger** | 대화 로그를 세션별 TOML 파일로 기록 |

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

### 선택적 의존성

```bash
# 텔레그램 봇 사용 시
uv add 'python-telegram-bot>=21.0'

# 디스코드 봇 사용 시
uv add 'discord.py>=2.0'
```

## 사용법

```bash
# CLI 모드로 실행
uv run python main.py
```

## 설정

`config.yaml`에서 Orchestrator와 Worker의 LLM 설정을 분리하여 관리합니다.
`config.example.yaml`을 참고하세요.

```yaml
orchestrator:          # 오케스트레이터 LLM 설정
  base_url: "https://openrouter.ai/api/v1"
  api_key: "sk-or-..."
  model: "qwen/qwen3.5-30b-a3b"
  temperature: 0.7
  max_tokens: 4096     # 출력 최대 토큰 수 (컨텍스트 윈도우가 아님!)

worker:                # 워커 LLM 설정
  base_url: "https://openrouter.ai/api/v1"
  api_key: "sk-or-..."
  model: "qwen/qwen3.5-4b"
  temperature: 0.5
  max_tokens: 2048

agent:
  max_loop_iterations: 10

interfaces:            # 활성화할 인터페이스 목록
  - type: cli
  # - type: telegram
  #   token: "your-bot-token"
  #   allowed_users: [12345678]        # 허용 사용자 ID
  #   blocked_users: []                # 차단 사용자 ID
  #   allowed_chatrooms: [-100123456]  # 허용 채팅방 ID
```

## 프로젝트 구조

```
src/smalltalk/
├── config.py           # 설정 로드/검증 (Pydantic)
├── client.py           # OpenAI-호환 LLM 클라이언트 + Tool 호출 루프
├── app.py              # 앱 부트스트랩
├── logger.py           # TOML 파일 기반 대화 로거
├── tool_registry.py    # @tool 데코레이터 및 Tool 관리
├── agent/
│   ├── base.py         # 에이전트 기본 클래스
│   ├── orchestrator.py # 오케스트레이터 (set_plan, report_status, send_final_response)
│   └── worker.py       # 워커 + WorkerRegistry
├── search/
│   └── keyword_search.py  # TF-IDF 키워드 검색
├── tools/
│   └── datetime_tool.py   # 예시 도구 (get_current_datetime)
└── interface/
    ├── base.py         # 인터페이스 추상 클래스 + 공통 필터링
    ├── cli.py          # CLI REPL
    ├── telegram.py     # 텔레그램 봇
    └── discord.py      # 디스코드 봇
```

## 기여하기

[CONTRIBUTING.md](CONTRIBUTING.md)를 참고해주세요.

## 라이선스

MIT License
