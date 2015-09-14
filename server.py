# coding=utf-8
__author__ = "Dmitry Zhiltsov"
__copyright__ = "Copyright 2015, Dmitry Zhiltsov"

from twisted.application import service, internet
from twisted.internet import reactor, protocol
from twisted.protocols import basic


class TestChat(basic.LineReceiver):
    def __init__(self):
        self.room = None
        self.login = None

    def connectionMade(self):
        print("New client!")
        self.factory.clients.append(self)

    def connectionLost(self, reason):
        print("Lost a client!")
        self.factory.clients.remove(self)

    def lineReceived(self, line):
        print("received", repr(line))
        for c in self.factory.clients:
            c.message(line)

    def message(self, message):
        self.transport.write(message + b'\n')

    def _login(self, login):
        # check if login already exists
        if login in self.factory.clients:
            self.transport.write('Name taken.\n')
            self.transport.write('Login Name?\n')
            return

        self.login = login
        self.room = None
        self.factory.clients[self.login] = {'protocol': self, 'room': self.room}
        self.transport.write('Hello %s!\n' % self.login)


factory = protocol.ServerFactory()
factory.protocol = TestChat
factory.clients = []

application = service.Application("test_chat_server")
internet.TCPServer(8989, factory).setServiceParent(application)

if __name__ == '__main__':
    reactor.listenTCP(8989, factory)
    reactor.run()
