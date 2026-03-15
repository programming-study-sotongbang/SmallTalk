"""
예시 도구: 현재 시간 조회.

Tool 시스템의 사용 예시를 보여주기 위한 간단한 도구입니다.
"""

from __future__ import annotations

from datetime import datetime

from smalltalk.tool_registry import ToolRegistry, tool

# 모듈 레벨 ToolRegistry 인스턴스
datetime_tools = ToolRegistry()


@tool(datetime_tools)
def get_current_time() -> str:
    """현재 날짜와 시간을 반환합니다."""
    now = datetime.now()
    return now.strftime("%Y년 %m월 %d일 %H시 %M분 %S초")


@tool(datetime_tools)
def get_current_date() -> str:
    """오늘 날짜를 반환합니다."""
    return datetime.now().strftime("%Y년 %m월 %d일")
