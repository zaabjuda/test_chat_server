# test_chat_server
Test job from RDS


Protocol description
=====================

Основные понятия
----------------

* Протокол сервера в качестве формата использует JSON (В идеале я хотел сделать на msg_pack но не хватило времени на 
реализацию клиента)
* Сервер всегда возвращает два поля - `data` и `error` 
* Если `error` значит возникла ошибка. `Error` содержит числовой идентификатор ошибки 
(смотри defs.py class ChatErrorState) и текстовое описание ошибки (опционально)
* `Channel` идентификатор комнаты если `channel` == '0' то это сервисный канал 

Комманды
---------

LOGIN
------
Пример запроса:
 {"msg": "/LOGIN Dima", "channel": "0"}
 
Ответ:
{"data": {"channel": "0", "msg": "Hello Dima!"}}

Пример ошибочного запроса:
{"msg": "/LOGIN", "channel": "0"}
{"error": {"msg": "Syntax error", "error": 4}}


JOIN
-----
Пример запроса:
    {"msg": "/JOIN Room1", "channel": "0"}
Ответ который увидят члены комнаты:
{"data": {"channel": "Room1", "author": "Dima", "msg": "@ACHTUNG!!! user Dima joined chat"}}

Ответ:
{"data": {"channel": "0", "msg": "entering room: Room1"}}

LEAVE
-----
Пример запроса:
    {"msg": "/LEFT Room1", "channel": "0"}
Ответ который увидят члены комнаты:
{"data": {"channel": "Room1", "author": "Dima1", "msg": "@ACHTUNG!!! user Dima1 has left chat"}}

QUIT
-----
Приемер:
{"msg": "/QUIT", "channel": "0"}


Write message
-------------
Пример запроса:
    {"msg": "Hello human!", "channel": "Room1"}
где  channel идентификатор комнаты

Ответ который увидят члены комнаты:
{"data": {"channel": "Room1", "author": "Dima1", "msg": "Hello human!"}}


Client usage
------------

Command login
/LOGIN <NICK> - login by nick
/JOIN <Room> - join room by room, if room not exists server create this room
/msg <Room> <msg> - write message to room
/LEFT <Room> - leave from room
/QUIT - quit from all room and disconect on server
/quit - quit fron client
