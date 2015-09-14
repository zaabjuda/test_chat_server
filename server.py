# coding=utf-8
__author__ = "Dmitry Zhiltsov"
__copyright__ = "Copyright 2015, Dmitry Zhiltsov"

import logging

from tornado.ioloop import IOLoop
from tornado.tcpserver import TCPServer

class ChatConnection(object):
    def __init__(self, stream, address, connections):
        logging.info("receive a new connection from {}".format(address))
        self.state = "AUTH"
        self.name = None
        self.connections = connections
        self.stream = stream
        self.address = address
        self.stream.set_close_callback(self._on_close)
        self.stream.read_until('\n', self._on_read_line)
        stream.write("Please put your name: ", self._on_write_complete)

    def _on_read_line(self, data):
        logging.info("read a new line from {}".format(self.address))
        if self.state == "AUTH":
            name = data.rstrip()
            if self.connections.has_key(name):
                self.stream.write("Name already exists, choose another: ".format(self._on_write_complete))
                return
            self.stream.write("Welcome, {}!\n".format(name), self._on_write_complete)
            self.connections[name] = self
            self.name = name
            self.state = "CHAT"
            message = "{} has arrived\n".format(self.name)
            for _,conn in self.connections.iteritems():
                if conn != self:
                    conn.stream.write(message, self._on_write_complete)
        else:
            message = "<{}> {}\n".format(self.name, data.rstrip())
            for _,conn in self.connections.iteritems():
                if conn != self:
                    conn.stream.write(message, self._on_write_complete)

    def _on_write_complete(self):
        if not self.stream.reading():
            self.stream.read_until('\n', self._on_read_line)

    def _on_close(self):
        logging.info("Client close connection {}".format(self.address))
        if self.name != None:
            del self.connections[self.name]
            message = "{} has left\n".format(self.name)
            for _,conn in self.connections.iteritems():
                conn.stream.write(message, self._on_write_complete)


class ChatServer(TCPServer):
    def handle_stream(self, stream, address):
        ChatConnection(stream, address, chat_connections)


def main(connections):
    chat_server = ChatServer()
    chat_server.listen(8989)
    IOLoop.instance().start()


chat_connections = {}

if __name__ == '__main__':
    main(chat_connections)
