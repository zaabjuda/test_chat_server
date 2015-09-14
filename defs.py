# coding=utf-8
__author__ = "Dmitry Zhiltsov"
__copyright__ = "Copyright 2015, Dmitry Zhiltsov"


from enum import Enum, unique


@unique
class ChatConnectionState(Enum):
    auth = 1
    chat = 2
