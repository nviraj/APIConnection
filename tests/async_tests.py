import asyncio
import time


async def heartbeat():
    while True:
        start = time.time()
        await asyncio.sleep(1)
        delay = time.time() - start - 1
        print(f'heartbeat delay = {delay:.3f}s')


async def process(i):
    ts = time.time()
    while True:
        time.sleep(0.5)
        print(f"task {i} is running...")
        await asyncio.sleep(50 - i/10)
        te = time.time() - ts
        if te > 100:
            return te


async def main():
    # asyncio.create_task(heartbeat())
    tasks = [heartbeat()]
    tasks += [process(i) for i in range(20)]
    await asyncio.gather(*tasks)


asyncio.get_event_loop().run_until_complete(main())
