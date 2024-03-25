#!/usr/bin/env python
from loguru import logger
import os
import json
from aiohttp import web
import asyncio
import socketio
from chat.broker import Broker

sio = socketio.AsyncServer(async_mode="aiohttp", cors_allowed_origins=json.loads(os.environ.get("FASTBOT_CORS_ALLOWED_ORIGIN")))

async def matrix_connect(app):
    logger.debug("matrix_connect")
    """
    Config should contain:
    - password
    - server
    - user
    """
    broker_config = {
        "DEBUG": os.environ.get("FASTBOT_DEBUG"),
        "password": os.environ.get("FASTBOT_password"),
        "server": os.environ.get("FASTBOT_server"),
        "user": os.environ.get("FASTBOT_user")
    }
    logger.debug(broker_config)
    app["broker"] = Broker(broker_config)

    app['room_list'] = dict()

    """Example of how to send server generated events to clients."""
    await app["broker"].login()
    logger.debug("syncing_forever")
    app['matrix_sync'] = asyncio.create_task(app["broker"].client.sync_forever(timeout=30000))
    app['room_list_tasks'] = asyncio.create_task(room_list_tasks(app))
    # await app["broker"].client.sync_forever(timeout=30000)
    logger.debug("synced_forever")


async def room_list_tasks(app):
    while True:
        logger.debug(f"rooms befor: {app['room_list']}")
        await app["broker"].client.synced.wait()
        logger.debug(f"rooms: {app['broker'].client.rooms}")
        updated = False
        for room_id in app['broker'].client.rooms.keys():
            if room_id not in app['room_list'].keys():
                app['room_list'][room_id] = app['broker'].client.rooms[room_id].display_name
                updated = True
        if updated:
            logger.debug(f"rooms updated: {app['room_list']}")
            await sio.emit('streams_update', app['room_list'])


    # yield
async def matrix_disconnect(app):
    logger.info("Shuting down")
    logger.info(app['matrix_sync'])
    logger.info(app['room_list_tasks'])
    await app["broker"].client.close()
    app['matrix_sync'].cancel()
    app['room_list_tasks'].cancel()
    await app['matrix_sync']
    await app['room_list_tasks']
    logger.info(app['matrix_sync'])
    logger.info(app['room_list_tasks'])
    await asyncio.sleep(0.50)
    logger.info(app['matrix_sync'])
    logger.info(app['room_list_tasks'])
    logger.info("Shutdown")

async def server_message_loop(app, sid, room_id):
    logger.info(f"subscribe to broker sid: {sid}")
    async for message in app["broker"].subscribe(room_id):
        logger.info(f"send message to ws client ({sid}): {message}")
        await sio.emit('server_message', message, to=sid)

@sio.event
async def connect(sid, environ, auth):
    """Get a connection event from a client"""
    logger.info(f"connected auth={auth} sid={sid}")
    #await sio.emit('server_message', (1, 2, {'hello': 'you'}), to=sid)
    # await sio.emit('server_message', {"nickname": "nick", "body": "hallo vom server", "channel": "a", "time": time.time()})
    await sio.emit('streams_update', app['room_list'])
    # sio_server_message_loop = sio.start_background_task(server_message_loop, app, sid)
    # await sio.save_session(sid, {'server_message_loop': sio_server_message_loop})

@sio.event
async def client_zapp(sid, room_id):
    """Receive a zap event from the client."""
    logger.info(f"client zapp to: {room_id} sid={sid}")
    session = await sio.get_session(sid)
    logger.info(f"session is: {session}")
    if 'server_message_loop' in session.keys():
        session['server_message_loop'].cancel()
    sio_server_message_loop = sio.start_background_task(server_message_loop, app, sid, room_id)
    await sio.save_session(sid, {'server_message_loop': sio_server_message_loop})
    await sio.emit('streams_update', app['room_list'], to=sid)
    # await app["broker"].publish(client_msg)

@sio.event
async def client_message(sid, client_msg, room_id):
    """Receive a message from the client."""
    logger.info(f"get a message from socket.io client: {client_msg} sid={sid}")
    await app["broker"].publish(client_msg, room_id)

@sio.event
async def disconnect(sid):
    """Get a disconnection event from a client"""
    logger.info(f"disconnected sid={sid}")
    session = await sio.get_session(sid)
    logger.info(f"session is: {session}")
    if 'server_message_loop' in session.keys():
        session['server_message_loop'].cancel()

async def index(request):
    """Serve the client-side application."""
    with open('static/chat.html') as f:
        return web.Response(text=f.read(), content_type='text/html')

app = web.Application()
sio.attach(app)
# app.cleanup_ctx.append(background_tasks)
app.on_startup.append(matrix_connect)
app.on_cleanup.append(matrix_disconnect)
app.router.add_static('/static', 'static')
app.router.add_get('/', index)

if __name__ == '__main__':
    web.run_app(app, port=3000)
    #uvicorn.run(app, host='127.0.0.1', port=8000)
