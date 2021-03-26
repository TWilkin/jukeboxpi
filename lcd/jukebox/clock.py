import asyncio
import time

from threading import Thread

from jukebox.lcd import LCD, LCDRow


class Clock(object):
    def __init__(self, lcd: LCD, sleep_after: int = 120):
        self.__lcd = lcd
        self.__running = False
        self.__sleep_after = sleep_after

    def start(self):
        if self.__running == False:
            self.__running = True
            self.__thread = Thread(target=self.__run)
            self.__thread.daemon = True
            self.__thread.start()

    def stop(self):
        self.__running = False
        self.__thread = None

    def __run(self):
        async def update_time():
            current_time = time.strftime('%H:%M:%S', time.localtime())
            self.__lcd.overwrite_centre(0, LCDRow.BOTTOM, current_time)

            sleep_counter = 0
            interval = 0.3

            while self.__running:
                current_time = time.strftime('%H:%M:%S', time.localtime())

                self.__lcd.overwrite_centre(0, LCDRow.BOTTOM, current_time)

                await asyncio.sleep(interval)

                sleep_counter += interval
                if sleep_counter >= self.__sleep_after:
                    self.__lcd.turn_off()
                    self.stop()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(update_time())
        loop.close()
