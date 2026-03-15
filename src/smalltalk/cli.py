"""SmallTalk CLI 진입점."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path


def _generate_agent_config() -> str:
    """설치된 워커를 자동 검색하여 config.agent.yaml 내용을 생성합니다."""
    from smalltalk.workers import get_worker_catalog

    lines = [
        "# SmallTalk 워커(서브 에이전트) 설정",
        "# 활성화할 워커의 주석을 해제하세요.",
        "",
    ]

    catalog = get_worker_catalog()

    if catalog:
        lines.append("workers:")
        for name, info in catalog.items():
            desc = info.description.split(".")[0]  # 첫 문장만
            lines.append(f"  # - {name:<20s} # {desc}")
    else:
        lines.append("workers: []")

    lines.append("")
    return "\n".join(lines)



def _get_example_content(name: str) -> str:
    """예시 설정 파일 내용을 반환합니다."""
    if "agent" in name:
        return _generate_agent_config()
    return (
        "# SmallTalk 설정 파일\n"
        "# 아래 값들을 실제 환경에 맞게 수정하세요.\n\n"
        "orchestrator:\n"
        '  base_url: "https://openrouter.ai/api/v1"\n'
        '  api_key: "sk-or-your-api-key"\n'
        '  model: "qwen/qwen3.5-30b-a3b"\n'
        "  temperature: 0.7\n"
        "  max_tokens: 4096\n\n"
        "worker:\n"
        '  base_url: "https://openrouter.ai/api/v1"\n'
        '  api_key: "sk-or-your-api-key"\n'
        '  model: "qwen/qwen3.5-4b"\n'
        "  temperature: 0.5\n"
        "  max_tokens: 2048\n\n"
        "agent:\n"
        "  max_loop_iterations: 10\n\n"
        "interfaces:\n"
        "  - type: cli\n"
    )


def init_configs(target_dir: Path | None = None) -> None:
    """설정 파일들을 지정된 경로에 생성합니다."""
    target = target_dir or Path.cwd()
    target.mkdir(parents=True, exist_ok=True)

    for dest_name, example_name in [
        ("config.yaml", "config.example.yaml"),
        ("config.agent.yaml", "config.agent.example.yaml"),
    ]:
        dest = target / dest_name
        if dest.exists():
            print(f"  ⏭️  {dest_name} — 이미 존재합니다. 건너뜁니다.")
            continue

        content = _get_example_content(example_name)
        dest.write_text(content, encoding="utf-8")
        print(f"  ✅ {dest_name} — 생성 완료")

    print()
    print(f"설정 파일이 {target} 에 생성되었습니다.")
    print("config.yaml을 열어 API 키와 모델 설정을 채워주세요.")


def run_app() -> None:
    """앱을 시작합니다."""
    logging.basicConfig(
        level=logging.WARNING,
        format="[%(levelname)s] %(name)s: %(message)s",
    )

    from smalltalk.app import create_app

    app = create_app()
    app.run()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="smalltalk",
        description="SmallTalk — 일상 생활 AI 에이전트",
    )
    parser.add_argument(
        "--init", "-i",
        action="store_true",
        help="현재 디렉토리에 설정 파일(config.yaml, config.agent.yaml)을 생성합니다.",
    )

    args = parser.parse_args()

    if args.init:
        print("📁 SmallTalk 설정 파일을 초기화합니다...\n")
        init_configs()
    else:
        run_app()
