"""
애플리케이션 부트스트랩.

설정을 로드하고, 앱 구성 요소들을 초기화하며,
인터페이스를 시작합니다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from smalltalk.agent.orchestrator import Orchestrator
from smalltalk.agent.worker import WorkerRegistry
from smalltalk.client import LLMClient
from smalltalk.config import AppConfig, load_config
from smalltalk.interface.base import BaseInterface
from smalltalk.interface.cli import CLIInterface
from smalltalk.tool_registry import ToolRegistry
from smalltalk.tools.datetime_tool import datetime_tools

if TYPE_CHECKING:
    pass

# 인터페이스 타입 → 클래스 매핑
INTERFACE_REGISTRY: dict[str, type[BaseInterface]] = {
    "cli": CLIInterface,
}

# 지연 임포트가 필요한 인터페이스 (의존성이 설치되어야 사용 가능)
LAZY_INTERFACES: dict[str, str] = {
    "telegram": "smalltalk.interface.telegram.TelegramInterface",
    "discord": "smalltalk.interface.discord.DiscordInterface",
}


def _resolve_interface(iface_config) -> BaseInterface:
    """설정에서 인터페이스 인스턴스를 생성합니다."""
    iface_type = iface_config.type

    if iface_type in INTERFACE_REGISTRY:
        cls = INTERFACE_REGISTRY[iface_type]
        return cls()

    if iface_type in LAZY_INTERFACES:
        import importlib

        module_path, _, class_name = LAZY_INTERFACES[iface_type].rpartition(".")
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)

        # InterfaceConfig의 extra 필드를 kwargs로 전달
        kwargs = iface_config.model_dump(exclude={"type"})
        return cls(**{k: v for k, v in kwargs.items() if v is not None})

    raise ValueError(f"알 수 없는 인터페이스 타입: {iface_type}")


class App:
    """SmallTalk 애플리케이션"""

    def __init__(self, config: AppConfig) -> None:
        self._config = config

        # LLM 클라이언트 초기화
        self._orchestrator_client = LLMClient(config.orchestrator)
        self._worker_client = LLMClient(config.worker)

        # 워커 레지스트리 초기화
        self._worker_registry = WorkerRegistry()

        # 기본 도구 레지스트리 구성
        self._tools = ToolRegistry()
        self._tools.merge(datetime_tools)

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

    def _handle_message(self, user_input: str) -> str:
        """사용자 메시지를 오케스트레이터에 전달합니다."""
        return self._orchestrator.run(user_input)

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
