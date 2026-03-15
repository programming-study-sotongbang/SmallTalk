"""
오케스트레이터 에이전트.

플래너 역할을 겸하며, 사용자 요청을 받아 작업을 분해하고,
키워드 검색으로 적절한 워커를 탐색한 뒤 Tool 호출로 실행합니다.
피드백 루프를 통해 작업 완료까지 반복합니다.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from smalltalk.agent.base import BaseAgent
from smalltalk.tool_registry import ToolRegistry

if TYPE_CHECKING:
    from smalltalk.agent.worker import WorkerRegistry
    from smalltalk.client import LLMClient
    from smalltalk.config import AgentConfig

ORCHESTRATOR_SYSTEM_PROMPT = """\
당신은 SmallTalk의 오케스트레이터 에이전트입니다. 사용자의 요청을 분석하고 \
적절한 단계로 분해하여 처리합니다.

## 역할
1. **플래너**: 사용자 요청을 분석하고, 필요한 작업 단계를 계획합니다.
2. **오케스트레이터**: 계획에 따라 워커(서브 에이전트)를 검색하고 호출하여 작업을 수행합니다.

## 사용 가능한 도구
- `search_workers(query)`: 키워드로 관련 워커를 검색합니다.
- `dispatch_worker(worker_name, task)`: 특정 워커에게 작업을 할당합니다.
- 기타 등록된 일반 도구들

## 작업 흐름
1. 사용자 요청을 분석합니다.
2. 직접 처리할 수 있으면 바로 응답합니다.
3. 워커가 필요하면 `search_workers`로 적절한 워커를 검색합니다.
4. 검색된 워커를 `dispatch_worker`로 호출합니다.
5. 워커의 결과를 바탕으로 다음 단계를 결정합니다.
6. 모든 작업이 완료되면 사용자에게 종합적인 응답을 제공합니다.

## 주의사항
- 워커가 없거나 검색 결과가 없으면 직접 응답합니다.
- 한 번에 하나의 워커만 호출합니다.
- 각 단계의 결과를 확인한 후 다음 단계로 진행합니다.
"""


class Orchestrator(BaseAgent):
    """
    플래너 겸 오케스트레이터 에이전트.

    사용자 요청을 받아 작업을 분해하고, 워커를 검색/호출하여
    피드백 루프를 통해 작업을 완료합니다.
    """

    def __init__(
        self,
        client: LLMClient,
        worker_registry: WorkerRegistry,
        agent_config: AgentConfig,
        extra_tools: ToolRegistry | None = None,
    ) -> None:
        # 오케스트레이터 전용 Tool 레지스트리 구성
        orchestrator_tools = ToolRegistry()
        self._worker_registry = worker_registry
        self._agent_config = agent_config

        # 워커 검색 Tool 등록
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

        # 워커 호출 Tool 등록
        @orchestrator_tools.register
        def dispatch_worker(worker_name: str, task: str) -> str:
            """워커(서브 에이전트)에게 작업을 할당하고 결과를 받습니다.

            Args:
                worker_name: 호출할 워커의 이름.
                task: 워커에게 전달할 구체적인 작업 지시.
            """
            from smalltalk.client import LLMClient as _LLMClient
            from smalltalk.config import load_config

            worker = self._worker_registry.create_worker(
                worker_name,
                self._worker_client,
            )
            if worker is None:
                return f"워커 '{worker_name}'을(를) 찾을 수 없습니다."

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

    def run(self, user_input: str) -> str:
        """
        사용자 요청을 처리합니다.

        Args:
            user_input: 사용자의 요청 문자열.

        Returns:
            최종 응답 문자열.
        """
        messages = [
            self._build_system_message(),
            {"role": "user", "content": user_input},
        ]

        response, _ = self.client.chat_with_tools(
            messages,
            self.tool_registry,
            max_iterations=self._agent_config.max_loop_iterations,
        )

        return response
