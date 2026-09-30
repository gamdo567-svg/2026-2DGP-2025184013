from pico2d import *

open_canvas()

character = load_image('characterSheet.png')
character.draw(400, 300)

animations = [
    [
        (106, 789, 30, 37),
        (137, 789, 20, 34),
        (158, 789, 23, 35),
        (181, 789, 32, 34),
        (213, 789, 33, 33),
        (247, 789, 28, 33),
        (276, 789, 22, 34),
        (299, 789, 24, 35),
        (326, 789, 30, 34),
        (357, 789, 34, 33),
        (391, 789, 30, 33),
    ],
    [
        (132, 607, 30, 34),
        (169, 607, 30, 32),
        (206, 606, 24, 29),
        (235, 606, 25, 42),
        (267, 609, 26, 38),
        (302, 609, 30, 42),
        (339, 609, 30, 41),
    ],
]
for animation in animations:
    for frame in animation:
        x, y, width, height = frame
        clear_canvas()
        character.clip_draw(
            x, y, width, height,
            400, 300,             
            width * 5, height * 5
        )
        update_canvas()
        delay(0.5)

delay(5)
close_canvas()