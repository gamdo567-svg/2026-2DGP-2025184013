"""소닉 스프라이트 애니메이션 뷰어."""

import pico2d

CANVAS_WIDTH, CANVAS_HEIGHT = 800, 600


def main():
    pico2d.open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)
    try:
        pico2d.clear_canvas()
        pico2d.update_canvas()
    finally:
        pico2d.close_canvas()


if __name__ == '__main__':
    main()
