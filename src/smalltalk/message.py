"""
멀티모달 메시지 모델.

텍스트와 이미지를 포함하는 타입화된 메시지 시스템입니다.
모든 인터페이스(CLI, Telegram, Discord)는 이 모델을 공통으로 사용합니다.
"""

from __future__ import annotations

import base64
import mimetypes
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class Message:
    """단일 메시지 단위"""

    type: Literal["text", "image"]
    content: str        # 텍스트 본문 또는 이미지 파일 경로
    caption: str = ""   # 이미지에 붙는 캡션 (선택)


def text_message(content: str) -> Message:
    """텍스트 메시지를 생성합니다."""
    return Message(type="text", content=content)


def image_message(path: str, caption: str = "") -> Message:
    """이미지 메시지를 생성합니다."""
    return Message(type="image", content=path, caption=caption)


def image_to_data_url(path: str) -> str:
    """이미지 파일을 data URL (base64)로 변환합니다. VLM 입력용."""
    file_path = Path(path)
    mime_type = mimetypes.guess_type(str(file_path))[0] or "image/png"

    with open(file_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{mime_type};base64,{b64}"


def messages_to_openai_content(messages: list[Message]) -> str | list[dict]:
    """
    Message 리스트를 OpenAI API content 형식으로 변환합니다.

    - 텍스트만 → str
    - 이미지 포함 → content 배열 (VLM 형식)
    """
    has_image = any(m.type == "image" for m in messages)

    if not has_image:
        return "\n".join(m.content for m in messages if m.type == "text")

    parts: list[dict] = []
    for msg in messages:
        if msg.type == "text":
            parts.append({"type": "text", "text": msg.content})
        elif msg.type == "image":
            data_url = image_to_data_url(msg.content)
            if msg.caption:
                parts.append({"type": "text", "text": msg.caption})
            parts.append({
                "type": "image_url",
                "image_url": {"url": data_url},
            })

    return parts
