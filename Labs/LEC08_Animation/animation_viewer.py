from pico2d import *

open_canvas()

character = load_image('characterSheet.png')
character.draw(400, 300)
update_canvas()
delay(5)
close_canvas()