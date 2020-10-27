import os
import json
import random
import threading
import asyncio

from tornado.ioloop import IOLoop
from tornado.gen import coroutine
from tornado.httpserver import HTTPServer
from tornado.websocket import WebSocketHandler
from tornado.web import Application, RequestHandler
from tornado.netutil import bind_unix_socket
import logging

settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
}

AllWebSockets = []
AllMessages = []


class BroadcastHandler(WebSocketHandler):
    waiters = set()

    def open(self):
        BroadcastHandler.waiters.add(self)

    def on_close(self):
        BroadcastHandler.waiters.remove(self)

    def on_message(self, message):
        logging.warning("ECHO message %s", message)
        for waiter in self.waiters:
            try:
                waiter.write_message(message)
            except Exception:
                logging.error("Error sending message", exc_info=True)



class WorkshopAuthAPI(RequestHandler):
    def get(self):
        self.query()

    def post(self):
        self.query()

    def query(self):
        key = self.get_argument('key', None)
        if key == 'supersecret':
            self.write("1")
        else:
            self.write("0")


class WorkshopWeatherAPI(RequestHandler):
    async def get(self, argument):
        weather = {
            'city': "Munich",
            'country': "Germany",
        }
        if argument == 'today':
            weather.update({
                'temperature': '10.1 C',
                'rain_probability': '90 %',
            })
        elif argument == 'tomorrow':
            weather.update({
                'temperature': '12.8 C',
                'rain_probability': '20 %',
            })
        await asyncio.sleep(1)
        self.set_header("Content-Type", "application/json")
        self.write(weather)


if __name__ == "__main__":
    application = Application([
        (r"/workshop/auth", WorkshopAuthAPI),
        (r"/workshop/weather/(\w+)/?", WorkshopWeatherAPI),
        (r"/broadcast", BroadcastHandler),
    ], **settings)
    application.listen(1234)
    IOLoop.current().start()

