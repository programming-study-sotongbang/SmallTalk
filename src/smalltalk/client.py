"""
OpenAI-호환 LLM 클라이언트.

LMStudio, Ollama, OpenRouter 등 OpenAI API 규격을 지원하는
모든 백엔드와 통신합니다. Tool 호출 자동 루프를 지원합니다.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

from openai import OpenAI

if TYPE_CHECKING:
    from openai.types.chat import (
        ChatCompletion,
        ChatCompletionMessageParam,
        ChatCompletionToolParam,
    )

    from smalltalk.config import LLMConfig
    from smalltalk.tool_registry import ToolRegistry


class LLMClient:
    """OpenAI-호환 API 클라이언트 래퍼"""

    def __init__(self, config: LLMConfig) -> None:
        self._config = config
        self._client = OpenAI(
            base_url=config.base_url,
            api_key=config.api_key or "not-needed",
        )

    def chat(
        self,
        messages: list[ChatCompletionMessageParam],
        tools: list[ChatCompletionToolParam] | None = None,
    ) -> ChatCompletion:
        """단일 LLM 호출을 수행합니다."""
        kwargs: dict = {
            "model": self._config.model,
            "messages": messages,
            "temperature": self._config.temperature,
            "max_tokens": self._config.max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        return self._client.chat.completions.create(**kwargs)

    def chat_with_tools(
        self,
        messages: list[ChatCompletionMessageParam],
        tool_registry: ToolRegistry,
        max_iterations: int = 10,
    ) -> tuple[str, list[ChatCompletionMessageParam]]:
        """
        Tool 호출 자동 루프를 수행합니다.

        LLM이 tool_calls를 반환하면 해당 도구를 실행하고,
        결과를 메시지에 추가한 뒤 재호출합니다.
        텍스트 응답이 나오거나 max_iterations에 도달하면 종료합니다.

        Args:
            messages: 대화 메시지 히스토리.
            tool_registry: 사용 가능한 도구 레지스트리.
            max_iterations: 최대 루프 반복 횟수.

        Returns:
            (최종 텍스트 응답, 전체 메시지 히스토리) 튜플.
        """
        openai_tools = tool_registry.get_openai_tools()
        working_messages = list(messages)

        for _ in range(max_iterations):
            response = self.chat(working_messages, tools=openai_tools or None)
            choice = response.choices[0]
            assistant_message = choice.message

            # 메시지 히스토리에 어시스턴트 응답 추가
            working_messages.append(assistant_message)  # type: ignore[arg-type]

            # Tool 호출이 없으면 최종 응답으로 판단
            if not assistant_message.tool_calls:
                content = assistant_message.content or ""
                return strip_think_block(content), working_messages

            # Tool 호출 실행 및 결과 주입
            for tool_call in assistant_message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)

                result = tool_registry.execute(fn_name, fn_args)

                working_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result),
                    }
                )

        # max_iterations 도달 시 마지막 응답 반환
        last_content = working_messages[-1].get("content", "") if isinstance(working_messages[-1], dict) else getattr(working_messages[-1], "content", "") or ""
        return strip_think_block(str(last_content)), working_messages


def strip_think_block(text: str) -> str:
    """<think>...</think> 블록을 제거합니다."""
    return re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL).strip()
