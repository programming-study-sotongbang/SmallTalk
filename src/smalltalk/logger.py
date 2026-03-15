"""
TOML 파일 기반 로깅 시스템.

대화 로그를 별도 폴더의 TOML 파일에 기록합니다.
각 세션마다 하나의 TOML 파일이 생성되며,
로그 엔트리는 [[logs]] 테이블 배열로 추가됩니다.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TomlLogger:
    """대화 로그를 TOML 파일에 기록하는 로거"""

    def __init__(self, log_dir: str | Path = "logs") -> None:
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)

        # 세션별 로그 파일 (시작 시각 기반)
        session_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._log_file = self._log_dir / f"session_{session_time}.toml"

        # 파일 헤더 작성
        self._log_file.write_text(
            f'# SmallTalk 대화 로그\n'
            f'# 세션 시작: {datetime.now().isoformat()}\n\n',
            encoding="utf-8",
        )

        logger.info("로그 파일: %s", self._log_file)

    def log(
        self,
        event: str,
        *,
        role: str = "",
        content: str = "",
        tool_name: str = "",
        tool_args: str = "",
        tool_result: str = "",
        extra: dict[str, Any] | None = None,
    ) -> None:
        """
        로그 엔트리를 TOML 파일에 추가합니다.

        Args:
            event: 이벤트 타입 (user_input, llm_response, tool_call, tool_result, error)
            role: 메시지 역할 (user, assistant, system, tool)
            content: 메시지 내용
            tool_name: 도구 이름 (tool_call 이벤트)
            tool_args: 도구 인자 (tool_call 이벤트)
            tool_result: 도구 결과 (tool_result 이벤트)
            extra: 추가 메타데이터
        """
        timestamp = datetime.now().isoformat()

        entry_lines = [
            "[[logs]]",
            f'timestamp = "{timestamp}"',
            f'event = "{event}"',
        ]

        if role:
            entry_lines.append(f'role = "{role}"')
        if content:
            entry_lines.append(f'content = """\n{_escape_toml(content)}"""')
        if tool_name:
            entry_lines.append(f'tool_name = "{tool_name}"')
        if tool_args:
            entry_lines.append(f'tool_args = """\n{_escape_toml(tool_args)}"""')
        if tool_result:
            entry_lines.append(f'tool_result = """\n{_escape_toml(tool_result)}"""')
        if extra:
            for k, v in extra.items():
                entry_lines.append(f'{k} = "{_escape_toml(str(v))}"')

        entry_lines.append("")  # 빈 줄로 엔트리 구분

        with open(self._log_file, "a", encoding="utf-8") as f:
            f.write("\n".join(entry_lines) + "\n")

    @property
    def log_file(self) -> Path:
        """현재 로그 파일 경로"""
        return self._log_file


def _escape_toml(text: str) -> str:
    """TOML 멀티라인 문자열에서 특수문자를 이스케이프합니다."""
    return text.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
