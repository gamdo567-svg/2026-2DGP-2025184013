"""소닉 동작을 각각 5회 재생하고 1초 대기하며 순환한다.

실행: python Labs/LEC09/sonic_animation_viewer.py
종료: Escape 또는 창 닫기. 이미지 파일은 이 스크립트와 같은 폴더에 둔다.
"""

from pathlib import Path
from dataclasses import dataclass, replace
from math import pi, sin
import sys
from time import perf_counter

import pico2d

CANVAS_WIDTH, CANVAS_HEIGHT = 800, 600
IMAGE_PATH = Path(__file__).resolve().with_name('sonic-sprite.png')
DEFAULT_FRAME_SECONDS = 0.1
REPEAT_COUNT = 5
WAIT_SECONDS = 1.0

# 이미지 상단 기준 영역 조사. 동작명은 원본에 이름이 없어 시각적으로 명명한다.
# y=38..77: 대기 8장, 위 보기, 웅크리기, 앉아 회전 각 1장
# y=79..117: 걷기 12장 / y=121..163: 달리기 6장
# y=167..199: 공중 회전 9장 / y=206..232: 회전 공 6장
# y=235..278: 고속 달리기 6장 / y=281..323: 잔상 달리기 6장
# y=326..370: 방향 전환 6장, 넘어지기 2장
# y=377..416: 균형 잡기 8장 / y=426..468: 놀라기 2장, 옆 보기 2장
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
    frame_seconds: float = DEFAULT_FRAME_SECONDS
    travel_x: float = 0.0
    jump_height: float = 0.0
    bounce_height: float = 0.0


ANIMATIONS = (
    Animation('idle', '대기', (
        Frame(1, 39, 29, 39), Frame(31, 40, 26, 38),
        Frame(58, 39, 28, 39), Frame(86, 40, 30, 38),
        Frame(118, 40, 30, 38), Frame(150, 40, 30, 38),
        Frame(182, 40, 29, 38), Frame(211, 39, 29, 38),
    )),
    Animation('look_up', '위 보기', (Frame(240, 39, 29, 38),)),
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

# 이동 거리는 5회 재생 전체에 걸쳐 적용한다. 공중 동작은 매 회차마다 도약한다.
MOTION_SETTINGS = {
    'crouch': {'frame_seconds': 0.06},
    'curl': {'frame_seconds': 0.06},
    'walk': {'frame_seconds': 0.08, 'travel_x': 180, 'bounce_height': 5},
    'run': {'frame_seconds': 0.06, 'travel_x': 320, 'bounce_height': 12},
    'spin': {'frame_seconds': 0.055, 'travel_x': 300, 'jump_height': 100},
    'spin_ball': {'frame_seconds': 0.06, 'travel_x': 280, 'bounce_height': 10},
    'fast_run': {'frame_seconds': 0.05, 'travel_x': 340, 'bounce_height': 11},
    'dash': {'frame_seconds': 0.05, 'travel_x': 340, 'bounce_height': 10},
    'turn': {'frame_seconds': 0.07},
    'fall': {'frame_seconds': 0.07},
    'balance': {'frame_seconds': 0.07},
    'surprise': {'frame_seconds': 0.06},
}
ANIMATIONS = tuple(replace(animation, **MOTION_SETTINGS.get(animation.key, {}))
                   for animation in ANIMATIONS)


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

    @property
    def position_offset(self):
        animation = self.animation
        phase = (self.frame_index + self.frame_elapsed / animation.frame_seconds) / len(animation.frames)
        overall = (self.completed_cycles + phase) / REPEAT_COUNT
        if self.waiting:
            overall = 1.0
            phase = 1.0
        x = animation.travel_x * (overall - 0.5)
        y = animation.jump_height * sin(pi * phase)
        y += animation.bounce_height * abs(sin(2 * pi * phase * 2))
        return x, y

    def update(self, dt):
        """넘친 시간을 다음 상태에 넘겨 지연 시에도 재생 순서를 유지한다."""
        while dt > 0:
            duration = WAIT_SECONDS if self.waiting else self.animation.frame_seconds
            elapsed = self.wait_elapsed if self.waiting else self.frame_elapsed
            remaining = duration - elapsed
            if dt + 1e-9 < remaining:
                if self.waiting:
                    self.wait_elapsed += dt
                else:
                    self.frame_elapsed += dt
                return
            dt = max(0.0, dt - remaining)
            if self.waiting:
                self.wait_elapsed = 0.0
                self.waiting = False
                self.completed_cycles = 0
                self.frame_index = 0
                self.animation_index = (self.animation_index + 1) % len(ANIMATIONS)
            else:
                self.frame_elapsed = 0.0
                self.frame_index += 1
                if self.frame_index == len(self.animation.frames):
                    self.completed_cycles += 1
                    self.waiting = self.completed_cycles == REPEAT_COUNT
                    self.frame_index = len(self.animation.frames) - 1 if self.waiting else 0


def calculate_scale():
    frames = [frame for animation in ANIMATIONS for frame in animation.frames]
    return max(1, int(min(
        CANVAS_WIDTH * 0.7 / max(frame.width for frame in frames),
        CANVAS_HEIGHT * 0.7 / max(frame.height for frame in frames),
    )))


def draw_frame(sheet, frame, scale, movement=(0.0, 0.0)):
    sheet.clip_draw(
        *frame.clip(sheet.h), CANVAS_WIDTH / 2 + frame.offset_x * scale + movement[0],
        CANVAS_HEIGHT / 2 + (frame.height / 2 + frame.offset_y - REFERENCE_HEIGHT / 2) * scale + movement[1],
        frame.width * scale, frame.height * scale,
    )


def handle_events():
    return not any(
        event.type == pico2d.SDL_QUIT
        or (event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_ESCAPE)
        for event in pico2d.get_events()
    )


def load_sprite():
    if not IMAGE_PATH.is_file():
        raise FileNotFoundError('이미지 파일이 없습니다.')
    sheet = pico2d.load_image(str(IMAGE_PATH))
    for animation in ANIMATIONS:
        for frame in animation.frames:
            if not (0 <= frame.x < frame.x + frame.width <= sheet.w
                    and 0 <= frame.top < frame.top + frame.height <= sheet.h):
                raise ValueError(f'이미지 영역을 벗어난 프레임: {animation.key}')
    return sheet


def main():
    pico2d.open_canvas(CANVAS_WIDTH, CANVAS_HEIGHT)
    try:
        # 기본 밝은 회색 배경을 유지하고 학습용 격자는 숨긴다.
        pico2d.hide_lattice()
        try:
            sheet = load_sprite()
        except Exception as error:
            detail = str(error) or 'pico2d에서 이미지를 읽을 수 없습니다.'
            print(f'이미지 로드 실패: {IMAGE_PATH}\n{detail}', file=sys.stderr)
            return 1
        playback = Playback()
        scale = calculate_scale()
        previous = perf_counter()
        while handle_events():
            now = perf_counter()
            playback.update(now - previous)
            previous = now
            pico2d.clear_canvas()
            draw_frame(sheet, playback.frame, scale, playback.position_offset)
            pico2d.update_canvas()
            pico2d.delay(0.01)
    finally:
        pico2d.close_canvas()
    return 0


if __name__ == '__main__':
    sys.exit(main())
