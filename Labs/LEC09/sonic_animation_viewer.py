"""소닉 스프라이트 애니메이션 뷰어."""

from pathlib import Path
from dataclasses import dataclass
import sys
from time import perf_counter

import pico2d

CANVAS_WIDTH, CANVAS_HEIGHT = 800, 600
IMAGE_PATH = Path(__file__).resolve().with_name('sonic-sprite.png')
FRAME_SECONDS = 0.1
REPEAT_COUNT = 5
WAIT_SECONDS = 1.0

# 이미지 상단 기준 영역 조사. 동작명은 원본에 이름이 없어 시각적으로 명명한다.
# y=38..77: 대기 8장, 위 보기, 웅크리기, 앉아 회전 각 1장
# y=78..120: 걷기 12장 / y=123..164: 달리기 6장
# y=168..201: 공중 회전 9장 / y=204..233: 회전 공 6장
# y=235..278: 고속 달리기 6장 / y=281..323: 잔상 달리기 6장
# y=327..372: 방향 전환 6장, 넘어지기 2장
# y=379..419: 균형 잡기 8장 / y=426..468: 놀라기 2장, 옆 보기 2장
# y>=469: 크레딧과 장식 캐릭터로 재생에서 제외한다.


@dataclass(frozen=True)
class Frame:
    x: int
    top: int
    width: int
    height: int
    offset_x: float = 0
    offset_y: float = 0

    def clip(self, image_height):
        return self.x, image_height - self.top - self.height, self.width, self.height


@dataclass(frozen=True)
class Animation:
    key: str
    name: str
    frames: tuple[Frame, ...]


ANIMATIONS = (Animation('idle', '대기', (
    Frame(1, 38, 28, 39), Frame(31, 38, 26, 39),
    Frame(58, 38, 28, 39), Frame(87, 38, 29, 39),
    Frame(118, 38, 30, 39), Frame(150, 38, 30, 39),
    Frame(182, 38, 30, 39), Frame(214, 38, 29, 39),
)),)


class Playback:
    def __init__(self):
        self.animation_index = 0
        self.frame_index = 0
        self.frame_elapsed = 0.0
        self.completed_cycles = 0
        self.waiting = False
        self.wait_elapsed = 0.0

    @property
    def animation(self):
        return ANIMATIONS[self.animation_index]

    @property
    def frame(self):
        return self.animation.frames[self.frame_index]

    def update(self, dt):
        if self.waiting:
            self.wait_elapsed += dt
            if self.wait_elapsed < WAIT_SECONDS:
                return
            dt = self.wait_elapsed - WAIT_SECONDS
            self.wait_elapsed = 0.0
            self.waiting = False
            self.completed_cycles = 0
            self.frame_index = 0
        self.frame_elapsed += dt
        while self.frame_elapsed >= FRAME_SECONDS:
            self.frame_elapsed -= FRAME_SECONDS
            self.frame_index = (self.frame_index + 1) % len(self.animation.frames)
            if self.frame_index == 0:
                self.completed_cycles += 1
                if self.completed_cycles == REPEAT_COUNT:
                    self.frame_index = len(self.animation.frames) - 1
                    self.waiting = True
                    self.wait_elapsed = self.frame_elapsed
                    self.frame_elapsed = 0.0
                    break


def draw_frame(sheet, frame):
    sheet.clip_draw(*frame.clip(sheet.h), CANVAS_WIDTH // 2, CANVAS_HEIGHT // 2)


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
        playback = Playback()
        previous = perf_counter()
        while handle_events():
            now = perf_counter()
            playback.update(now - previous)
            previous = now
            pico2d.clear_canvas()
            draw_frame(sheet, playback.frame)
            pico2d.update_canvas()
            pico2d.delay(0.01)
    finally:
        pico2d.close_canvas()
    return 0


if __name__ == '__main__':
    sys.exit(main())
