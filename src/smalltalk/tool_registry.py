"""
Tool 등록 및 관리 시스템.

@tool 데코레이터를 통해 함수를 Tool로 등록하고,
OpenAI function calling 규격의 스키마를 자동 생성합니다.
"""

from __future__ import annotations

import inspect
import json
from typing import Any, Callable, get_type_hints


def _python_type_to_json_schema(py_type: type) -> dict[str, str]:
    """Python 타입 힌트를 JSON Schema 타입으로 변환합니다."""
    type_map: dict[type, str] = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
    }
    return {"type": type_map.get(py_type, "string")}


def _parse_docstring_params(docstring: str | None) -> dict[str, str]:
    """
    Google 스타일 docstring에서 파라미터 설명을 추출합니다.

    예:
        Args:
            query: 검색할 키워드 문자열.
            top_k: 반환할 최대 결과 수.
    """
    if not docstring:
        return {}

    params: dict[str, str] = {}
    in_args = False

    for line in docstring.split("\n"):
        stripped = line.strip()

        if stripped.lower().startswith("args:"):
            in_args = True
            continue

        if in_args:
            if stripped == "" or (not stripped.startswith(" ") and ":" not in stripped and stripped.lower().startswith(("returns", "raises", "example"))):
                in_args = False
                continue

            if ":" in stripped:
                param_name, _, desc = stripped.partition(":")
                param_name = param_name.strip()
                desc = desc.strip()
                if param_name and not param_name.startswith(("Returns", "Raises", "Example")):
                    params[param_name] = desc

    return params


def _build_function_schema(func: Callable) -> dict[str, Any]:
    """함수의 타입 힌트와 docstring에서 OpenAI function schema를 생성합니다."""
    hints = get_type_hints(func)
    sig = inspect.signature(func)
    doc = inspect.getdoc(func) or ""
    param_docs = _parse_docstring_params(doc)

    # 첫 줄을 함수 설명으로 사용
    description = doc.split("\n")[0].strip() if doc else func.__name__

    properties: dict[str, Any] = {}
    required: list[str] = []

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue

        py_type = hints.get(param_name, str)
        schema = _python_type_to_json_schema(py_type)

        if param_name in param_docs:
            schema["description"] = param_docs[param_name]

        properties[param_name] = schema

        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


class ToolRegistry:
    """Tool 등록, 조회, 실행을 관리하는 레지스트리"""

    def __init__(self) -> None:
        self._tools: dict[str, Callable] = {}
        self._schemas: dict[str, dict[str, Any]] = {}

    def register(self, func: Callable) -> Callable:
        """함수를 Tool로 등록합니다. 데코레이터로 사용 가능."""
        schema = _build_function_schema(func)
        name = func.__name__
        self._tools[name] = func
        self._schemas[name] = schema
        return func

    def get_openai_tools(self) -> list[dict[str, Any]]:
        """등록된 모든 Tool의 OpenAI function calling 스키마 배열을 반환합니다."""
        return list(self._schemas.values())

    def execute(self, name: str, arguments: dict[str, Any]) -> str:
        """
        이름과 인자로 Tool을 실행합니다.

        Args:
            name: 실행할 Tool 함수 이름.
            arguments: Tool에 전달할 인자 딕셔너리.

        Returns:
            Tool 실행 결과를 문자열로 반환.

        Raises:
            KeyError: 등록되지 않은 Tool 이름일 경우.
        """
        if name not in self._tools:
            raise KeyError(f"등록되지 않은 Tool: {name}")

        result = self._tools[name](**arguments)
        if isinstance(result, str):
            return result
        return json.dumps(result, ensure_ascii=False, default=str)

    def has(self, name: str) -> bool:
        """Tool이 등록되어 있는지 확인합니다."""
        return name in self._tools

    @property
    def names(self) -> list[str]:
        """등록된 Tool 이름 목록을 반환합니다."""
        return list(self._tools.keys())

    def merge(self, other: ToolRegistry) -> None:
        """다른 레지스트리의 Tool들을 현재 레지스트리에 병합합니다."""
        self._tools.update(other._tools)
        self._schemas.update(other._schemas)


def tool(registry: ToolRegistry) -> Callable:
    """
    Tool 등록 데코레이터 팩토리.

    사용법:
        registry = ToolRegistry()

        @tool(registry)
        def get_current_time() -> str:
            '''현재 시간을 반환합니다.'''
            ...
    """

    def decorator(func: Callable) -> Callable:
        registry.register(func)
        return func

    return decorator
