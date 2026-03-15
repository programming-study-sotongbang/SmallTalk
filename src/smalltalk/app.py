"""
애플리케이션 부트스트랩.

설정을 로드하고, 앱 구성 요소들을 초기화하며,
인터페이스를 시작합니다.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from smalltalk.agent.orchestrator import Orchestrator
from smalltalk.agent.worker import WorkerRegistry
from smalltalk.client import LLMClient
from smalltalk.config import AppConfig, load_config
from smalltalk.interface.base import BaseInterface
from smalltalk.interface.cli import CLIInterface
from smalltalk.logger import TomlLogger
from smalltalk.tools import discover_all_tools
from smalltalk.workers import get_worker_catalog

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# 인터페이스 타입 → 클래스 매핑
INTERFACE_REGISTRY: dict[str, type[BaseInterface]] = {
    "cli": CLIInterface,
}

# 지연 임포트가 필요한 인터페이스
LAZY_INTERFACES: dict[str, str] = {
    "telegram": "smalltalk.interface.telegram.TelegramInterface",
    "discord": "smalltalk.interface.discord.DiscordInterface",
}


def _resolve_interface(iface_config) -> BaseInterface:
    """설정에서 인터페이스 인스턴스를 생성합니다."""
    iface_type = iface_config.type
    kwargs = iface_config.model_dump(exclude={"type"})
    kwargs = {k: v for k, v in kwargs.items() if v is not None}

    if iface_type in INTERFACE_REGISTRY:
        cls = INTERFACE_REGISTRY[iface_type]
        return cls(**kwargs)

    if iface_type in LAZY_INTERFACES:
        import importlib

        module_path, _, class_name = LAZY_INTERFACES[iface_type].rpartition(".")
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        return cls(**kwargs)

    raise ValueError(f"알 수 없는 인터페이스 타입: {iface_type}")


def _load_agent_config(filename: str = "config.agent.yaml") -> list[str]:
    """config.agent.yaml에서 활성화할 워커 목록을 로드합니다."""
    from smalltalk.config import resolve_config_path

    config_path = resolve_config_path(filename)
    if config_path is None:
        logger.info("config.agent.yaml이 없습니다. 워커 없이 시작합니다.")
        return []

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    workers = data.get("workers", []) or []
    logger.info("워커 설정 로드: %s (from %s)", workers, config_path)
    return workers


class App:
    """SmallTalk 애플리케이션"""

    def __init__(self, config: AppConfig) -> None:
        self._config = config

        # TOML 로거 초기화
        self._toml_logger = TomlLogger()

        # LLM 클라이언트 초기화 (TOML 로거 주입)
        self._orchestrator_client = LLMClient(config.orchestrator, toml_logger=self._toml_logger)
        self._worker_client = LLMClient(config.worker, toml_logger=self._toml_logger)

        # ── 도구 자동 검색 (모두 로드) ──
        self._tools = discover_all_tools()
        logger.info("등록된 도구: %s", self._tools.names)

        # ── 워커 등록 (config.agent.yaml 기반) ──
        self._worker_registry = WorkerRegistry()
        active_workers = _load_agent_config()
        catalog = get_worker_catalog()

        for worker_name in active_workers:
            if worker_name in catalog:
                self._worker_registry.register(catalog[worker_name])
                logger.info("워커 활성화: %s", worker_name)
            else:
                logger.warning(
                    "워커 '%s'를 찾을 수 없습니다. "
                    "src/smalltalk/workers/ 에 해당 모듈이 있는지 확인하세요.",
                    worker_name,
                )

        # 오케스트레이터 초기화
        self._orchestrator = Orchestrator(
            client=self._orchestrator_client,
            worker_registry=self._worker_registry,
            agent_config=config.agent,
            extra_tools=self._tools,
        )
        self._orchestrator.set_worker_client(self._worker_client)

        # 인터페이스 목록
        self._interfaces: list[BaseInterface] = [
            _resolve_interface(iface) for iface in config.interfaces
        ]

    def _handle_message(self, user_input: str) -> list:
        """사용자 메시지를 오케스트레이터에 전달합니다."""
        self._toml_logger.log("user_input", role="user", content=user_input)
        messages = self._orchestrator.run(user_input)

        # TOML 로그: 텍스트 응답만 기록
        text_parts = [m.content for m in messages if m.type == "text"]
        if text_parts:
            self._toml_logger.log("assistant_response", role="assistant", content="\n".join(text_parts))

        return messages

    def run(self) -> None:
        """첫 번째 인터페이스를 시작합니다."""
        if not self._interfaces:
            print("[오류] 활성화된 인터페이스가 없습니다. config.yaml을 확인해주세요.")
            return

        # 첫 번째 인터페이스로 시작 (CLI가 기본)
        self._interfaces[0].start(self._handle_message)


def create_app(config_path: str = "config.yaml") -> App:
    """설정을 로드하고 앱 인스턴스를 생성합니다."""
    config = load_config(config_path)
    return App(config)
