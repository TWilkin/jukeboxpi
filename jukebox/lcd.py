import board
import busio

from adafruit_character_lcd.character_lcd_rgb_i2c import Character_LCD_RGB_I2C


class LCD(object):
    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.__lcd = Character_LCD_RGB_I2C(i2c, 16, 2)
        self.__lcd.clear()

    def turn_on(self):
        self.__lcd.dispaly = True
        self.__lcd.backlight = True

    def turn_off(self):
        self.__display = False
        self.__lcd.backlight = False

    def set_message(self, top: str, bottom: str = ''):
        message = f'{top:<15}\n{bottom:<15}'
        self.__lcd.clear()
        self.__lcd.message = message
