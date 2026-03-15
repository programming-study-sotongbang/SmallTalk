"""
도구 모듈 자동 검색.

src/smalltalk/tools/ 하위의 모든 도구 모듈을 스캔하여
ToolRegistry 인스턴스를 자동으로 수집하고 병합합니다.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
from pathlib import Path

from smalltalk.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


def discover_all_tools() -> ToolRegistry:
    """tools/ 하위 모듈을 스캔하여 모든 ToolRegistry를 병합해 반환합니다."""
    merged = ToolRegistry()
    package_path = Path(__file__).parent

    for module_info in pkgutil.iter_modules([str(package_path)]):
        if module_info.name.startswith("_"):
            continue

        try:
            module = importlib.import_module(f"smalltalk.tools.{module_info.name}")
        except Exception as e:
            logger.warning("도구 모듈 로드 실패: %s (%s)", module_info.name, e)
            continue

        # 모듈의 모든 ToolRegistry 인스턴스를 병합
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, ToolRegistry):
                merged.merge(attr)
                logger.debug("도구 등록: %s (from %s)", attr.names, module_info.name)

    return merged
