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
    offset: int

    def __init__(self, top: str = ' ' * 16, bottom: str = ' ' * 16, scroll: bool = True):
        self.top = top
        self.bottom = bottom
        self.scroll = scroll
        self.offset = 0


class LCD(object):
    def __init__(self, button_callback, pages: int):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.__lcd = Character_LCD_RGB_I2C(i2c, 16, 2)

        self.__pages = pages
        self.__message = [LCDPageData() for _ in range(0, pages)]
        self.__current_page = 0

        self.__lock = Lock()
        self.__scroll_thread = Thread(target=self.__scroll)
        self.__scroll_thread.daemon = True
        self.__scroll_thread.start()

        self.__button_callback = button_callback
        self.__button_thread = Thread(target=self.__button)
        self.__button_thread.daemon = True
        self.__button_thread.start()

    @property
    def page(self):
        return self.__current_page

    @page.setter
    def page(self, new_page: int):
        with self.__lock:
            self.__lcd.clear()

        # emulate circular list of pages
        if new_page >= self.__pages:
            new_page = 0

        self.__current_page = new_page
        self.__write_current_page()

    def next_page(self):
        self.page = self.__current_page + 1

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

            self.__message = [LCDPageData() for _ in range(0, self.__pages)]

    def write_message(self, page: int, top: str = '', bottom: str = ''):
        top = self.__fix_length(top)
        bottom = self.__fix_length(bottom)

        scroll = max(len(top), len(bottom)) > self.__lcd.columns

        with self.__lock:
            self.__message[page] = LCDPageData(
                top,
                bottom,
                scroll
            )

        if self.__current_page == page:
            self.__write_current_page()

    def write_centre(self, page: int, top: str = '', bottom: str = ''):
        top = self.__centre(top)
        bottom = self.__centre(bottom)

        self.write_message(page, top, bottom)

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

    def __write_current_page(self):
        with self.__lock:
            if not self.__lcd.display:
                self.turn_on()

            top = self.__message[self.__current_page].top[:16]
            bottom = self.__message[self.__current_page].bottom[:16]
            self.__message[self.__current_page].offset = 0

            self.__lcd.cursor_position(0, 0)
            self.__lcd.message = f'{top}\n{bottom}'

    def __centre(self, line: str):
        diff = (self.__lcd.columns - len(line)) // 2
        line = (' ' * diff) + line
        return line

    def __fix_length(self, line: str):
        if len(line) > 16:
            line = f'{line}      '

        line = f'{line:<16}'

        return line

    def __scroll(self):
        def append_next_char(page: LCDPageData, row: LCDRow):
            message = page.top if row == LCDRow.TOP else page.bottom

            message_offset = (page.offset + 16) % len(message)
            lcd_offset = (page.offset + self.__lcd.columns) % 40

            self.__lcd.columns = 40
            self.__lcd.cursor_position(lcd_offset, row.value)
            self.__lcd._write8(
                ord(message[message_offset]), True)
            self.__lcd.columns = 16

        async def scroll():
            while True:
                with self.__lock:
                    current = self.__message[self.__current_page]

                    if current.scroll:
                        append_next_char(current, LCDRow.TOP)
                        append_next_char(current, LCDRow.BOTTOM)

                        self.__lcd.move_left()
                        current.offset += 1

                await asyncio.sleep(0.3)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(scroll())
        loop.close()

    def __button(self):
        async def listener():
            while True:
                if self.__lcd.select_button:
                    await self.__button_callback(self, Button.SELECT)

                if self.__lcd.up_button:
                    await self.__button_callback(self, Button.UP)

                if self.__lcd.down_button:
                    await self.__button_callback(self, Button.DOWN)

                if self.__lcd.left_button:
                    await self.__button_callback(self, Button.LEFT)

                if self.__lcd.right_button:
                    await self.__button_callback(self, Button.RIGHT)

                await asyncio.sleep(0.3)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(listener())
        loop.close()
