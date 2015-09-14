# coding=utf-8
__author__ = "Dmitry Zhiltsov"
__copyright__ = "Copyright 2015, Dmitry Zhiltsov"

from twisted.application import service, internet
from twisted.internet import reactor, protocol
from twisted.protocols import basic

from util import to_bytes


class TestChat(basic.LineReceiver):
    def __init__(self):
        self.room = None
        self.login = None

    def connectionMade(self):
        self.transport.write(to_bytes("Welcome to the test_chat_server\n"))
        self.transport.write(to_bytes("Login Name?\n"))

    def connectionLost(self, reason):
        print("Lost a client!")

    def _join_room(self, room):
        if self.room is not None:
            self.transport.write(to_bytes("You are already in a room\n"))
            return

        # check if room exists
        if room not in self.factory.rooms:
            self.factory.rooms[room] = [self.login]

        # join room
        self.room = room
        self.factory.rooms[room].append(self.login)
        self.factory.clients[self.login]["room"] = room

        self.transport.write(to_bytes("entering room: {}\n".format(room)))

        if self.room is not None:
            for person in self.factory.rooms[self.room]:
                if self.login != person:
                    # search for this client
                    client = self.factory.clients[person]
                    protocol = client['protocol']
                    protocol.sendLine(to_bytes("@ACHTUNG!!! user {} joined chat".format(self.login)))

    def lineReceived(self, line):
        line = line.decode()
        if len(line) == 0:
            return
        if not self.login:
            self._login(line)
        elif line.startswith('/'):
            command, *args = line[1:].split(' ')
            args = [i for i in map(lambda x: x.strip(), args)]
            if command in self.factory.supported_command:
                getattr(self, self.factory.supported_command[command])(*args)
        else:
            if self.room is not None:
                for person in self.factory.rooms[self.room]:
                    if person != self.login:
                        client = self.factory.clients[person]
                        protocol = client['protocol']
                        protocol.sendLine(to_bytes("{}: {}".format(self.login, line)))

    def message(self, message):
        self.transport.write(message + b'\n')

    def _login(self, login):
        # check if login already exists
        if login in self.factory.clients:
            self.transport.write(to_bytes("Name taken.\n"))
            self.transport.write(to_bytes("Login Name?\n"))
            return

        self.login = login
        self.room = None
        self.factory.clients[self.login] = {'protocol': self, 'room': self.room}
        self.transport.write(to_bytes("Hello {}!\n".format(self.login)))


factory = protocol.ServerFactory()
factory.protocol = TestChat
factory.clients = {}
factory.rooms = {}
factory.supported_command = {'join': '_join_room'}

application = service.Application("test_chat_server")
internet.TCPServer(8989, factory).setServiceParent(application)

if __name__ == '__main__':
    reactor.listenTCP(8989, factory)
    reactor.run()
