from pico2d import *

open_canvas()

character = load_image('characterSheet.png')
character.draw(400, 300)

animation = [
    (106, 786, 30, 37),
    (137, 789, 20, 34),
    (158, 789, 24, 35),
    (183, 789, 30, 34),
    (214, 789, 30, 33),
    (245, 789, 28, 33),
    (276, 789, 22, 34),
    (299, 789, 24, 35),
    (326, 789, 30, 34),
    (357, 789, 32, 33),
    (390, 789, 30, 33),
]
for frame in animation:
    x, y, width, height = frame
    clear_canvas()
    character.clip_draw(
        x, y, width, height,
        400, 300,             
        width, height 
    )
    update_canvas()
    delay(1)

delay(5)
close_canvas()