import asyncio
import board
import busio

from adafruit_character_lcd.character_lcd_rgb_i2c import Character_LCD_RGB_I2C
from enum import Enum
from threading import Lock, Thread
from unidecode import unidecode


class LCDRow(Enum):
    TOP = 0
    BOTTOM = 1


class Button(Enum):
    SELECT = 0
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4


class Row(object):
    __message: str
    __length: int
    __offset: int

    def __init__(self, message: str):
        self.message = message

    def __len__(self):
        return self.__length

    @property
    def message(self):
        return self.__message

    @message.setter
    def message(self, new_message: str):
        new_message = unidecode(new_message)

        if len(new_message) > 16:
            new_message = f'{new_message}      '

        new_message = f'{new_message:<16}'

        self.__message = new_message
        self.__length = len(self.__message)
        self.__offset = 16

    @property
    def next_char(self):
        return self.__message[self.__offset]

    def scroll(self):
        self.__offset += 1

        if self.__offset >= self.__length:
            self.__offset = 0


class LCDPageData(object):
    __top: Row
    __bottom: Row
    __scroll: bool
    __lcd_offset: int

    def __init__(self, top: str = ' ' * 16, bottom: str = ' ' * 16):
        self.__top = Row(top)
        self.__bottom = Row(bottom)
        self.reset()

    @property
    def should_scroll(self):
        return self.__scroll

    @property
    def offset(self):
        return self.__lcd_offset

    @property
    def top(self):
        return self.__top

    @top.setter
    def top(self, new_message: str):
        self.__top = Row(new_message)
        self.reset()

    @property
    def bottom(self):
        return self.__bottom

    @bottom.setter
    def bottom(self, new_message: str):
        self.__bottom = Row(new_message)
        self.reset()

    def scroll(self):
        self.__lcd_offset += 1

        # reset when we hit the end of the buffer
        if self.__lcd_offset >= 40:
            self.__lcd_offset = 0

    def reset(self):
        self.__lcd_offset = 16
        self.__scroll = max(len(self.__top), len(self.__bottom)) > 16


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
        with self.__lock:
            self.__message[page] = LCDPageData(top, bottom)

        if self.__current_page == page:
            self.__write_current_page()

    def write_centre(self, page: int, top: str = '', bottom: str = ''):
        top = self.__centre(top)
        bottom = self.__centre(bottom)

        self.write_message(page, top, bottom)

    def overwrite(self, page: int, row: LCDRow, text: str):
        text = f'{unidecode(text):<15}'

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
                            changed = message.message[i] != char

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

            top = self.__message[self.__current_page].top.message[:16]
            bottom = self.__message[self.__current_page].bottom.message[:16]
            self.__message[self.__current_page].reset()

            self.__lcd.cursor_position(0, 0)
            self.__lcd.message = f'{top}\n{bottom}'

    def __centre(self, line: str):
        diff = (16 - len(line)) // 2
        line = (' ' * diff) + line
        return line

    def __scroll(self):
        def append_next_char(page: LCDPageData, row: LCDRow):
            page_row = page.top if row == LCDRow.TOP else page.bottom

            page_row.scroll()

            self.__lcd.columns = 40
            self.__lcd.cursor_position(page.offset, row.value)
            self.__lcd._write8(ord(page_row.next_char), True)
            self.__lcd.columns = 16

        async def scroll():
            while True:
                with self.__lock:
                    current = self.__message[self.__current_page]

                    if current.should_scroll:
                        append_next_char(current, LCDRow.TOP)
                        append_next_char(current, LCDRow.BOTTOM)

                        self.__lcd.move_left()

                        current.scroll()

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
