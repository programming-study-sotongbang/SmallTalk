"""
인터페이스 추상 클래스.

모든 수신/발송 인터페이스(CLI, Telegram, Discord 등)의 공통 인터페이스를 정의합니다.
allow/block list, chatroom/channel 필터링 로직을 공통으로 제공합니다.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable


class BaseInterface(ABC):
    """수신/발송 인터페이스 추상 클래스"""

    def __init__(
        self,
        allowed_users: list[str | int] | None = None,
        blocked_users: list[str | int] | None = None,
        allowed_chatrooms: list[str | int] | None = None,
        **kwargs,
    ) -> None:
        self._allowed_users: set[str] = (
            {str(u) for u in allowed_users} if allowed_users else set()
        )
        self._blocked_users: set[str] = (
            {str(u) for u in blocked_users} if blocked_users else set()
        )
        self._allowed_chatrooms: set[str] = (
            {str(c) for c in allowed_chatrooms} if allowed_chatrooms else set()
        )

    def is_user_allowed(self, user_id: str | int) -> bool:
        """
        사용자가 허용되었는지 확인합니다.

        - block list에 있으면 거부
        - allow list가 비어있으면 모두 허용
        - allow list가 있으면 목록에 있는 사용자만 허용

        Args:
            user_id: 확인할 사용자 ID.
        """
        uid = str(user_id)

        if uid in self._blocked_users:
            return False

        if not self._allowed_users:
            return True

        return uid in self._allowed_users

    def is_chatroom_allowed(self, chatroom_id: str | int) -> bool:
        """
        채팅방/채널이 허용되었는지 확인합니다.

        - allow list가 비어있으면 모든 채팅방 허용
        - allow list가 있으면 목록에 있는 채팅방만 허용

        Args:
            chatroom_id: 확인할 채팅방/채널 ID.
        """
        if not self._allowed_chatrooms:
            return True

        return str(chatroom_id) in self._allowed_chatrooms

    def should_handle(self, user_id: str | int, chatroom_id: str | int | None = None) -> bool:
        """
        메시지를 처리해야 하는지 종합 판단합니다.

        Args:
            user_id: 발신 사용자 ID.
            chatroom_id: 발신 채팅방 ID (없으면 DM으로 간주).
        """
        if not self.is_user_allowed(user_id):
            return False

        if chatroom_id is not None and not self.is_chatroom_allowed(chatroom_id):
            return False

        return True

    @abstractmethod
    def start(self, message_handler: Callable[[str], str]) -> None:
        """
        인터페이스를 시작합니다.

        Args:
            message_handler: 사용자 메시지를 받아 응답을 반환하는 콜백.
        """
        ...

    @abstractmethod
    def stop(self) -> None:
        """인터페이스를 중지합니다."""
        ...
