"""소닉 스프라이트 애니메이션 뷰어."""

from pathlib import Path
import sys

import pico2d

CANVAS_WIDTH, CANVAS_HEIGHT = 800, 600
IMAGE_PATH = Path(__file__).resolve().with_name('sonic-sprite.png')


def handle_events():
    return not any(
        event.type == pico2d.SDL_QUIT
        or (event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_ESCAPE)
        for event in pico2d.get_events()
    )


def main():
    pico2d.open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)
    try:
        try:
            if not IMAGE_PATH.is_file():
                raise FileNotFoundError('이미지 파일이 없습니다.')
            sheet = pico2d.load_image(str(IMAGE_PATH))
        except Exception as error:
            print(f'이미지 로드 실패: {IMAGE_PATH}\n{error}', file=sys.stderr)
            return 1
        while handle_events():
            pico2d.clear_canvas()
            pico2d.update_canvas()
            pico2d.delay(0.01)
    finally:
        pico2d.close_canvas()
    return 0


if __name__ == '__main__':
    sys.exit(main())
