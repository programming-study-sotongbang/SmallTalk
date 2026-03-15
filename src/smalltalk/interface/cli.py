"""
CLI REPL 인터페이스.

터미널에서 대화형으로 에이전트와 소통하는 기본 인터페이스입니다.
"""

from __future__ import annotations

from typing import Callable

from smalltalk.interface.base import BaseInterface


class CLIInterface(BaseInterface):
    """터미널 기반 대화형 인터페이스"""

    EXIT_COMMANDS = {"exit", "quit", "종료", "q"}

    def __init__(self) -> None:
        self._running = False

    def start(self, message_handler: Callable[[str], str]) -> None:
        """
        CLI REPL을 시작합니다.

        Args:
            message_handler: 사용자 메시지를 처리하는 콜백.
        """
        self._running = True

        print("=" * 60)
        print("  SmallTalk — 일상 생활 AI 어시스턴트")
        print("=" * 60)
        print(f"  종료하려면: {', '.join(sorted(self.EXIT_COMMANDS))}")
        print("=" * 60)
        print()

        while self._running:
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
                response = message_handler(user_input)
                print(f"\n어시스턴트> {response}\n")
            except Exception as e:
                print(f"\n[오류] 응답 처리 중 문제가 발생했습니다: {e}\n")

    def stop(self) -> None:
        """CLI를 중지합니다."""
        self._running = False


def main() -> None:
    """CLI 진입점 (pyproject.toml의 [project.scripts]에서 호출)"""
    from smalltalk.app import create_app

    app = create_app()
    app.run()
