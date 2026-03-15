"""
인터페이스 추상 클래스.

모든 수신/발송 인터페이스(CLI, Telegram, Discord 등)의 공통 인터페이스를 정의합니다.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    pass


class BaseInterface(ABC):
    """수신/발송 인터페이스 추상 클래스"""

    @abstractmethod
    def start(self, message_handler: Callable[[str], str]) -> None:
        """
        인터페이스를 시작합니다.

        Args:
            message_handler: 사용자 메시지를 받아 응답을 반환하는 콜백.
                             signature: (user_input: str) -> str
        """
        ...

    @abstractmethod
    def stop(self) -> None:
        """인터페이스를 중지합니다."""
        ...
