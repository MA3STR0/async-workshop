#!/usr/bin/env python
import asyncio
import logging
import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado.web import RequestHandler
from tornado.websocket import WebSocketHandler, websocket_connect
import os.path
from tornado.options import define, options
import os


define("port", default=8888, help="run on the given port", type=int)


tornado.ioloop.IOLoop.configure("tornado.platform.asyncio.AsyncIOLoop")
io_loop = tornado.ioloop.IOLoop.current()
asyncio.set_event_loop(io_loop.asyncio_loop)


class NoiseHandler(RequestHandler):
    def get(self):
        self.render("noise.html")


class BroadcastHandler(WebSocketHandler):
    waiters = set()

    def open(self):
        BroadcastHandler.waiters.add(self)

    def on_close(self):
        BroadcastHandler.waiters.remove(self)

    async def on_message(self, message):
        """send message to central server"""
        await self.application.settings['parent_ws'].write_message(message)

    @classmethod
    def on_parent_message(cls, message):
        """receive message from the central server"""
        for waiter in cls.waiters:
            try:
                waiter.write_message(message)
            except Exception:
                logging.error("Error sending message", exc_info=True)



async def make_app():
    parent_ws_url = "wss://caceres.me/broadcast"
    parent_ws = await websocket_connect(parent_ws_url, on_message_callback=BroadcastHandler.on_parent_message)
    return tornado.web.Application(
        [
            (r"/", NoiseHandler),
            (r"/websocket", BroadcastHandler)
        ],
        cookie_secret="FyiHU49fdpqndD8vAg6YHr46gPLjbHJHSgYYI8I5EBypkmyaNMaY1m2xpKWD",
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        xsrf_cookies=True,
        debug=True,
        parent_ws_url=parent_ws_url,
        parent_ws=parent_ws,
    )


if __name__ == "__main__":
    options.parse_command_line()
    app = io_loop.asyncio_loop.run_until_complete(make_app())
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()
