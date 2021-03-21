import asyncio
import atexit

from mpd.asyncio import MPDClient


async def main():
    print('Jukebox')

    client = MPDClient()
    atexit.register(client.close)

    try:
        await client.connect('localhost', 6600)
    except Exception as e:
        print('Connection to MPD failed:', e)
        return

    print('Connected to MPD version ', client.mpd_version)

    async for _ in client.idle(['player']):
        status = await get_status(client)
        print(status)


async def get_status(client: MPDClient):
    status = await client.status()
    current_song = await client.currentsong()

    sample_rate, bits, channels = status.get('audio', '?:?:?').split(':', 3)

    return {
        'status': status.get('state'),
        'title': current_song.get('title'),
        'artist': current_song.get('artist'),
        'album': current_song.get('album'),
        'sample_rate': sample_rate,
        'bits': bits,
        'channels': channels
    }

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
