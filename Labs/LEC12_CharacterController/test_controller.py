"""Headless behavioral checks; run with python -m unittest -v test_controller."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
import main


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        image = patch('boy.load_image', return_value=Mock())
        clock = patch('main.get_time', side_effect=lambda: self.now)
        image.start()
        clock.start()
        self.addCleanup(image.stop)
        self.addCleanup(clock.stop)
        self.boy = main.Boy()

    def key(self, key, down=True, repeat=False):
        self.boy.handle_event(SimpleNamespace(
            type=main.SDL_KEYDOWN if down else main.SDL_KEYUP,
            key=key, repeat=repeat))

    def step(self, dt):
        self.now += dt
        self.boy.update()

    def test_activation_speed_and_invincibility(self):
        self.key(main.SDLK_a)
        self.assertIsInstance(self.boy.auto_run, main.AutoRun)
        self.assertEqual(self.boy.state, 'AutoRun')
        self.assertTrue(self.boy.invincible)
        self.key(main.SDLK_a, False)
        self.step(.1)
        self.assertEqual(self.boy.x, 450)
        self.assertGreater(self.boy.frame, 0)

    def test_five_second_deadline_and_fresh_idle_timer(self):
        self.key(main.SDLK_a)
        self.step(4.999)
        self.assertEqual(self.boy.state, 'AutoRun')
        self.step(.001)
        self.assertEqual(self.boy.state, 'Idle')
        self.assertFalse(self.boy.invincible)
        self.step(4.99)
        self.assertEqual(self.boy.state, 'Idle')
        self.step(.02)
        self.assertEqual(self.boy.state, 'SLEEP')

    def test_both_wall_reflections(self):
        self.key(main.SDLK_a)
        self.boy.x = 690
        self.step(.1)
        self.assertAlmostEqual(self.boy.x, 660)
        self.assertEqual(self.boy.face_dir, -1)
        self.boy.x = 110
        self.step(.1)
        self.assertAlmostEqual(self.boy.x, 140)
        self.assertEqual(self.boy.face_dir, 1)

    def test_large_frame_stays_inside_and_timeout_caps_travel(self):
        self.key(main.SDLK_a)
        self.step(10)
        self.assertEqual(self.boy.state, 'Idle')
        self.assertAlmostEqual(self.boy.x, 500)
        self.assertEqual(self.boy.face_dir, 1)

    def test_entry_at_edge_and_late_activation(self):
        self.boy.x = 775
        self.now = 100
        self.key(main.SDLK_a)
        self.assertEqual(self.boy.x, 700)
        self.step(.1)
        self.assertAlmostEqual(self.boy.x, 650)
        self.assertEqual(self.boy.state, 'AutoRun')

    def test_cancel_each_direction_restores_run_and_size(self):
        for key, direction in [(main.SDLK_LEFT, -1), (main.SDLK_RIGHT, 1)]:
            with self.subTest(direction=direction):
                self.key(main.SDLK_a)
                self.key(key)
                self.assertEqual(self.boy.state, 'Run')
                self.assertFalse(self.boy.invincible)
                self.assertEqual(self.boy.face_dir, direction)
                x = self.boy.x
                self.step(.1)
                self.assertAlmostEqual(self.boy.x, x + direction * 25)
                self.boy.draw()
                self.assertEqual(len(self.boy.image.clip_draw.call_args.args), 6)
                self.key(key, False)
                self.assertEqual(self.boy.state, 'Idle')

    def test_enlarged_draw_both_directions(self):
        self.key(main.SDLK_a)
        for direction, row in [(1, 100), (-1, 0)]:
            self.boy.face_dir = direction
            self.boy.draw()
            args = self.boy.image.clip_draw.call_args.args
            self.assertEqual(args[1], row)
            self.assertEqual(args[-2:], (200, 200))
            self.assertEqual(args[5], 130)

    def test_auto_run_ignores_space_and_a(self):
        self.key(main.SDLK_a)
        deadline = self.boy.auto_run.deadline
        self.step(1)
        self.key(main.SDLK_SPACE)
        self.key(main.SDLK_a)
        self.assertEqual(self.boy.state, 'AutoRun')
        self.assertEqual(self.boy.auto_run.deadline, deadline)
        self.assertEqual(self.boy.y, 90)

    def test_a_does_not_activate_from_other_states(self):
        self.key(main.SDLK_RIGHT)
        self.key(main.SDLK_a)
        self.assertEqual(self.boy.state, 'Run')
        self.key(main.SDLK_a, False)
        self.key(main.SDLK_SPACE)
        self.key(main.SDLK_a)
        self.assertEqual(self.boy.state, 'Jump')
        self.key(main.SDLK_RIGHT, False)
        self.step(1)
        self.step(5)
        self.assertEqual(self.boy.state, 'SLEEP')
        self.key(main.SDLK_a)
        self.assertEqual(self.boy.state, 'SLEEP')

    def test_held_a_cannot_restart_after_timeout(self):
        self.key(main.SDLK_a)
        self.step(5)
        self.key(main.SDLK_a, repeat=True)
        self.assertEqual(self.boy.state, 'Idle')
        self.key(main.SDLK_a, False)
        self.key(main.SDLK_a)
        self.assertEqual(self.boy.state, 'AutoRun')

    def test_sleep_wake_and_jump_regression(self):
        self.step(5)
        self.boy.draw()
        self.assertTrue(self.boy.image.clip_composite_draw.called)
        self.key(main.SDLK_SPACE)
        self.assertEqual(self.boy.state, 'Idle')
        self.key(main.SDLK_SPACE, False)
        self.key(main.SDLK_SPACE)
        self.step(.1)
        self.assertEqual(self.boy.state, 'Jump')
        self.assertGreater(self.boy.y, 90)
        self.step(1)
        self.assertEqual(self.boy.state, 'Idle')
        self.step(5)
        self.key(main.SDLK_LEFT)
        self.assertEqual(self.boy.state, 'Run')
        self.assertEqual(self.boy.face_dir, -1)


if __name__ == '__main__':
    unittest.main()
