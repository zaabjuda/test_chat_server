# coding=utf-8
__author__ = "Dmitry Zhiltsov"
__copyright__ = "Copyright 2015, Dmitry Zhiltsov"

import json
from sys import stdout

from strictdict import ValidationError
from twisted.internet import reactor, protocol, stdio
from twisted.protocols import basic

from defs import ChatMessage, ChatResponse, supported_commands, ChatErrorState
from util import to_bytes

host = 'localhost'
port = 8989
console_delimiter = b'\n'


class ChatClient(protocol.Protocol):
    def dataReceived(self, data):
        try:
            resp_msg = ChatResponse(**json.loads(data.decode()))
            stdout.write(resp_msg + '\n')
            stdout.flush()
            return
        except (ValueError, ValidationError) as exc:
            response_msg = "Server Error: {} Message: {}".format(resp_msg.error.error,  resp_msg.error.msg)
        if resp_msg.data:
            msg = resp_msg.data.msg
            if resp_msg.data.channel == '0':
                channel = 'SERVICE'
                response_msg = "SENDER: {} {}".format(channel, msg)
            else:
                channel = resp_msg.data.channel
                author = resp_msg.data.author
                response_msg = "{}@{} ---> {}: ".format(channel, author, msg)
        elif resp_msg.error:
            response_msg = "Server Error: {} Message: {}".format(resp_msg.error.error,  resp_msg.error.msg)
        else:
            return
        stdout.write(response_msg + '\n')
        stdout.flush()

    def sendData(self, data):
        self.transport.write(to_bytes(data) + console_delimiter)


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

    def _make_msg(self, line):
        line = line.decode()
        if str(line).startswith('/msg '):
            command, *args = line[1:].split(' ')
            channel = args[0]
            try:
                msg = ' '.join(args[1:])
                self_message = "{}@-=ME=- ---> {}: ".format(channel, msg)
                stdout.write(self_message + '\n')
                stdout.flush()
            except IndexError as exc:
                return
        elif line.startswith('/'):
            command, *args = line[1:].split(' ')
            if command in supported_commands:
                channel = '0'
                msg = line
            else:
                print('Command not supported')
                return
        else:
            print('Command not supported')
            return
        w = ChatMessage(msg=msg, channel=channel)

        self.factory.client.sendData(json.dumps(w.to_dict()))

    def lineReceived(self, line):
        if line == '/quit':
            self.quit()
        else:
            self._make_msg(line)

    def quit(self):
        reactor.stop()


def main():
    factory = ChatClientFactory()
    stdio.StandardIO(Console(factory))
    reactor.connectTCP(host, port, factory)
    reactor.run()


if __name__ == '__main__':
    main()
