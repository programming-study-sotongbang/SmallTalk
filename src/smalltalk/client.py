"""
OpenAI-호환 LLM 클라이언트.

LMStudio, Ollama, OpenRouter 등 OpenAI API 규격을 지원하는
모든 백엔드와 통신합니다. Tool 호출 자동 루프를 지원합니다.
"""

from __future__ import annotations

import json
import logging
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
    from smalltalk.logger import TomlLogger
    from smalltalk.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class LLMClient:
    """OpenAI-호환 API 클라이언트 래퍼"""

    def __init__(self, config: LLMConfig, toml_logger: TomlLogger | None = None) -> None:
        self._config = config
        self._toml_logger = toml_logger
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

        Args:
            messages: 대화 메시지 히스토리.
            tool_registry: 사용 가능한 도구 레지스트리.
            max_iterations: 최대 루프 반복 횟수.

        Returns:
            (최종 텍스트 응답, 전체 메시지 히스토리) 튜플.
        """
        openai_tools = tool_registry.get_openai_tools()
        working_messages = list(messages)

        for iteration in range(max_iterations):
            response = self.chat(working_messages, tools=openai_tools or None)
            choice = response.choices[0]
            assistant_message = choice.message

            working_messages.append(assistant_message)  # type: ignore[arg-type]

            # Tool 호출이 없으면 최종 응답으로 판단
            if not assistant_message.tool_calls:
                raw_content = assistant_message.content or ""
                content = strip_think_block(raw_content)

                # 실제 텍스트 응답이 있으면 그대로 반환 (send_final_response 안 쓴 경우)
                if content:
                    if self._toml_logger:
                        self._toml_logger.log(
                            "llm_response",
                            role="assistant",
                            content=content,
                            extra={"iteration": iteration, "model": self._config.model},
                        )
                    return content, working_messages

                # 빈 응답 (think만 있거나 완전히 비어있음) → 재촉
                logger.warning("빈 응답 감지 (iteration=%d). send_final_response 재촉 중...", iteration)
                working_messages.append({
                    "role": "user",
                    "content": (
                        "응답이 비어있습니다. "
                        "반드시 send_final_response 도구를 호출하여 최종 답변을 전달하세요."
                    ),
                })
                continue  # 루프 계속 → 모델에게 다시 기회

            # Tool 호출 실행 및 결과 주입
            for tool_call in assistant_message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)

                logger.info("Tool 호출: %s(%s)", fn_name, fn_args)

                # TOML 로그 — Tool 호출
                if self._toml_logger:
                    self._toml_logger.log(
                        "tool_call",
                        tool_name=fn_name,
                        tool_args=json.dumps(fn_args, ensure_ascii=False),
                    )

                result = tool_registry.execute(fn_name, fn_args)
                logger.info("Tool 결과: %s", result[:200] if len(result) > 200 else result)

                # TOML 로그 — Tool 결과
                if self._toml_logger:
                    self._toml_logger.log(
                        "tool_result",
                        tool_name=fn_name,
                        tool_result=result,
                    )

                # send_final_response 감지 → 즉시 반환
                from smalltalk.agent.orchestrator import FINAL_RESPONSE_MARKER
                if result.startswith(FINAL_RESPONSE_MARKER):
                    final = result[len(FINAL_RESPONSE_MARKER):]
                    logger.info("최종 응답 (send_final_response): %s...", final[:100])
                    if self._toml_logger:
                        self._toml_logger.log(
                            "final_response",
                            role="assistant",
                            content=final,
                        )
                    return final, working_messages

                working_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result),
                    }
                )

        logger.warning("max_iterations(%d) 도달", max_iterations)
        last_content = working_messages[-1].get("content", "") if isinstance(working_messages[-1], dict) else getattr(working_messages[-1], "content", "") or ""
        return strip_think_block(str(last_content)), working_messages


def strip_think_block(text: str) -> str:
    """<think>...</think> 블록을 제거합니다."""
    return re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL).strip()


def extract_think_content(text: str) -> str:
    """<think>...</think> 블록에서 내용만 추출합니다 (폴백용)."""
    match = re.search(r"<think>(.*?)</think>", text, flags=re.DOTALL)
    if match:
        return f"(생각 중이었던 내용)\n{match.group(1).strip()}"
    return ""
