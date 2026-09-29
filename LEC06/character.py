
from pico2d import *
import math

open_canvas(900, 600)

character = load_image('character.png')
startX = 300
startY = 200
targetX = 300
targetY = 300
speed = 10

def move_circle():
    for deg in range(0,360, speed // 2):
        rad = math.radians(deg)
        x = startX + (targetX / 2) * math.cos(rad)
        y = startY + (targetY / 2) * math.sin(rad)
        draw_character(x,y)
      

def draw_character(x,y):
    clear_canvas()
    character.draw(x,y)
    update_canvas()
    delay(0.05)


def draw_top():
    for y in range(startY,startY + targetY, speed):
        draw_character(startX, y)


def draw_right():
    for x in range(startX,startX + targetX, speed):
        draw_character(x,startY + targetY)


def draw_bottom():
    for y in range(startY + targetY, startY, -speed):
        draw_character(startX + targetX, y)


def draw_left():
    for x in range(startX + targetX, startX, -speed):
        draw_character(x, startY)
 

def move_rectangle():
    draw_top()
    draw_right()
    draw_bottom()
    draw_left()


def draw_triangle_line(x, y, deg):
    rad = math.radians(deg)

    for i in range(30):
        x += speed * math.cos(rad)
        y += speed * math.sin(rad)

        draw_character(x, y)
    return x,y


def move_triangle():
    x,y = startX,startY
    angle = 120
    for i in range(1,4):
        x, y = draw_triangle_line(x, y, i * angle)


while True:
    move_circle()
    delay(1)
    move_rectangle()
    delay(1)
    move_triangle()
    delay(1)

close_canvas()

