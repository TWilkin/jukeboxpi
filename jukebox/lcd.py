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
        self.__scroll_thread_run = True
        self.__scroll_thread = Thread(target=self.__scroll)
        self.__scroll_thread.start()

    def stop(self):
        self.turn_off()
        self.__scroll_thread_run = False

    def turn_on(self):
        with self.__lock:
            self.__lcd.display = True
            self.__lcd.color = [0, 0, 255]

    def turn_off(self):
        with self.__lock:
            self.__lcd.display = False
            self.__lcd.color = [0, 0, 0]

    def set_message(self, top: str = None, bottom: str = None):
        if not self.__lcd.display:
            self.turn_on()

        with self.__lock:
            if top is None:
                top = self.__top
            if bottom is None:
                bottom = self.__bottom

            self.__direction = 0
            self.__scroll_index = 0
            self.__top = top
            self.__bottom = bottom

            message = f'{top}\n{bottom}'
            self.__lcd.clear()
            self.__lcd.message = message

    def set_centre(self, top: str = None, bottom: str = None):
        def centre(message: str):
            diff = (16 - len(message)) // 2
            return (' ' * diff) + message

        if top is not None:
            top = centre(top)

        if bottom is not None:
            bottom = centre(bottom)

        self.set_message(top, bottom)

    def overwrite(self, text: str, column: int, row: int):
        def update(old: str):
            return '{}{}{}'.format(old[:column], text, old[column + len(text):])

        if row == 0:
            self.__top = update(self.__top)
        else:
            self.__bottom = update(self.__bottom)

        for char in text:
            self.__lcd.cursor_position(column, row)

            self.__lcd._write8(ord(char), True)

            column += 1
            if column == 16:
                break
        self.__lcd.cursor_position(0, 0)

    def __scroll(self):
        while self.__scroll_thread_run:
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
