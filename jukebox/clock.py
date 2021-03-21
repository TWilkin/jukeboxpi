import time

from threading import Thread

from jukebox.lcd import LCD


class Clock(object):
    def __init__(self, lcd: LCD):
        self.__lcd = lcd

        self.__thread = Thread(target=self.__run)
        self.__running = False

    def start(self):
        if self.__running == False:
            self.__running = True
            self.__thread.start()

    def stop(self):
        self.__running = False

    def __run(self):
        while self.__running:
            current_time = time.strftime('%H:%M:%S', time.localtime())

            self.__lcd.set_centre(bottom=current_time)

            time.sleep(1)
