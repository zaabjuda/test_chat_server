# coding=utf-8
__author__ = "Dmitry Zhiltsov"
__copyright__ = "Copyright 2015, Dmitry Zhiltsov"

from sys import stdout

from twisted.internet import reactor, protocol, stdio
from twisted.protocols import basic

host = 'localhost'
port = 8989
console_delimiter = b'\n'


class ChatClient(protocol.Protocol):
    def dataReceived(self, data):
        stdout.write(data.decode())
        stdout.flush()

    def sendData(self, data):
        self.transport.write(data + console_delimiter)


class ChatClientFactory(protocol.ClientFactory):
    def startedConnecting(self, connector):
        print('Starting connection to server.')

    def buildProtocol(self, addr):
        self.client = ChatClient()
        self.client.name = 'chat_client'
        return self.client

    def clientConnectionFailed(self, connector, reason):
        print('Connection failed with reason:', reason)


class Console(basic.LineReceiver):
    factory = None
    delimiter = console_delimiter

    def __init__(self, factory):
        self.factory = factory

    def lineReceived(self, line):
        if line == 'quit':
            self.quit()
        else:
            self.factory.client.sendData(line)

    def quit(self):
        reactor.stop()


def main():
    factory = ChatClientFactory()
    stdio.StandardIO(Console(factory))
    reactor.connectTCP(host, port, factory)
    reactor.run()


if __name__ == '__main__':
    main()
