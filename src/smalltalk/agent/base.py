"""
에이전트 기본 클래스.

모든 에이전트(Orchestrator, Worker)의 공통 인터페이스를 정의합니다.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openai.types.chat import ChatCompletionMessageParam

    from smalltalk.client import LLMClient
    from smalltalk.tool_registry import ToolRegistry


class BaseAgent(ABC):
    """에이전트 추상 기본 클래스"""

    def __init__(
        self,
        client: LLMClient,
        system_prompt: str,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self.client = client
        self.system_prompt = system_prompt
        self.tool_registry = tool_registry

    def _build_system_message(self) -> ChatCompletionMessageParam:
        """시스템 메시지를 생성합니다."""
        return {"role": "system", "content": self.system_prompt}

    @abstractmethod
    def run(self, user_input: str) -> str:
        """
        사용자 입력을 처리하고 응답을 반환합니다.

        Args:
            user_input: 사용자의 요청 문자열.

        Returns:
            에이전트의 응답 문자열.
        """
        ...
