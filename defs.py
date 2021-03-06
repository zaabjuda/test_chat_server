# coding=utf-8
__author__ = "Dmitry Zhiltsov"
__copyright__ = "Copyright 2015, Dmitry Zhiltsov"


from enum import Enum, unique
from strictdict import StrictDict
from strictdict import fields as f
from strictdict.api import optlist, opt

supported_commands = {'JOIN': '_join_room', 'LEFT': '_leave_room', 'LOGIN': '_login', 'QUIT': '_quit'}


@unique
class ChatErrorState(Enum):
    user_exist = 1
    room_not_found = 2
    command_not_found = 3
    command_syntax_failed = 4
    room_name_invalid = 5
    unknow_error = 100
    serialize_error = 101
    protocol_error = 102


class ChatMessage(StrictDict):
    msg = f.String(required=True)
    channel = f.String(required=True)
    args = optlist(f.String)


class ChatDataResponse(ChatMessage):
    author = f.String(required=False)


class ChatErrorResponse(StrictDict):
    error = f.Int(required=True)
    msg = f.String(required=False)


class ChatResponse(StrictDict):
    data = opt(ChatDataResponse)
    error = opt(ChatErrorResponse)
