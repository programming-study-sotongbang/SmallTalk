"""
워커 모듈 자동 검색 및 등록.

src/smalltalk/workers/ 하위의 모든 워커 모듈을 스캔하여
WorkerInfo 객체를 자동으로 수집합니다.
config.agent.yaml에 명시된 워커만 실제로 등록됩니다.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from smalltalk.agent.worker import WorkerInfo

logger = logging.getLogger(__name__)

# 이 패키지 하위의 모든 모듈에서 WorkerInfo 객체를 자동 수집
_WORKER_CATALOG: dict[str, WorkerInfo] = {}


def _discover_workers() -> None:
    """workers/ 하위 모듈을 스캔하여 WorkerInfo를 카탈로그에 등록합니다."""
    from smalltalk.agent.worker import WorkerInfo as _WorkerInfo

    package_path = Path(__file__).parent
    for module_info in pkgutil.iter_modules([str(package_path)]):
        if module_info.name.startswith("_"):
            continue

        try:
            module = importlib.import_module(f"smalltalk.workers.{module_info.name}")
        except Exception as e:
            logger.warning("워커 모듈 로드 실패: %s (%s)", module_info.name, e)
            continue

        # 모듈의 모든 속성 중 WorkerInfo 인스턴스 찾기
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, _WorkerInfo):
                _WORKER_CATALOG[attr.name] = attr
                logger.debug("워커 발견: %s (from %s)", attr.name, module_info.name)


def get_worker_catalog() -> dict[str, WorkerInfo]:
    """발견된 모든 워커의 카탈로그를 반환합니다."""
    if not _WORKER_CATALOG:
        _discover_workers()
    return _WORKER_CATALOG
