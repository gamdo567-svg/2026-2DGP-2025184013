from pico2d import *
from pathlib import Path
import os
from math import pi
from transitions import Machine, State
from grass import Grass
from boy import Boy as BaseBoy

class AutoRun(State):
    DURATION = 5.0
    SPEED_MULTIPLIER = 2.0
    SCALE = 2.0

    def __init__(self, boy):
        self.boy = boy
        super().__init__(name='AutoRun', on_enter=self.enter, on_exit=self.exit)

    def enter(self):
        self.boy.reset_frame()
        self.boy.pressed_keys.clear()
        self.boy.invincible = True
        self.deadline = get_time() + self.DURATION
        left, right = self.bounds()
        self.boy.x = max(left, min(right, self.boy.x))

    def exit(self):
        self.boy.invincible = False

    def bounds(self):
        margin = 50 * self.SCALE
        return margin, 800 - margin

    def advance(self, dt):
        self.boy.x += self.boy.face_dir * self.boy.MOVE_SPEED * self.SPEED_MULTIPLIER * dt
        self.boy.frame = (self.boy.frame + self.boy.RUN_FPS * self.SPEED_MULTIPLIER * dt) % 8
        left, right = self.bounds()
        while self.boy.x < left or self.boy.x > right:
            if self.boy.x > right:
                self.boy.x = 2 * right - self.boy.x
                self.boy.face_dir = -1
            elif self.boy.x < left:
                self.boy.x = 2 * left - self.boy.x
                self.boy.face_dir = 1
        if self.boy.x == left:
            self.boy.face_dir = 1
        elif self.boy.x == right:
            self.boy.face_dir = -1

    def update(self, dt, now):
        remaining = max(0.0, self.deadline - (now - dt))
        self.advance(min(dt, remaining))
        if now >= self.deadline:
            self.boy.finish_auto_run()

    def draw(self):
        boy = self.boy
        row = 100 if boy.face_dir == 1 else 0
        size = 100 * self.SCALE
        # Lift the center as the sprite grows to keep its feet on the grass.
        y = boy.GROUND_Y + 40 * (self.SCALE - 1)
        boy.image.clip_draw(int(boy.frame) * 100, row, 100, 100,
                            boy.x, y, size, size)


class Boy(BaseBoy):
    IDLE_FPS = 8
    IDLE_FRAMES = 8
    RUN_FPS = 12
    MOVE_SPEED = 250
    JUMP_SPEED = 600
    GRAVITY = 1600
    GROUND_Y = 90
    SLEEP_DELAY = 5.0

    def __init__(self):
        super().__init__()
        self.frame = 0.0
        self.pressed_keys = set()
        self.velocity_y = 0.0
        self.invincible = False
        self.auto_run = AutoRun(self)
        self.last_update = get_time()
        self.machine = Machine(
            model=self,
            states=[State(name='Idle', on_enter='enter_idle'),
                    State(name='Run', on_enter='reset_frame'),
                    State(name='Jump', on_enter='enter_jump'),
                    State(name='SLEEP', on_enter='enter_sleep'),
                    self.auto_run],
            transitions=[
                {'trigger': 'move', 'source': ['Idle', 'SLEEP'], 'dest': 'Run'},
                {'trigger': 'stop', 'source': 'Run', 'dest': 'Idle'},
                {'trigger': 'jump', 'source': ['Idle', 'Run'], 'dest': 'Jump'},
                {'trigger': 'land', 'source': 'Jump', 'dest': 'Run',
                 'conditions': 'is_moving'},
                {'trigger': 'land', 'source': 'Jump', 'dest': 'Idle'},
                {'trigger': 'fall_asleep', 'source': 'Idle', 'dest': 'SLEEP'},
                {'trigger': 'wake_up', 'source': 'SLEEP', 'dest': 'Idle'},
                {'trigger': 'start_auto_run', 'source': 'Idle', 'dest': 'AutoRun'},
                {'trigger': 'finish_auto_run', 'source': 'AutoRun', 'dest': 'Idle'},
                {'trigger': 'cancel_auto_run', 'source': 'AutoRun', 'dest': 'Run'},
            ],
            initial='Idle',
            auto_transitions=False,
        )
        # Machine's initial state does not invoke on_enter automatically.
        self.enter_idle()

    def enter_idle(self):
        self.reset_frame()
        self.idle_started_at = get_time()

    def enter_sleep(self):
        self.reset_frame()
        self.pressed_keys.clear()
        self.velocity_y = 0.0

    def reset_frame(self):
        self.frame = 0.0

    def enter_jump(self):
        self.reset_frame()
        self.velocity_y = self.JUMP_SPEED

    def direction(self):
        return int(SDLK_RIGHT in self.pressed_keys) - int(SDLK_LEFT in self.pressed_keys)

    def is_moving(self):
        return self.direction() != 0

    def handle_event(self, event):
        if event.type not in (SDL_KEYDOWN, SDL_KEYUP):
            return
        if self.is_SLEEP():
            if event.type == SDL_KEYDOWN and event.key in (SDLK_LEFT, SDLK_RIGHT):
                self.pressed_keys.add(event.key)
                self.face_dir = self.direction()
                self.move()
            elif event.type == SDL_KEYDOWN and event.key == SDLK_SPACE:
                if not getattr(event, 'repeat', False):
                    self.pressed_keys.add(SDLK_SPACE)
                    self.wake_up()
            return
        if event.type == SDL_KEYDOWN:
            # Ignore OS key repeat so holding space does not auto-jump on landing.
            if event.key in self.pressed_keys:
                return
            self.pressed_keys.add(event.key)
            if event.key == SDLK_SPACE and not self.is_Jump():
                self.jump()
        else:
            self.pressed_keys.discard(event.key)
        direction = self.direction()
        if direction:
            self.face_dir = direction
        if not self.is_Jump():
            if direction and self.is_Idle():
                self.move()
            elif not direction and self.is_Run():
                self.stop()

    def update(self):
        now = get_time()
        dt = max(0.0, now - self.last_update)
        self.last_update = now
        if self.is_SLEEP():
            return
        self.x = max(25, min(775, self.x + self.direction() * self.MOVE_SPEED * dt))
        if self.is_Jump():
            self.y += self.velocity_y * dt - 0.5 * self.GRAVITY * dt * dt
            self.velocity_y -= self.GRAVITY * dt
            # Use a fixed airborne pose from the run sheet (no jump sheet supplied).
            self.frame = 2
            if self.y <= self.GROUND_Y:
                self.y = self.GROUND_Y
                self.velocity_y = 0.0
                self.land()
        if self.is_Idle():
            self.frame = (self.frame + self.IDLE_FPS * dt) % self.IDLE_FRAMES
            if now - self.idle_started_at >= self.SLEEP_DELAY:
                self.fall_asleep()
        elif self.is_Run():
            self.frame = (self.frame + self.RUN_FPS * dt) % 8

    def draw(self):
        if self.is_SLEEP():
            row = 300 if self.face_dir == 1 else 200
            # Rotate the standing sprite onto the grass to make a lying pose.
            angle = pi / 2 if self.face_dir == 1 else -pi / 2
            self.image.clip_composite_draw(0, row, 100, 100, angle, '',
                                           self.x, self.GROUND_Y - 20, 100, 100)
            return
        if self.is_Idle():
            row = 300 if self.face_dir == 1 else 200
        else:
            row = 100 if self.face_dir == 1 else 0
        self.image.clip_draw(int(self.frame) * 100, row, 100, 100,
                             self.x, self.y)


def handle_events():
    global running

    event_list = get_events()
    for event in event_list:
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False
        else:
            boy.handle_event(event)


def reset_world():
    global world
    global boy

    world = []

    grass = Grass()
    world.append(grass)

    boy = Boy()
    world.append(boy)



def update_world():
    for o in world:
        o.update()
    pass


def render_world():
    clear_canvas()
    for o in world:
        o.draw()
    update_canvas()


def main():
    global running
    running = True
    # Assets are stored beside this file, including when launched elsewhere.
    os.chdir(Path(__file__).resolve().parent)
    open_canvas()
    try:
        reset_world()
        while running:
            handle_events()
            update_world()
            render_world()
            delay(0.01)
    finally:
        close_canvas()


if __name__ == '__main__':
    main()
