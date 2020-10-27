import asyncio
import aiohttp
from aiohttp import web

loop = asyncio.get_event_loop()


async def handle_today(request):
    url = "https://caceres.me/workshop/weather/today"
    async with aiohttp.ClientSession(loop=loop) as session:
        async with session.get(url) as response:
            result = await response.json()
    text = f"Today it's {result['temperature']} in Munich"
    return web.Response(text=text)


async def handle_forecast(request):
    urls = [
        "https://caceres.me/workshop/weather/today",
        "https://caceres.me/workshop/weather/tomorrow"
    ]
    async with aiohttp.ClientSession(loop=loop) as session:
        futures = [session.get(url) for url in urls]
        done, pending = await asyncio.wait(futures)
        done, pending = await asyncio.wait(
            [task.result().json() for task in done]
        )
    results = [response.result() for response in done]
    text = f"Today it's {results[0]['temperature']} in Munich. Tomorrow it's {results[1]['temperature']}"
    return web.Response(text=text)


app = web.Application()
app.add_routes([
    web.get('/today', handle_today),
    web.get('/forecast', handle_forecast),
])

if __name__ == '__main__':
    web.run_app(app)
