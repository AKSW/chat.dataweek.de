from loguru import logger
import asyncio
from typing import AsyncGenerator

from nio import AsyncClient, MatrixRoom, RoomMessageText, RoomTopicEvent

import re
from datetime import datetime

username_quote = re.compile("\[(.*)\]")

class Broker:
    def __init__(self, config) -> None:
        self.config = config
        self.connections = dict()
        self.messages = dict()

        logger.info("get client")

        self.client = AsyncClient(self.config["server"], self.config["user"])
        logger.info(f"client: {self.client}")
        self.client.add_event_callback(self.message_callback, RoomMessageText)
        self.client.add_event_callback(self.topic_callback, RoomTopicEvent)
        logger.info("event callbacks added")

    async def login(self):
        logger.info(await self.client.login(self.config["password"]))

    def addMessage(self, room_id, message):
        if room_id not in self.messages.keys():
            self.messages[room_id] = list()
        self.messages[room_id].append(message)

    def addConnection(self, room_id, connection):
        if room_id not in self.connections.keys():
            self.connections[room_id] = set()
        self.connections[room_id].add(connection)

    def getConnections(self, room_id):
        if room_id not in self.connections.keys():
            return set()
        return self.connections[room_id]

    async def message_callback(self, room: MatrixRoom, event: RoomMessageText) -> None:
        logger.debug(
            f"Message received in room {room.display_name}\n"
            f"{event.sender} ({room.user_name(event.sender)}) | {event.body}"
        )
        logger.debug(f"{room.room_id} ({type(room.room_id)})")
        if event.sender == self.config["user"]:
            logger.debug(f"split username from {event.body}")
            nickname, body = self.split_username_from_message(event.body)
        else:
            logger.debug("matrix message")
            body = event.body
            nickname = room.user_name(event.sender)
        logger.debug(event.server_timestamp)
        client_msg = {
            'type': 'message',
            'id': event.event_id,
            'time': datetime.fromtimestamp(event.server_timestamp/1000).strftime('%Y-%m-%d %H:%M:%S'),
            'body': body,
            'nickname': nickname
        }
        self.addMessage(room.room_id, client_msg)
        await self.send_message(client_msg, room.room_id)

    async def topic_callback(self, room: MatrixRoom, event: RoomTopicEvent) -> None:
        logger.debug(
            f"Message received in room {room.display_name} ({room.room_id})\n"
            f"topic is: {event.topic} ({event})"
        )
        update = self.create_topic_update(event.topic, event.event_id)
        await self.send_message(update, room.room_id)

    def create_topic_update(self, topic, event_id="init"):
        client_msg = {
            'type': 'topic',
            'id': event_id,
            'body': topic,
        }
        return client_msg

    async def send_message(self, client_msg, room_id) -> None:
        logger.debug(client_msg)
        for connection in self.getConnections(room_id):
            await connection.put(client_msg)

    async def publish(self, message: complex, room_id) -> None:
        message_body = f"[{message['nickname']}] {message['body']}"
        await self.client.room_send(
            room_id=room_id,
            message_type="m.room.message",
            content={"msgtype": "m.text", "body": message_body},
        )

    async def subscribe(self, room_id=None) -> AsyncGenerator[str, None]:
        logger.debug("new subscription")
        connection = asyncio.Queue()
        room = self.client.rooms[room_id]
        update = self.create_topic_update(room.topic)
        await connection.put(update)
        logger.debug(f"deliver history for {room_id}")
        for message in self.messages[room_id]:
            logger.debug(f"deliver: {message}")
            await connection.put(message)
        logger.debug("history done")
        self.addConnection(room_id, connection)
        try:
            while True:
                yield await connection.get()
        finally:
            self.getConnections(room_id).remove(connection)

    def split_username_from_message(self, message: str):
        match = username_quote.match(message)
        if match is None:
            return "unknown", message.strip()
        return match[1], message[len(match[1])+2:].strip()
