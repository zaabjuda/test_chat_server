# coding=utf-8
__author__ = "Dmitry Zhiltsov"
__copyright__ = "Copyright 2015, Dmitry Zhiltsov"

from twisted.application import service, internet
from twisted.internet import reactor, protocol
from twisted.protocols import basic

from util import to_bytes


class TestChat(basic.LineReceiver):
    def __init__(self):
        self.rooms = []
        self.login = None
        self.server_prefix = "@ACHTUNG!!!"

    def connectionMade(self):
        self.transport.write(to_bytes("Welcome to the test_chat_server\n"))

    def connectionLost(self, reason):
        client = self.factory.clients[self.login]
        rooms = client['rooms']
        for room in rooms:
            for people in self.factory.rooms[room]:
                if people != self.login:
                    current = self.factory.clients[people]
                    protocol = current['protocol']
                    self._send_message(protocol, "user {} has quit the chat room".format(self.login), is_system=True)

    def _send_message(self, protocol, message, is_system=False):
        if is_system:
            message = self.server_prefix + ' ' +message
        protocol.sendLine(to_bytes(message))

    def _join_room(self, room):
        if room in self.rooms:
            self.transport.write(to_bytes("You are already in a room\n"))
            return

        # check if room exists
        if room not in self.factory.rooms:
            self.factory.rooms[room] = []

        # join room
        self.rooms.append(room)
        self.factory.rooms[room].append(self.login)
        self.factory.clients[self.login]["rooms"].append(room)

        self.transport.write(to_bytes("entering room: {}\n".format(room)))

        if self.rooms is not None:
            for person in self.factory.rooms[self.rooms]:
                if self.login != person:
                    # search for this client
                    client = self.factory.clients[person]
                    protocol = client['protocol']
                    self._send_message(protocol, "user {} joined chat".format(self.login), is_system=True)

    def _leave_room(self, room):
        if room not in self.rooms:
            self.transport.write(to_bytes("You not in a room\n"))
            return

        # leave room
        self.factory.rooms[self.rooms].remove(self.login)
        self.factory.clients[self.login]["room"] = None

        if self.rooms is not None:
            for person in self.factory.rooms[self.rooms]:
                if person != self.login:
                    client = self.factory.clients[person]
                    protocol = client['protocol']
                    self._send_message(protocol, "user {} has left chat".format(self.login), is_system=True)
        self.rooms = None

    def _quit(self):
        for room in self.rooms:
            self._leave_room(room)

        self.transport.write(to_bytes('BYE!\n'))
        self.transport.loseConnection()

    def lineReceived(self, line):
        line = line.decode()
        if len(line) == 0:
            return
        if line.startswith('/'):
            command, *args = line[1:].split(' ')
            args = [i for i in map(lambda x: x.strip(), args)]
            if command in self.factory.supported_command:
                getattr(self, self.factory.supported_command[command])(*args)
        elif not self.login:
            self.transport.write(to_bytes("Please use /LOGIN YOUR_NICKNAME to login\n"))
        else:
            if self.rooms is not None:
                for person in self.factory.rooms[self.rooms]:
                    if person != self.login:
                        client = self.factory.clients[person]
                        protocol = client['protocol']
                        protocol.sendLine(to_bytes("{}: {}".format(self.login, line)))

    def _login(self, login):
        # check if login already exists
        if login in self.factory.clients:
            self.transport.write(to_bytes("Name taken.\n"))
            self.transport.write(to_bytes("Login Name?\n"))
            return

        self.login = login
        self.rooms = None
        self.factory.clients[self.login] = {'protocol': self, 'room': self.rooms}
        self.transport.write(to_bytes("Hello {}!\n".format(self.login)))


factory = protocol.ServerFactory()
factory.protocol = TestChat
factory.clients = {}
factory.rooms = {}
factory.supported_command = {'JOIN': '_join_room', 'LEFT': '_leave_room', 'LOGIN': '_login', 'QUIT': '_quit'}

application = service.Application("test_chat_server")
internet.TCPServer(8989, factory).setServiceParent(application)

if __name__ == '__main__':
    reactor.listenTCP(8989, factory)
    reactor.run()
