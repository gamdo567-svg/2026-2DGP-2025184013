"""소닉 스프라이트 애니메이션 뷰어."""

from pathlib import Path

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
        while handle_events():
            pico2d.clear_canvas()
            pico2d.update_canvas()
            pico2d.delay(0.01)
    finally:
        pico2d.close_canvas()


if __name__ == '__main__':
    main()
