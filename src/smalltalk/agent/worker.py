"""
워커(서브 에이전트) 및 워커 레지스트리.

Worker는 특정 작업에 특화된 에이전트로, 독립된 컨텍스트에서 동작합니다.
WorkerRegistry는 워커를 등록하고 키워드 검색을 통해 탐색할 수 있게 합니다.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from smalltalk.agent.base import BaseAgent
from smalltalk.search.keyword_search import KeywordSearchEngine, SearchableItem
from smalltalk.tool_registry import ToolRegistry

if TYPE_CHECKING:
    from smalltalk.client import LLMClient
    from smalltalk.config import LLMConfig


@dataclass
class WorkerInfo:
    """워커 메타데이터"""

    name: str
    description: str
    system_prompt: str
    tool_registry: ToolRegistry = field(default_factory=ToolRegistry)


class Worker(BaseAgent):
    """특정 작업에 특화된 서브 에이전트"""

    def __init__(
        self,
        client: LLMClient,
        info: WorkerInfo,
    ) -> None:
        super().__init__(
            client=client,
            system_prompt=info.system_prompt,
            tool_registry=info.tool_registry,
        )
        self.info = info

    def run(self, user_input: str) -> str:
        """
        독립된 컨텍스트에서 작업을 수행합니다.

        매 호출마다 새로운 메시지 히스토리를 생성하여
        메인 에이전트와 분리된 컨텍스트를 유지합니다.

        Args:
            user_input: 오케스트레이터로부터 할당받은 작업 설명.

        Returns:
            작업 결과 문자열.
        """
        messages = [
            self._build_system_message(),
            {"role": "user", "content": user_input},
        ]

        if self.tool_registry and self.tool_registry.names:
            response, _ = self.client.chat_with_tools(messages, self.tool_registry)
        else:
            completion = self.client.chat(messages)
            from smalltalk.client import strip_think_block
            response = strip_think_block(completion.choices[0].message.content or "")

        return response


class WorkerRegistry:
    """
    워커 등록 및 검색 레지스트리.

    워커를 등록하면 자동으로 키워드 검색 인덱스가 구축되어,
    오케스트레이터가 필요한 워커를 탐색할 수 있습니다.
    """

    def __init__(self) -> None:
        self._workers: dict[str, WorkerInfo] = {}
        self._search_engine = KeywordSearchEngine()

    def register(self, info: WorkerInfo) -> None:
        """
        워커를 레지스트리에 등록합니다.

        Args:
            info: 등록할 워커의 메타데이터.
        """
        self._workers[info.name] = info
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        """검색 인덱스를 재구축합니다."""
        items = [
            SearchableItem(name=w.name, description=w.description)
            for w in self._workers.values()
        ]
        self._search_engine.index(items)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        쿼리로 관련 워커를 검색합니다.

        Args:
            query: 검색 키워드.
            top_k: 최대 결과 수.

        Returns:
            워커 정보 딕셔너리 목록 (이름, 설명, 유사도 점수).
        """
        results = self._search_engine.search(query, top_k=top_k)
        return [
            {
                "name": r.item.name,
                "description": r.item.description,
                "score": round(r.score, 4),
            }
            for r in results
        ]

    def get(self, name: str) -> WorkerInfo | None:
        """이름으로 워커 정보를 가져옵니다."""
        return self._workers.get(name)

    def create_worker(self, name: str, client: LLMClient) -> Worker | None:
        """워커 인스턴스를 생성합니다."""
        info = self.get(name)
        if info is None:
            return None
        return Worker(client=client, info=info)

    @property
    def names(self) -> list[str]:
        """등록된 워커 이름 목록"""
        return list(self._workers.keys())

    def list_all(self) -> list[dict[str, str]]:
        """등록된 모든 워커의 이름과 설명을 반환합니다."""
        return [
            {"name": w.name, "description": w.description}
            for w in self._workers.values()
        ]
