"""SmallTalk — 일상 생활 AI 에이전트 프레임워크"""

import logging

from smalltalk.app import create_app


def main():
    # 로깅 설정 — smalltalk 패키지의 INFO 이상 로그 출력
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(name)s: %(message)s",
    )
    # DEBUG 레벨로 보려면 아래 주석을 해제
    # logging.getLogger("smalltalk").setLevel(logging.DEBUG)

    app = create_app()
    app.run()


if __name__ == "__main__":
    main()
