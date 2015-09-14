# coding=utf-8
__author__ = "Dmitry Zhiltsov"
__copyright__ = "Copyright 2015, Dmitry Zhiltsov"

import json

from strictdict import ValidationError
from twisted.application import service, internet
from twisted.internet import reactor, protocol
from twisted.protocols import basic

from defs import ChatMessage, ChatDataResponse, ChatErrorResponse, ChatResponse, ChatErrorState, supported_commands
from util import to_bytes


class TestChat(basic.LineReceiver):
    delimiter = b'\n'

    def __init__(self):
        self.rooms = []
        self.login = None
        self.server_prefix = "@ACHTUNG!!!"

    def connectionMade(self):
        self._write_service_message(data=ChatDataResponse(msg="Welcome to the test_chat_server", channel='0'))

    def connectionLost(self, reason):
        client = self.factory.clients.get(self.login)
        if not client:
            return
        rooms = client['rooms']
        for room in rooms:
            for people in self.factory.rooms[room]:
                if people != self.login:
                    current = self.factory.clients[people]
                    protocol = current['protocol']
                    resp = ChatDataResponse(msg=self._ser_message("user {} has quit the chat room".format(self.login),
                                                                  is_system=True), channel=room, author=self.login)
                    self._write_usual_message(protocol, data=resp)

    def _ser_message(self, message, is_system=False):
        if is_system:
            message = self.server_prefix + ' ' + message
        return message

    def _join_room(self, room):
        if room.isdigit():
            self.transport.write(to_bytes("Room name is invalid\n"))
            return
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

        self._write_service_message(data=ChatDataResponse(msg="entering room: {}".format(room), channel='0'))

        for person in self.factory.rooms[room]:
            if self.login != person:
                # search for this client
                client = self.factory.clients[person]
                protocol = client['protocol']
                resp = ChatDataResponse(msg=self._ser_message("user {} joined chat".format(self.login), is_system=True),
                                        channel=room, author=self.login)
                self._write_usual_message(protocol, data=resp)

    def _leave_room(self, room):
        if room not in self.rooms:
            self.transport.write(to_bytes("You not in a room\n"))
            return

        # leave room
        self.factory.rooms[room].remove(self.login)
        self.factory.clients[self.login]["room"] = None

        for person in self.factory.rooms[room]:
            if person != self.login:
                client = self.factory.clients[person]
                protocol = client['protocol']
                resp = ChatDataResponse(msg=self._ser_message("user {} has left chat".format(self.login),
                                                              is_system=True), channel=room, author=self.login)
                self._write_usual_message(protocol, data=resp)

    def _quit(self):
        for room in self.rooms:
            self._leave_room(room)

        self.transport.write(to_bytes('BYE!\n'))
        self.transport.loseConnection()

    def lineReceived(self, line):
        line = line.decode()
        if len(line) == 0:
            return
        try:
            msg_data = ChatMessage(**json.loads(line))
        except ValidationError as e:
            self._write_service_message(err=ChatErrorResponse(error=ChatErrorState.protocol_error.value,
                                                              msg="Protocol Error"))
            return
        except ValueError as e:
            self._write_service_message(err=ChatErrorResponse(error=ChatErrorState.serialize_error.value,
                                                              msg="Serialize error"))
            return
        if len(msg_data.msg) == 0:
            return
        if msg_data.msg.startswith('/') and msg_data.channel == '0':
            command, *args = msg_data.msg[1:].split(' ')
            args = [i for i in map(lambda x: x.strip(), args)]
            if command in self.factory.supported_command:
                try:
                    getattr(self, self.factory.supported_command[command])(*args)
                except TypeError as e:
                    self._write_service_message(err=ChatErrorResponse(error=ChatErrorState.command_syntax_failed.value,
                                                           msg='Syntax error'))
            else:
                self._write_service_message(err=ChatErrorResponse(error=ChatErrorState.command_not_found.value,
                                                              msg="Command not supported"))
        elif not self.login:
            self.transport.write(to_bytes("Please use /LOGIN YOUR_NICKNAME to login\n"))
        else:
            self._msg(msg_data)

    def _msg(self, msg_data):
        if msg_data.channel != '0':
            room = msg_data.channel
            if self.factory.rooms.get(room):
                for person in self.factory.rooms[msg_data.channel]:
                        if person != self.login:
                            client = self.factory.clients[person]
                            protocol = client['protocol']
                            resp = ChatDataResponse(msg=msg_data.msg, channel=room, author=self.login)
                            self._write_usual_message(protocol, resp)

    def _login(self, login):
        # check if login already exists
        if login in self.factory.clients:
            self.transport.write(to_bytes("Name taken.\n"))
            self.transport.write(to_bytes("Login Name?\n"))
            return

        self.login = login
        # TODO Load user rooms from storage
        user_rooms = []
        self.factory.clients[self.login] = {'protocol': self, 'rooms': user_rooms}
        self._write_service_message(data=ChatDataResponse(msg="Hello {}!".format(self.login), channel='0'))

    def _write_usual_message(self, protocol, data):
        resp = ChatResponse(data=data)
        protocol.sendLine(to_bytes(json.dumps(resp.to_dict())))

    def _write_service_message(self, data=None, err=None):
        resp = {}
        resp['error'] = err
        resp['data'] = data
        self.transport.write(to_bytes(json.dumps(ChatResponse(**resp).to_dict()) + '\n'))


factory = protocol.ServerFactory()
factory.protocol = TestChat
factory.clients = {}
factory.rooms = {}
factory.supported_command = supported_commands

application = service.Application("test_chat_server")
internet.TCPServer(8989, factory).setServiceParent(application)

if __name__ == '__main__':
    reactor.listenTCP(8989, factory)
    reactor.run()
