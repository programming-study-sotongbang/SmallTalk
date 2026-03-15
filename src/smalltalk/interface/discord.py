"""
디스코드 봇 인터페이스.

discord.py 라이브러리를 사용하여 디스코드 봇으로
사용자와 소통합니다. allow/block list 및 channel 필터링을
BaseInterface에서 상속받아 사용합니다.
"""

from __future__ import annotations

import logging
from typing import Callable

from smalltalk.interface.base import BaseInterface

logger = logging.getLogger(__name__)


class DiscordInterface(BaseInterface):
    """디스코드 봇 인터페이스"""

    def __init__(self, token: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._token = token

    def start(self, message_handler: Callable[[str], str]) -> None:
        """
        디스코드 봇을 시작합니다.

        Args:
            message_handler: 사용자 메시지를 처리하는 콜백.
        """
        try:
            import discord
        except ImportError:
            raise ImportError(
                "디스코드 인터페이스를 사용하려면 discord.py를 설치해주세요:\n"
                "  uv add 'discord.py>=2.0'"
            )

        intents = discord.Intents.default()
        intents.message_content = True

        client = discord.Client(intents=intents)

        @client.event
        async def on_ready():
            logger.info("디스코드 봇 로그인: %s", client.user)
            print(f"[Discord] 봇이 로그인했습니다: {client.user}")

        @client.event
        async def on_message(message: discord.Message):
            # 봇 자신의 메시지 무시
            if message.author == client.user:
                return

            # 빈 메시지 무시
            if not message.content:
                return

            user_id = message.author.id
            channel_id = message.channel.id

            # 공통 필터링
            if not self.should_handle(user_id, channel_id):
                logger.debug(
                    "Filtered message from user=%s channel=%s",
                    user_id,
                    channel_id,
                )
                return

            user_input = message.content
            logger.info(
                "Discord message from user=%s: %s", user_id, user_input[:50]
            )

            try:
                # 타이핑 인디케이터 표시
                async with message.channel.typing():
                    response = message_handler(user_input)
                await message.reply(response)
            except Exception as e:
                logger.error("Error handling message: %s", e)
                await message.reply(
                    f"죄송합니다, 응답 처리 중 오류가 발생했습니다: {e}"
                )

        logger.info("디스코드 봇을 시작합니다...")
        print("[Discord] 봇을 시작합니다. Ctrl+C로 종료합니다.")
        client.run(self._token)

    def stop(self) -> None:
        """디스코드 봇을 중지합니다."""
        pass
