"""소닉 스프라이트 애니메이션 뷰어."""

from pathlib import Path
from dataclasses import dataclass, replace
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
    Frame(1, 39, 29, 39), Frame(31, 40, 26, 38),
    Frame(58, 39, 29, 39), Frame(87, 40, 29, 38),
    Frame(118, 40, 30, 38), Frame(150, 40, 30, 38),
    Frame(182, 40, 32, 38), Frame(214, 40, 30, 37),
)), Animation('look_up', '위 보기', (Frame(244, 38, 25, 39),)))

ANIMATIONS += (
    Animation('crouch', '웅크리기', (Frame(270, 45, 24, 32),)),
    Animation('curl', '앉아 회전', (Frame(302, 51, 29, 26),)),
    Animation('walk', '걷기', tuple(Frame(*rect) for rect in (
        (8, 80, 26, 37), (37, 80, 27, 37), (65, 80, 31, 38),
        (97, 80, 37, 37), (135, 80, 32, 35), (170, 79, 32, 38),
        (206, 79, 26, 38), (238, 80, 24, 37), (263, 80, 30, 37),
        (295, 80, 36, 37), (334, 80, 32, 36), (370, 79, 29, 38),
    ))),
    Animation('run', '달리기', tuple(Frame(*rect) for rect in (
        (1, 124, 33, 40), (39, 124, 35, 39), (89, 125, 35, 38),
        (130, 121, 34, 42), (181, 122, 34, 41), (228, 122, 33, 40),
    ))),
    Animation('spin', '공중 회전', tuple(Frame(*rect) for rect in (
        (1, 169, 29, 30), (35, 167, 29, 31), (67, 169, 30, 29),
        (98, 169, 31, 29), (131, 168, 29, 30), (162, 168, 29, 31),
        (193, 170, 30, 29), (230, 170, 31, 29), (268, 170, 30, 30),
    ))),
    Animation('spin_ball', '회전 공', tuple(Frame(*rect) for rect in (
        (1, 206, 30, 27), (36, 206, 29, 27), (70, 206, 29, 27),
        (105, 206, 29, 27), (139, 206, 29, 27), (174, 206, 29, 27),
    ))),
    Animation('fast_run', '고속 달리기', tuple(Frame(*rect) for rect in (
        (1, 239, 29, 35), (36, 239, 30, 35), (74, 239, 31, 35),
        (111, 238, 31, 36), (149, 239, 30, 35), (186, 238, 31, 36),
    ))),
    Animation('dash', '잔상 달리기', tuple(Frame(*rect) for rect in (
        (1, 283, 29, 35), (36, 283, 30, 35), (72, 286, 39, 31),
        (123, 285, 39, 32), (172, 286, 39, 31), (218, 285, 38, 32),
    ))),
    Animation('turn', '방향 전환', tuple(Frame(*rect) for rect in (
        (1, 326, 24, 45), (31, 327, 29, 44), (65, 327, 20, 44),
        (90, 327, 25, 43), (119, 327, 25, 43), (149, 327, 20, 44),
    ))),
    Animation('fall', '넘어지기', (Frame(184, 341, 40, 28), Frame(232, 341, 39, 27))),
    Animation('balance', '균형 잡기', tuple(Frame(*rect) for rect in (
        (1, 379, 27, 38), (31, 379, 31, 36), (64, 379, 31, 36),
        (99, 377, 33, 38), (136, 379, 32, 36), (176, 379, 33, 36),
        (217, 379, 33, 36), (254, 378, 33, 36),
    ))),
    Animation('surprise', '놀라기', (Frame(6, 429, 34, 40), Frame(49, 426, 34, 43))),
    Animation('look_side', '옆 보기', (Frame(96, 427, 23, 39), Frame(125, 427, 23, 39))),
)

# 행의 바닥선을 기준으로 원본의 상하 움직임을 보존한다.
# 공중 회전과 회전 공은 중심을 기준으로 정렬한다.
GROUND_LINES = {
    'idle': 78, 'look_up': 78, 'crouch': 78, 'curl': 78,
    'walk': 118, 'run': 164, 'fast_run': 274, 'dash': 318,
    'turn': 371, 'fall': 371, 'balance': 417,
    'surprise': 469, 'look_side': 466,
}
REFERENCE_HEIGHT = max(f.height for a in ANIMATIONS for f in a.frames)
ANIMATIONS = tuple(replace(animation, frames=tuple(
    replace(frame, offset_y=(
        GROUND_LINES[animation.key] - frame.top - frame.height
        if animation.key in GROUND_LINES else (REFERENCE_HEIGHT - frame.height) / 2
    )) for frame in animation.frames
)) for animation in ANIMATIONS)


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
            self.animation_index = (self.animation_index + 1) % len(ANIMATIONS)
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


def calculate_scale():
    frames = [frame for animation in ANIMATIONS for frame in animation.frames]
    return max(1, int(min(
        CANVAS_WIDTH * 0.7 / max(frame.width for frame in frames),
        CANVAS_HEIGHT * 0.7 / max(frame.height for frame in frames),
    )))


def draw_frame(sheet, frame, scale):
    sheet.clip_draw(
        *frame.clip(sheet.h), CANVAS_WIDTH / 2 + frame.offset_x * scale,
        CANVAS_HEIGHT / 2 + (frame.height / 2 + frame.offset_y - REFERENCE_HEIGHT / 2) * scale,
        frame.width * scale, frame.height * scale,
    )


def handle_events():
    return not any(
        event.type == pico2d.SDL_QUIT
        or (event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_ESCAPE)
        for event in pico2d.get_events()
    )


def main():
    pico2d.open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)
    try:
        # 기본 밝은 회색 배경을 유지하고 학습용 격자는 숨긴다.
        pico2d.hide_lattice()
        try:
            if not IMAGE_PATH.is_file():
                raise FileNotFoundError('이미지 파일이 없습니다.')
            sheet = pico2d.load_image(str(IMAGE_PATH))
        except Exception as error:
            print(f'이미지 로드 실패: {IMAGE_PATH}\n{error}', file=sys.stderr)
            return 1
        playback = Playback()
        scale = calculate_scale()
        previous = perf_counter()
        while handle_events():
            now = perf_counter()
            playback.update(now - previous)
            previous = now
            pico2d.clear_canvas()
            draw_frame(sheet, playback.frame, scale)
            pico2d.update_canvas()
            pico2d.delay(0.01)
    finally:
        pico2d.close_canvas()
    return 0


if __name__ == '__main__':
    sys.exit(main())
