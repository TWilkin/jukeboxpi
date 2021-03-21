import time

from threading import Thread

from jukebox.lcd import LCD


class Clock(object):
    def __init__(self, lcd: LCD, sleep_after: int = 120):
        self.__lcd = lcd
        self.__running = False
        self.__sleep_after = sleep_after

    def start(self):
        if self.__running == False:
            self.__running = True
            self.__thread = Thread(target=self.__run)
            self.__thread.start()

    def stop(self):
        self.__running = False
        self.__thread = None

    def __run(self):
        current_time = time.strftime('%H:%M', time.localtime())
        self.__lcd.set_centre(bottom=current_time)

        sleep_counter = 0

        while self.__running:
            current_time = time.strftime('%H:%M', time.localtime())

            self.__lcd.overwrite(current_time, 5, 1)

            time.sleep(1)

            sleep_counter += 1
            if sleep_counter == self.__sleep_after:
                self.__lcd.turn_off()
                self.stop()
