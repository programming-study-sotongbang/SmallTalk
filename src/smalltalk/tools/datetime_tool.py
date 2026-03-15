"""
예시 도구: 현재 날짜/시간 조회.

Tool 시스템의 사용 예시를 보여주기 위한 간단한 도구입니다.
"""

from __future__ import annotations

from datetime import datetime

from smalltalk.tool_registry import ToolRegistry, tool

# 모듈 레벨 ToolRegistry 인스턴스
datetime_tools = ToolRegistry()


@tool(datetime_tools)
def get_current_datetime() -> str:
    """현재 날짜, 시간, 요일을 반환합니다."""
    now = datetime.now()
    weekday = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"][now.weekday()]
    return now.strftime(f"%Y년 %m월 %d일 ({weekday}) %H시 %M분 %S초")
