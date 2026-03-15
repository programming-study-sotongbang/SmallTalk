"""SmallTalk — 일상 생활 AI 에이전트 프레임워크"""

from smalltalk.app import create_app


def main():
    app = create_app()
    app.run()


if __name__ == "__main__":
    main()
