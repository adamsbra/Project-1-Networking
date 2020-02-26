import asyncio
import struct
import socket
from file_utils import recv_single_value, recv_str, recv_str_list, send_integer, send_str_list, send_str


async def send_messages(writer, username):
    loop = asyncio.get_running_loop()
    while True:
        # Get the message from the user
        send_integer(writer, 3)
        message = await loop.run_in_executor(None, input)
        if not message:
            writer.close()
            await writer.wait_closed()
            break
        # Broadcast the message
        message = [username, message]
        send_str_list(writer, message)
        await writer.drain()


async def recieve_messages(reader):
    while True:
        message = await recv_str_list(reader)
        if reader
        print(message[0] + ":" + message[1] + "~ " + message[2])


async def print_log(log, length):
    for message in log:
        print(message[0] + ":" + message[1] + "~ " + message[2])


async def handshake_request(reader, writer):
    send_integer(writer, 1)
    value = await recv_single_value(reader, "<i")
    print(value)
    if value == 1:
        await username_validation_int(reader, writer)


async def username_validation_int(reader, writer):
    send_integer(writer, 2)
    await writer.drain()
    await username_validation(reader, writer)


async def username_validation(reader, writer):
    loop = asyncio.get_running_loop()
    prompt = await recv_str(reader)
    name = await loop.run_in_executor(None, lambda: input(prompt))
    send_str(writer, name)
    await writer.drain()
    success = await recv_single_value(reader, "<i")
    if success == 2:
        await recieve_message_log(reader, writer, name)


async def recieve_message_log(reader, writer, name):  
    length = await recv_single_value(reader, "<i")
    log = []
    for i in range(0, length):
        message = await recv_str_list(reader)
        log.append(message)
    await print_log(log, length)
    task1 = asyncio.create_task(send_messages(writer, name))
    task2 = asyncio.create_task(recieve_messages(reader))
    await task1
    await task2

async def chat_client():
    reader, writer = await asyncio.open_connection('127.0.0.1', 25565)
    await handshake_request(reader, writer)

asyncio.run(chat_client())
