from pico2d import *
import math

open_canvas(800, 600)
character = load_image('character.png')

centerX = 400
centerY = 300

radius = 200

angle = 0

while 1:
    clear_canvas()

    x = centerX + radius * math.cos(angle)
    y = centerY + radius * math.sin(angle)

    character.draw(x, y)

    update_canvas()

    angle += 0.02
    if angle >= 2 * math.pi:
        angle = 0

    delay(0.01)

close_canvas()