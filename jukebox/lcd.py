import board
import busio

from adafruit_character_lcd.character_lcd_rgb_i2c import Character_LCD_RGB_I2C


class LCD(object):
    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.__lcd = Character_LCD_RGB_I2C(i2c, 16, 2)
        self.__lcd.clear()

    def turn_on(self):
        self.__lcd.backlight = True

    def turn_off(self):
        self.__lcd.backlight = False

    def set_message(self, message: str):
        self.__lcd.message = message
