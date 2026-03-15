"""SmallTalk — 일상 생활 AI 에이전트 프레임워크"""

import logging

from smalltalk.app import create_app


def main():
    # 로깅 설정 — WARNING 이상만 콘솔 출력 (상세 로그는 logs/ 폴더의 TOML 참고)
    logging.basicConfig(
        level=logging.WARNING,
        format="[%(levelname)s] %(name)s: %(message)s",
    )
    # DEBUG/INFO 콘솔 출력이 필요하면 아래 주석 해제
    # logging.getLogger("smalltalk").setLevel(logging.DEBUG)

    app = create_app()
    app.run()


if __name__ == "__main__":
    main()
