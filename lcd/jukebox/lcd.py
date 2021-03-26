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


class LCDRowData(object):
    message: str
    scroll: bool
    direction: bool
    offset: int

    def __init__(self, message: str = ' ' * 16, scroll: bool = False):
        self.message = message
        self.scroll = scroll
        self.direction = True
        self.offset = 0


class LCD(object):
    def __init__(self, button_callback):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.__lcd = Character_LCD_RGB_I2C(i2c, 16, 2)
        self.__lcd.columns = 40

        self.__message = [
            LCDRowData(),
            LCDRowData()
        ]

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
            self.__lcd.color = [0, 0, 255]

    def turn_off(self):
        with self.__lock:
            self.__lcd.display = False
            self.__lcd.color = [0, 0, 0]

    def clear(self):
        with self.__lock:
            self.__lcd.clear()

            self.__message = [
                LCDRowData(),
                LCDRowData()
            ]

    def write_message(self, text: str, row: LCDRow, scroll: bool):
        if len(text) < 16:
            text = f'{text:<15}'

        self.__overwrite(text, row)

        with self.__lock:
            self.__message[row.value] = LCDRowData(
                text,
                scroll and len(text) > 16
            )

    def write_centre(self, text: str, row: LCDRow):
        diff = (16 - len(text)) // 2
        text = (' ' * diff) + text

        self.write_message(text, row, False)

    def __overwrite(self, text: str, row: LCDRow):
        with self.__lock:
            if not self.__lcd.display:
                self.turn_on()

            # update only the characters that have changed
            original_len = len(self.__message[row.value].message)
            new_len = len(text)
            for i in range(max(original_len, new_len)):
                char = ' '
                changed = True

                if i < new_len:
                    char = text[i]

                    if i < original_len:
                        changed = self.__message[row.value].message[i] != text[i]

                if changed:
                    self.__lcd.cursor_position(i, row.value)
                    self.__lcd._write8(ord(char), True)

    def __scroll(self):
        async def scroll():
            while True:
                with self.__lock:
                    for row in LCDRow:
                        current = self.__message[row.value]

                        if current.scroll:
                            if current.direction:
                                self.__lcd.move_left()
                                current.offset += 1

                                if current.offset == len(current.message) - 16 + 2:
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
