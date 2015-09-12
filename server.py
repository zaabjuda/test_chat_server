# coding=utf-8
__author__ = "Dmitry Zhiltsov"
__copyright__ = "Copyright 2015, Dmitry Zhiltsov"

from tornado.ioloop import IOLoop
from tornado.tcpserver import TCPServer


class ChatServer(TCPServer):
    def handle_stream(self, stream, address):
        pass


def main(connections):
    chat_server = ChatServer()
    chat_server.listen(8989)
    IOLoop.instance().start()


chat_connections = {}

if __name__ == '__main__':
    main(chat_connections)
