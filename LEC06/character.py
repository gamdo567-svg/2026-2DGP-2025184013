
from pico2d import *
import math

open_canvas(900, 600)

character = load_image('character.png')
startX = 300
startY = 200

def move_circle():
    print("Circle")
    for deg in range(0,360, 5):
        rad = math.radians(deg)
        x = startX + 150 * math.cos(rad)
        y = startY + 150 * math.sin(rad)
        draw_character(x,y)
      

def draw_character(x,y):
    clear_canvas()
    character.draw(x,y)
    update_canvas()
    delay(0.05)


def draw_top():
    print("Top")
    for y in range(startY,startY + 200,10):
        draw_character(startX, y)


def draw_right():
    print("Right")
    for x in range(startX,startX + 200,10):
        draw_character(x,startY + 200)


def draw_bottom():
    print("Bottom")
    for y in range(startY + 200, startY, -10):
        draw_character(startX + 200, y)


def draw_left():
    for x in range(startX + 200, startX, -10):
        draw_character(x, startY)
 

def move_rectangle():
    print("Rectangle")
    draw_top()
    draw_right()
    draw_bottom()
    draw_left()


def draw_triangle_line(x, y, deg):
    print("Triangle Line")
    rad = math.radians(deg)

    for i in range(25):
        x += 10 * math.cos(rad)
        y += 10 * math.sin(rad)

        draw_character(x, y)
    return x,y


def move_triangle():
    print("Triangle")
    x,y = startX,startY
    for deg in range(0, 360, 120):
        x, y = draw_triangle_line(x, y, deg)

    pass


while True:
    move_circle()
    delay(1)
    move_rectangle()
    delay(1)
    move_triangle()
    delay(1)
    pass

close_canvas()

