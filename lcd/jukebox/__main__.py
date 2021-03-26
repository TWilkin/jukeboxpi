import asyncio
import atexit
import os
import signal
import sys
import time

from mpd.asyncio import MPDClient
from jukebox.clock import Clock
from jukebox.lcd import Button, LCD, LCDRow


async def main():
    print('Jukebox Pi')

    signal.signal(signal.SIGINT, signal_handler)

    client = MPDClient()
    atexit.register(client.disconnect)

    lcd = LCD(make_callback(client))
    lcd.turn_on()
    atexit.register(lcd.stop)

    clock = Clock(lcd)
    atexit.register(clock.stop)

    try:
        await client.connect('localhost', 6600)
    except Exception as e:
        print('Connection to MPD failed:', e)
        return

    print('Connected to MPD version ', client.mpd_version)

    current_status = await get_status(client)
    show_track(lcd, clock, {}, current_status)

    async for _ in client.idle(['player']):
        status = await get_status(client)
        print(status)

        show_track(lcd, clock, current_status, status)
        current_status = status


async def get_status(client: MPDClient):
    status = await client.status()
    current_song = await client.currentsong()

    sample_rate, bits, channels = status.get('audio', '0:0:0').split(':', 3)

    _, extension = os.path.splitext(current_song.get('file', 'a.nothing'))

    return {
        'state': status.get('state'),
        'title': current_song.get('title'),
        'artist': current_song.get('artist'),
        'album': current_song.get('album'),
        'sample_rate': int(sample_rate) / 1000,
        'bits': int(bits),
        'channels': int(channels),
        'format': extension[1:].upper() if extension != '.nothing' else None
    }


def make_callback(client: MPDClient):
    async def button_callback(button: Button):
        print(button)

        if button == Button.LEFT:
            client.previous()
        elif button == Button.RIGHT:
            client.next()
        elif button == Button.UP:
            client.pause()
        elif button == Button.DOWN:
            client.stop()

    return button_callback


def show_track(lcd: LCD, clock: Clock, current_status, status):
    state = status.get('state')

    if state in ['play', 'pause']:
        clock.stop()

        # only update if it has changed, or we're going from stop
        if current_status.get('state') == 'stop' or not compare_keys(current_status, status, 'title', 'artist'):
            lcd.clear()

            lcd.write_message('{} - {}'.format(
                status.get('artist', ''),
                status.get('title', '')
            ), LCDRow.TOP, True)

            lcd.write_message('{} {:.1f}kHz {}b'.format(
                status.get('format', '?'),
                status.get('sample_rate', 0),
                status.get('bits', 0)
            ), LCDRow.BOTTOM, True)
    elif state == 'stop':
        initial_message(lcd, clock)


def initial_message(lcd: LCD, clock: Clock):
    lcd.clear()
    lcd.write_centre('Jukebox Pi', LCDRow.TOP)
    clock.start()


def compare_keys(state1, state2, *args):
    match = True

    for arg in args:
        match = match and state1.get(arg) == state2.get(arg)

    return match


def signal_handler(signal, frame):
    print('Shutting down')
    sys.exit(0)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())