"""
CLI REPL 인터페이스.

터미널에서 대화형으로 에이전트와 소통하는 기본 인터페이스입니다.
이미지 메시지는 파일 경로로 표시됩니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from smalltalk.interface.base import BaseInterface
from smalltalk.message import Message


class CLIInterface(BaseInterface):
    """터미널 기반 대화형 인터페이스"""

    EXIT_COMMANDS = {"exit", "quit", "종료", "q"}

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def start(self, message_handler: Callable[[str], list[Message]]) -> None:
        """
        CLI REPL을 시작합니다.

        Args:
            message_handler: 사용자 메시지를 처리하는 콜백.
        """
        print("=" * 60)
        print("  SmallTalk — 일상 생활 AI 어시스턴트")
        print("=" * 60)
        print(f"  종료하려면: {', '.join(sorted(self.EXIT_COMMANDS))}")
        print("=" * 60)
        print()

        while True:
            try:
                user_input = input("사용자> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n프로그램을 종료합니다.")
                break

            if not user_input:
                continue

            if user_input.lower() in self.EXIT_COMMANDS:
                print("프로그램을 종료합니다. 안녕히 가세요!")
                break

            try:
                messages = message_handler(user_input)
                self._print_messages(messages)
            except Exception as e:
                print(f"\n[오류] 응답 처리 중 문제가 발생했습니다: {e}\n")

    def _print_messages(self, messages: list[Message]) -> None:
        """Message 리스트를 터미널에 출력합니다."""
        print()
        for msg in messages:
            if msg.type == "text":
                print(f"어시스턴트> {msg.content}")
            elif msg.type == "image":
                path = Path(msg.content)
                caption = f" ({msg.caption})" if msg.caption else ""
                if path.exists():
                    print(f"  📎 [이미지{caption}] {path}")
                else:
                    print(f"  📎 [이미지{caption}] {msg.content} (파일 없음)")
        print()

    def stop(self) -> None:
        """CLI를 중지합니다."""
        pass


def main() -> None:
    """CLI 진입점 (pyproject.toml의 [project.scripts]에서 호출)"""
    from smalltalk.app import create_app

    app = create_app()
    app.run()
