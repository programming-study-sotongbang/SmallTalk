"""
예시 워커: 인사 어시스턴트.

워커 작성법의 참고 예시입니다.
실제로 유용한 기능은 없으며, 구조를 보여주기 위한 목적입니다.
"""

from smalltalk.agent.worker import WorkerInfo
from smalltalk.tool_registry import ToolRegistry

greeter_worker = WorkerInfo(
    name="greeter",
    description="인사와 간단한 대화를 나누는 어시스턴트. 환영 인사, 안부 인사 등을 처리합니다.",
    system_prompt=(
        "당신은 친절한 인사 어시스턴트입니다. "
        "사용자에게 따뜻하게 인사하고, 간단한 대화를 나눠주세요. "
        "항상 밝고 긍정적인 톤을 유지합니다."
    ),
    tool_registry=ToolRegistry(),
)
