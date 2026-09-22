# 실습 과제 진행
from pico2d import *

open_canvas(900, 600)

character = load_image('character.png')

def move_circle():
    clear_canvas()
    character.draw(400, 300)
    update_canvas()
    print("Circle")
    pass


def move_rectangle():
    print("Rectangle")
    pass


def move_triangle():
    print("Triangle")
    pass


while True:
    move_circle()
    move_rectangle()
    move_triangle()
    pass

close_canvas()
