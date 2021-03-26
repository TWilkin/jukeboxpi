import asyncio
import board
import busio

from adafruit_character_lcd.character_lcd_rgb_i2c import Character_LCD_RGB_I2C
from enum import Enum
from threading import Lock, Thread


class LCDRow(Enum):
    TOP = 0
    BOTTOM = 1


class Button(Enum):
    SELECT = 0
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4


class LCDPageData(object):
    top: str
    bottom: str
    scroll: bool
    direction: bool
    offset: int

    def __init__(self, top: str = ' ' * 16, bottom: str = ' ' * 16, scroll: bool = False):
        self.top = top
        self.bottom = bottom
        self.scroll = scroll
        self.direction = True
        self.offset = 0


class LCD(object):
    def __init__(self, button_callback):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.__lcd = Character_LCD_RGB_I2C(i2c, 16, 2)

        self.__message = [
            LCDPageData(),
        ]
        self.__current_page = 0

        self.__lock = Lock()
        self.__scroll_thread = Thread(target=self.__scroll)
        self.__scroll_thread.daemon = True
        self.__scroll_thread.start()

        self.__button_callback = button_callback
        self.__button_thread = Thread(target=self.__button)
        self.__button_thread.daemon = True
        self.__button_thread.start()

    def stop(self):
        self.turn_off()

    def turn_on(self):
        with self.__lock:
            self.__lcd.display = True
            self.__lcd.color = [0, 0, 128]

    def turn_off(self):
        with self.__lock:
            self.__lcd.display = False
            self.__lcd.color = [0, 0, 0]

    def clear(self):
        with self.__lock:
            self.__lcd.clear()

            self.__message = [
                LCDPageData(),
            ]

    def write_message(self, page: int, top: str = '', bottom: str = '', scroll: bool = True):
        top = self.__fix_length(top)
        bottom = self.__fix_length(bottom)

        with self.__lock:
            if not self.__lcd.display:
                self.turn_on()

            if self.__current_page == page:
                self.__lcd.cursor_position(0, 0)
                self.__lcd.message = f'{top}\n{bottom}'

            self.__message[page] = LCDPageData(
                top,
                bottom,
                scroll
            )

    def write_centre(self, page: int, top: str = '', bottom: str = ''):
        top = self.__centre(top)
        bottom = self.__centre(bottom)

        self.write_message(page, top, bottom, False)

    def overwrite(self, page: int, row: LCDRow, text: str):
        text = self.__fix_length(text)

        with self.__lock:
            if self.__current_page == page:
                message = self.__message[page].top if row == LCDRow.TOP else self.__message[page].bottom

                # update only the characters that have changed
                original_len = len(message)
                new_len = len(text)
                for i in range(max(original_len, new_len)):
                    char = ' '
                    changed = True

                    if i < new_len:
                        char = text[i]

                        if i < original_len:
                            changed = message[i] != text[i]

                    if changed:
                        self.__lcd.cursor_position(i, row.value)
                        self.__lcd._write8(ord(char), True)

            # update the message
            if row == LCDRow.TOP:
                self.__message[page].top = text
            else:
                self.__message[page].bottom = text

    def overwrite_centre(self, page: int, row: LCDRow, text: str):
        text = self.__centre(text)

        self.overwrite(page, row, text)

    def __centre(self, line: str):
        diff = (self.__lcd.columns - len(line)) // 2
        line = (' ' * diff) + line
        return line

    def __fix_length(self, line: str):
        buffer = 40 - 2 - len('...')

        # ensure we don't overflow per-line character buffer
        if len(line) > buffer:
            line = f'{line[:buffer]}...'

        return line

    def __scroll(self):
        async def scroll():
            while True:
                with self.__lock:
                    current = self.__message[self.__current_page]

                    if current.scroll:
                        if current.direction:
                            self.__lcd.move_left()
                            current.offset += 1

                            if current.offset == max(len(current.top), len(current.bottom)) - self.__lcd.columns + 2:
                                current.direction = False
                        else:
                            self.__lcd.move_right()
                            current.offset -= 1

                            if current.offset == -2:
                                current.direction = True

                await asyncio.sleep(0.5)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(scroll())
        loop.close()

    def __button(self):
        async def listener():
            while True:
                if self.__lcd.select_button:
                    await self.__button_callback(Button.SELECT)

                if self.__lcd.up_button:
                    await self.__button_callback(Button.UP)

                if self.__lcd.down_button:
                    await self.__button_callback(Button.DOWN)

                if self.__lcd.left_button:
                    await self.__button_callback(Button.LEFT)

                if self.__lcd.right_button:
                    await self.__button_callback(Button.RIGHT)

                await asyncio.sleep(0.3)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(listener())
        loop.close()
