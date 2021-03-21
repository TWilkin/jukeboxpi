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
        current_time = time.strftime('%H:%M:%S', time.localtime())
        self.__lcd.set_centre(bottom=current_time)

        sleep_counter = 0
        interval = 0.3

        previous = current_time
        while self.__running:
            current_time = time.strftime('%H:%M:%S', time.localtime())

            diffs = [i for i in range(len(previous))
                     if previous[i] != current_time[i]]

            for diff in diffs:
                self.__lcd.overwrite(current_time[diff], 4 + diff, 1)

            time.sleep(interval)

            sleep_counter += interval
            if sleep_counter >= self.__sleep_after:
                self.__lcd.turn_off()
                self.stop()

            previous = current_time
