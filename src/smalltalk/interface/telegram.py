"""
텔레그램 봇 인터페이스. (스텁)

추후 커뮤니티 기여로 구현될 예정입니다.
python-telegram-bot 라이브러리를 사용할 것을 권장합니다.
"""

from __future__ import annotations

from typing import Callable

from smalltalk.interface.base import BaseInterface


class TelegramInterface(BaseInterface):
    """텔레그램 봇 인터페이스 (미구현)"""

    def __init__(self, token: str, **kwargs) -> None:
        self._token = token

    def start(self, message_handler: Callable[[str], str]) -> None:
        raise NotImplementedError(
            "텔레그램 인터페이스는 아직 구현되지 않았습니다. "
            "기여를 환영합니다! "
            "https://github.com/programming-study-sotongbang/SmallTalk"
        )

    def stop(self) -> None:
        pass
