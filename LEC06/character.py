
from pico2d import *
import math

open_canvas(900, 600)

character = load_image('character.png')

def move_circle():
    print("Circle")
    for deg in range(0,360, 5):
        rad = math.radians(deg)
        x = 400 + 200 * math.cos(rad)
        y = 300 + 200 * math.sin(rad)
        draw_character(x,y)
      

def draw_character(x,y):
    clear_canvas()
    character.draw(x,y)
    update_canvas()
    delay(0.05)

def draw_top():
    print("Top")
    for y in range(50,550,5):
        draw_character(50, y)


def draw_right():
    print("Right")
    for x in range(50,550,5):
        draw_character(x,550)


def draw_bottom():
    print("Bottom")
    for y in range(550,50,-5):
        draw_character(550, y)


def draw_left():
    for x in range(550,50,-5):
        draw_character(x, 50)
 

def move_rectangle():
    print("Rectangle")
    draw_top()
    draw_right()
    draw_bottom()
    draw_left()


def draw_triangle_line(x, y, deg):
    print("Triangle Line")
    rad = math.radians(deg)

    for i in range(100):
        x += 5 * math.cos(rad)
        y += 5 * math.sin(rad)

        draw_character(x, y)
    return x,y


def move_triangle():
    print("Triangle")
    x,y = 0,0
    for deg in range(0, 360, 120):
        x, y = draw_triangle_line(x, y, deg)

    pass


while True:
    move_circle()
    move_rectangle()
    move_triangle()
    pass

close_canvas()

