"""
오케스트레이터 에이전트.

플래너 역할을 겸하며, 사용자 요청을 받아 작업을 분해하고,
키워드 검색으로 적절한 워커를 탐색한 뒤 Tool 호출로 실행합니다.
피드백 루프를 통해 작업 완료까지 반복합니다.

모든 출력(상태, 최종 응답)은 Tool 호출로 전달됩니다.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Callable

from smalltalk.agent.base import BaseAgent
from smalltalk.message import Message, image_message, messages_to_openai_content, text_message
from smalltalk.tool_registry import ToolRegistry

if TYPE_CHECKING:
    from smalltalk.agent.worker import WorkerRegistry
    from smalltalk.client import LLMClient
    from smalltalk.config import AgentConfig

# 최종 응답임을 표시하는 내부 마커
FINAL_RESPONSE_MARKER = "__SMALLTALK_FINAL__:"

ORCHESTRATOR_SYSTEM_PROMPT = """\
당신은 SmallTalk의 오케스트레이터 에이전트입니다. 사용자의 요청을 분석하고 \
적절한 단계로 분해하여 처리합니다.

## 역할
1. **플래너**: 사용자 요청을 분석하고, 필요한 작업 단계를 계획합니다.
2. **오케스트레이터**: 계획에 따라 워커(서브 에이전트)를 검색하고 호출하여 작업을 수행합니다.

## 필수 작업 흐름
**모든 응답은 반드시 도구를 통해 전달합니다. 절대 도구 없이 직접 텍스트로 응답하지 마세요.**

1. `set_plan`을 호출하여 작업 계획을 사용자에게 공유합니다.
2. 각 단계를 시작할 때 `report_status`로 현재 진행 상황을 알립니다.
3. 필요한 도구를 호출하거나 워커를 검색/실행합니다.
4. 단계가 끝나면 다음 단계로 넘어가며 `report_status`를 다시 호출합니다.
5. **모든 작업이 완료되면 반드시 `send_final_response`를 호출하여 최종 응답을 전달합니다.**

## 사용 가능한 도구
- `set_plan(steps)`: 작업 계획을 단계별로 사용자에게 보여줍니다.
- `report_status(step, status)`: 현재 진행 중인 단계와 상태를 표시합니다.
- `send_final_response(response)`: **최종 응답을 사용자에게 전달합니다. 반드시 마지막에 호출.**
- `search_workers(query)`: 키워드로 관련 워커를 검색합니다.
- `dispatch_worker(worker_name, task)`: 특정 워커에게 작업을 할당합니다.
- 기타 등록된 일반 도구들

## 중요
- 절대 도구 호출 없이 텍스트만으로 응답하지 마세요.
- 반드시 `send_final_response`로 최종 답변을 전달하세요.
"""


class Orchestrator(BaseAgent):
    """플래너 겸 오케스트레이터 에이전트."""

    def __init__(
        self,
        client: LLMClient,
        worker_registry: WorkerRegistry,
        agent_config: AgentConfig,
        extra_tools: ToolRegistry | None = None,
        on_status: Callable[[str], None] | None = None,
    ) -> None:
        orchestrator_tools = ToolRegistry()
        self._worker_registry = worker_registry
        self._agent_config = agent_config
        self._on_status = on_status or (lambda msg: print(f"  {msg}"))

        # ── 상태/응답 도구 ──

        @orchestrator_tools.register
        def set_plan(steps: str) -> str:
            """작업 계획을 단계별로 사용자에게 보여줍니다. 작업 시작 시 반드시 호출하세요.

            Args:
                steps: 단계별 계획 (줄바꿈으로 구분). 예: "1. 현재 날짜 확인\\n2. 10일 후 계산"
            """
            self._on_status("📋 계획:")
            for line in steps.strip().split("\n"):
                line = line.strip()
                if line:
                    self._on_status(f"   {line}")
            return "계획이 사용자에게 표시되었습니다. 계속 진행하세요."

        @orchestrator_tools.register
        def report_status(step: str, status: str) -> str:
            """현재 진행 중인 단계와 상태를 사용자에게 실시간으로 표시합니다.

            Args:
                step: 현재 단계 번호 또는 이름.
                status: 현재 상태 설명.
            """
            self._on_status(f"▶ [{step}] {status}")
            return "상태가 사용자에게 표시되었습니다. 계속 진행하세요."

        @orchestrator_tools.register
        def send_final_response(response: str, images: str = "") -> str:
            """최종 응답을 사용자에게 전달합니다. 모든 작업이 완료된 후 반드시 호출하세요.

            Args:
                response: 사용자에게 전달할 최종 응답 텍스트.
                images: 첨부 이미지 맵 (JSON). 키=파일경로, 값=캡션. 예: {"chart.png": "매출 차트"}
            """
            import json as _json

            payload = {"response": response}
            if images:
                try:
                    payload["images"] = _json.loads(images)
                except _json.JSONDecodeError:
                    payload["images"] = {}

            return f"{FINAL_RESPONSE_MARKER}{_json.dumps(payload, ensure_ascii=False)}"

        # ── 워커 관련 도구 ──

        @orchestrator_tools.register
        def search_workers(query: str) -> str:
            """키워드로 관련 워커(서브 에이전트)를 검색합니다.

            Args:
                query: 검색할 키워드 또는 작업 설명.
            """
            results = self._worker_registry.search(query)
            if not results:
                return "관련 워커를 찾을 수 없습니다."
            return json.dumps(results, ensure_ascii=False)

        @orchestrator_tools.register
        def dispatch_worker(worker_name: str, task: str) -> str:
            """워커(서브 에이전트)에게 작업을 할당하고 결과를 받습니다.

            Args:
                worker_name: 호출할 워커의 이름.
                task: 워커에게 전달할 구체적인 작업 지시.
            """
            worker = self._worker_registry.create_worker(
                worker_name,
                self._worker_client,
            )
            if worker is None:
                return f"워커 '{worker_name}'을(를) 찾을 수 없습니다."

            self._on_status(f"🤖 워커 '{worker_name}' 실행 중...")
            return worker.run(task)

        # 외부 도구 병합
        if extra_tools:
            orchestrator_tools.merge(extra_tools)

        super().__init__(
            client=client,
            system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
            tool_registry=orchestrator_tools,
        )

        self._worker_client: LLMClient | None = None

    def set_worker_client(self, client: LLMClient) -> None:
        """워커용 LLM 클라이언트를 설정합니다."""
        self._worker_client = client

    def run(self, user_input: list[Message] | str) -> list[Message]:
        """
        사용자 요청을 처리합니다.

        Args:
            user_input: 사용자 입력. str 또는 list[Message].

        Returns:
            응답 Message 리스트.
        """
        # 입력을 OpenAI 메시지 형식으로 변환
        if isinstance(user_input, str):
            content: str | list[dict] = user_input
        else:
            content = messages_to_openai_content(user_input)

        messages = [
            self._build_system_message(),
            {"role": "user", "content": content},
        ]

        response, _ = self.client.chat_with_tools(
            messages,
            self.tool_registry,
            max_iterations=self._agent_config.max_loop_iterations,
        )

        return self._parse_response(response)

    def _parse_response(self, response: str) -> list[Message]:
        """응답 문자열을 Message 리스트로 변환합니다."""
        # send_final_response 마커 감지
        if response.startswith(FINAL_RESPONSE_MARKER):
            raw = response[len(FINAL_RESPONSE_MARKER):]
            try:
                payload = json.loads(raw)
                result: list[Message] = []

                text = payload.get("response", "")
                if text:
                    result.append(text_message(text))

                images = payload.get("images", {})
                if isinstance(images, dict):
                    for path, caption in images.items():
                        result.append(image_message(path, caption or ""))

                return result if result else [text_message(raw)]

            except json.JSONDecodeError:
                return [text_message(raw)]

        return [text_message(response)]
