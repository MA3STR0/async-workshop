#!/usr/bin/env python
import asyncio
import logging
import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado.web import RequestHandler
from tornado.websocket import websocket_connect
import os.path
from tornado.options import define, options
from tornado.httpclient import AsyncHTTPClient
import os
import aioredis


define("port", default=8888, help="run on the given port", type=int)


tornado.ioloop.IOLoop.configure("tornado.platform.asyncio.AsyncIOLoop")
io_loop = tornado.ioloop.IOLoop.current()
asyncio.set_event_loop(io_loop.asyncio_loop)


services = {
    'auth': 'http://caceres.me/workshop/auth?key=supersecret',
    'weather': 'http://127.0.0.1:8080/forecast',
}


class ApiHandler(RequestHandler):
    async def get(self, service):
        self.http= AsyncHTTPClient()
        if not service:
            self.write(f"Specify a service endpoint. Available: {list(services.keys())}")
            return
        endpoint = services.get(service)
        if not endpoint:
            raise tornado.web.HTTPError(404)
        response = await self.http.fetch(endpoint)
        result = response.body
        self.write(result)


class CachedApiHandler(RequestHandler):
    async def prepare(self, **kwargs):
        self.http= AsyncHTTPClient()
        self.redis = await aioredis.create_redis_pool('redis://caceres.me',
                                                      password='lulz@workshop')
        super().prepare(**kwargs)

    async def get(self, service):
        if not service:
            self.write(f"Specify a service endpoint. Available: {list(services.keys())}")
            return
        result = await self.redis.get(service, encoding='utf-8')
        if not result:
            endpoint = services.get(service)
            if not endpoint:
                raise tornado.web.HTTPError(404)
            response = await self.http.fetch(endpoint)
            result = response.body
            await self.redis.set(service, result)
            logging.info("Saved to cache")
        self.write(result)




async def make_app():
    return tornado.web.Application(
        [
            (r"/(.*)?/?", ApiHandler),
        ],
        cookie_secret="FyiHU49fdpqndD8vAg6YHr46gPLjbHJHSgYYI8I5EBypkmyaNMaY1m2xpKWD",
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        xsrf_cookies=True,
        debug=True,
    )


if __name__ == "__main__":
    options.parse_command_line()
    app = io_loop.asyncio_loop.run_until_complete(make_app())
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()
