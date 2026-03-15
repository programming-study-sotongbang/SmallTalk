"""
설정 로드 및 검증 모듈.

config.yaml 파일에서 설정을 읽어 Pydantic 모델로 검증합니다.
Orchestrator와 Worker의 LLM 설정을 분리하여 관리합니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM 백엔드 연결 설정"""

    base_url: str = Field(description="OpenAI-호환 API 엔드포인트 URL")
    api_key: str = Field(default="", description="API 키 (로컬 서버는 빈 문자열 가능)")
    model: str = Field(description="사용할 모델명")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, gt=0)


class AgentConfig(BaseModel):
    """에이전트 동작 설정"""

    max_loop_iterations: int = Field(
        default=10,
        gt=0,
        description="오케스트레이터 피드백 루프 최대 반복 횟수",
    )


class InterfaceConfig(BaseModel):
    """개별 인터페이스 설정"""

    type: str = Field(description="인터페이스 타입 (cli, telegram, discord 등)")
    token: str | None = Field(default=None, description="봇 토큰 (telegram, discord 등)")
    allowed_users: list[str | int] | None = Field(default=None, description="허용 사용자 ID 목록")
    blocked_users: list[str | int] | None = Field(default=None, description="차단 사용자 ID 목록")
    allowed_chatrooms: list[str | int] | None = Field(default=None, description="허용 채팅방/채널 ID 목록")

    model_config = {"extra": "allow"}


class AppConfig(BaseModel):
    """애플리케이션 전체 설정"""

    orchestrator: LLMConfig
    worker: LLMConfig
    agent: AgentConfig = Field(default_factory=AgentConfig)
    interfaces: list[InterfaceConfig] = Field(
        default_factory=lambda: [InterfaceConfig(type="cli")]
    )


def load_config(path: str | Path = "config.yaml") -> AppConfig:
    """
    YAML 설정 파일을 로드하고 검증합니다.

    Args:
        path: 설정 파일 경로. 기본값은 프로젝트 루트의 config.yaml.

    Returns:
        검증된 AppConfig 객체.

    Raises:
        FileNotFoundError: 설정 파일이 없을 경우.
        pydantic.ValidationError: 설정 값이 유효하지 않을 경우.
    """
    config_path = Path(path)

    if not config_path.exists():
        raise FileNotFoundError(
            f"설정 파일을 찾을 수 없습니다: {config_path}\n"
            f"config.example.yaml을 config.yaml로 복사한 뒤, 실제 값을 채워주세요."
        )

    with open(config_path, encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    return AppConfig(**raw)
