import board
import busio
import time

from adafruit_character_lcd.character_lcd_rgb_i2c import Character_LCD_RGB_I2C
from enum import Enum
from threading import Lock, Thread


class LCDRow(Enum):
    TOP = 0
    BOTTOM = 1


class LCDRowData(object):
    message: str

    def __init__(self):
        self.message = ' ' * 16


class LCD(object):
    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.__lcd = Character_LCD_RGB_I2C(i2c, 16, 2)

        self.__message = [
            LCDRowData(),
            LCDRowData()
        ]

        self.__lock = Lock()
        # self.__scroll_thread_run = True
        # self.__scroll_thread = Thread(target=self.__scroll)
        # self.__scroll_thread.start()

    def stop(self):
        self.turn_off()
        # self.__scroll_thread_run = False

    def turn_on(self):
        with self.__lock:
            self.__lcd.display = True
            self.__lcd.color = [0, 0, 255]

    def turn_off(self):
        with self.__lock:
            self.__lcd.display = False
            self.__lcd.color = [0, 0, 0]

    def write_message(self, text: str, row: LCDRow):
        if len(text) < 16:
            text = f'{text:<15}'

        self.__overwrite(text, row)

    def write_centre(self, text: str, row: LCDRow):
        diff = (16 - len(text)) // 2
        message = (' ' * diff) + text

        self.__overwrite(message, row)

    def __overwrite(self, text: str, row: LCDRow):
        with self.__lock:
            if not self.__lcd.display:
                self.turn_on()

            # find the characters that have changed
            diffs = [i for i in range(min(len(text), 16))
                     if self.__message[row.value].message[i] != text[i]]

            for i in diffs:
                if i > 16:
                    break

                self.__lcd.cursor_position(i, row.value)
                self.__lcd._write8(ord(text[i]), True)

            self.__message[row.value].message = text


"""     def __scroll(self):
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

            time.sleep(0.5) """
