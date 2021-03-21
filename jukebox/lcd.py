import board
import busio
import time

from adafruit_character_lcd.character_lcd_rgb_i2c import Character_LCD_RGB_I2C
from threading import Lock, Thread


class LCD(object):
    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.__lcd = Character_LCD_RGB_I2C(i2c, 16, 2)

        self.__direction = 0
        self.__scroll_index = 0
        self.__top = ''
        self.__bottom = ''

        self.__lock = Lock()
        self.__scroll_thread = Thread(target=self.__scroll)
        self.__scroll_thread.start()

    def turn_on(self):
        self.__lcd.dispaly = True
        self.__lcd.backlight = True

    def turn_off(self):
        self.__display = False
        self.__lcd.backlight = False

    def set_message(self, top: str, bottom: str = ''):
        with self.__lock:
            self.__direction = 0
            self.__scroll_index = 0
            self.__top = top
            self.__bottom = bottom

            message = f'{top}\n{bottom}'
            self.__lcd.clear()
            self.__lcd.message = message

    def set_track(self, artist: str, title: str):
        top = f'{artist} - {title}'

        self.set_message(top)

    def __scroll(self):
        while True:
            with self.__lock:
                if len(self.__top) > 16:
                    if self.__direction == 0:
                        self.__lcd.move_left()
                        self.__scroll_index += 1

                        if self.__scroll_index == len(self.__top) - 16 + 2:
                            self.__direction = 1
                    else:
                        self.__lcd.move_right()
                        self.__scroll_index -= 1

                        if self.__scroll_index == -2:
                            self.__direction = 0

            time.sleep(0.5)
