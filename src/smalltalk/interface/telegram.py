"""
텔레그램 봇 인터페이스.

python-telegram-bot 라이브러리를 사용하여 텔레그램 봇으로
사용자와 소통합니다. allow/block list 및 chatroom 필터링을
BaseInterface에서 상속받아 사용합니다.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Callable

from smalltalk.interface.base import BaseInterface

logger = logging.getLogger(__name__)


class TelegramInterface(BaseInterface):
    """텔레그램 봇 인터페이스"""

    def __init__(self, token: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._token = token
        self._application = None

    def start(self, message_handler: Callable[[str], str]) -> None:
        """
        텔레그램 봇을 시작합니다.

        Args:
            message_handler: 사용자 메시지를 처리하는 콜백.
        """
        try:
            from telegram import Update
            from telegram.ext import (
                ApplicationBuilder,
                CommandHandler,
                ContextTypes,
                MessageHandler,
                filters,
            )
        except ImportError:
            raise ImportError(
                "텔레그램 인터페이스를 사용하려면 python-telegram-bot을 설치해주세요:\n"
                "  uv add 'python-telegram-bot>=21.0'"
            )

        async def _handle_start(
            update: Update, context: ContextTypes.DEFAULT_TYPE
        ) -> None:
            """'/start' 명령어 핸들러"""
            if update.effective_user is None or update.message is None:
                return

            user_id = update.effective_user.id
            chat_id = update.effective_chat.id if update.effective_chat else None

            if not self.should_handle(user_id, chat_id):
                return

            await update.message.reply_text(
                "안녕하세요! SmallTalk AI 어시스턴트입니다. 무엇을 도와드릴까요?"
            )

        async def _handle_message(
            update: Update, context: ContextTypes.DEFAULT_TYPE
        ) -> None:
            """일반 텍스트 메시지 핸들러"""
            if update.effective_user is None or update.message is None:
                return
            if not update.message.text:
                return

            user_id = update.effective_user.id
            chat_id = update.effective_chat.id if update.effective_chat else None

            if not self.should_handle(user_id, chat_id):
                logger.debug(
                    "Filtered message from user=%s chat=%s", user_id, chat_id
                )
                return

            user_input = update.message.text
            logger.info("Telegram message from user=%s: %s", user_id, user_input[:50])

            try:
                response = message_handler(user_input)
                await update.message.reply_text(response)
            except Exception as e:
                logger.error("Error handling message: %s", e)
                await update.message.reply_text(
                    f"죄송합니다, 응답 처리 중 오류가 발생했습니다: {e}"
                )

        # 앱 빌드 및 핸들러 등록
        self._application = (
            ApplicationBuilder().token(self._token).build()
        )
        self._application.add_handler(CommandHandler("start", _handle_start))
        self._application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, _handle_message)
        )

        logger.info("텔레그램 봇을 시작합니다...")
        print("[Telegram] 봇이 시작되었습니다. Ctrl+C로 종료합니다.")
        self._application.run_polling()

    def stop(self) -> None:
        """텔레그램 봇을 중지합니다."""
        if self._application:
            logger.info("텔레그램 봇을 중지합니다...")
