"""
This program runs the client for a chat program based on TCP protocol.
Name: Brandon Adams and Trae Freeman
"""

import asyncio
import struct
import socket
import argparse
from file_utils import recv_single_value, recv_str, recv_str_list, send_integer, send_str_list, send_str


async def send_messages(writer, username, reader_task):
    loop = asyncio.get_running_loop()
    while True:
        # Get the message from the user
        message = await loop.run_in_executor(None, input)
        if not message:
            await writer.drain()
            writer.close()
            break
        send_str(writer, message)
        await writer.drain()
        # Broadcast the message


async def recieve_messages(reader):
    while True:
        try:
            message = await recv_str_list(reader)
            print(message[0] + " ~ " + message[1] + " ~ " + message[2])
        except Exception:
            print("Connection Aborted")
            break


def print_log(log, length):
    for message in log:
        print(message[0] + ":" + message[1] + "~ " + message[2])


async def handshake_request(reader, writer):
    send_integer(writer, 1)
    await username_validation(reader, writer)


async def username_validation(reader, writer):
    loop = asyncio.get_running_loop()
    prompt = await recv_str(reader)
    name = await loop.run_in_executor(None, lambda: input(prompt))
    send_str(writer, name)
    await writer.drain()
    try:
        await recieve_message_log(reader, writer, name)
    except Exception:
        print("Username already taken.")
        return


async def recieve_message_log(reader, writer, name):
    length = await recv_single_value(reader, "<i")
    log = []
    for i in range(0, length):
        message = await recv_str_list(reader)
        log.append(message)
    print_log(log, length)
    await start_tasks(reader, writer, name)


async def start_tasks(reader, writer, name):
    reader_task = asyncio.create_task(recieve_messages(reader))
    writer_task = asyncio.create_task(send_messages(writer, name, reader_task))
    await reader_task
    await writer_task


async def chat_client(ip, port):
    print(ip)
    reader, writer = await asyncio.open_connection(host=ip, port=port)
    await handshake_request(reader, writer)


def main():
    parser = argparse.ArgumentParser(description='Client for a TCP chat program.')
    parser.add_argument("-ip", "--ip", type=str, help="The ip that you want to connect to.." default='127.0.0.1')
    parser.add_argument("-p", "--port", type=int, help="The port that you want to connect on."default=25565)
    args = parser.parse_args()
    asyncio.run(chat_client(args.ip, args.port))


if __name__ == "__main__":
    main()