import aiouring
import asyncio


async def test_inet_server(address):
    print(f'server {address} +++')

    async def callback(r: asyncio.StreamReader, w: asyncio.StreamWriter):
        print('server recv', await r.read(65536))
        w.write(b'Response Data')
        await w.drain()
        w.close()

    server = await asyncio.start_server(callback, address[0], address[1])
    await server.start_serving()
    print(f'server {address} ---')


async def test_inet_client(address):
    await asyncio.sleep(1)
    print(f'client {address} +++')
    r, w = await asyncio.open_connection(address[0], address[1])
    w.write(f"GET / HTTP/1.1\n\nHost: {address[0]}\r\n\r\n".encode())
    await w.drain()
    print('client recv', await r.read(65536))
    print(f'client {address} ---')

asyncio.set_event_loop_policy(aiouring.UringEventLoopPolicy())
loop = asyncio.get_event_loop()
print(loop)
asyncio.ensure_future(test_inet_server(('127.0.0.1', 8065)))
loop.run_until_complete(test_inet_client(('127.0.0.1', 8065)))
