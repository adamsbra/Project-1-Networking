import asyncio
import struct
import datetime
import argparse
from file_utils import recv_str_list, recv_str, recv_single_value, send_str, send_str_list, send_integer

users = {}
message_log = []


def add_message_to_log(message):
    """
    Adds a message to the message log. Replaces oldest message
    if the log is at length 10.
    """
    if len(message_log) >= 10:
        message_log.pop(0)
    message_log.append(message)


async def accept_new_user(writer, reader):
    """
    Accept a new user by prompting them for a username and
    adding their name and writer to a dictionary. In addition,
    also starts the process of recieving and sending messages for a particular user.
    """
    send_str(writer, "Enter a username: ")
    await writer.drain()
    username = await recv_str(reader)
    if username in users:
        print("Duplicate")
        await writer.drain()
        writer.close()
        return
    else:
        i = 0
        users[username] = writer
        await send_message_log(writer)
        try:
            await recieve_and_send_message(reader, username)
        except Exception:
            pass
        finally:
            print(username + " disconnected")
            del users[username]


async def send_message_log(writer):
    """
    Sends the server message log to a user, defaults to
    a message if there are no previous messages.
    """
    send_integer(writer, len(message_log))
    i = 0
    if (len(message_log) > 0):
        for message in message_log:
            if i < 10:
                send_str_list(writer, message)
                i += 1
    else:
        send_str_list(writer, ["00:00", "SERVER", "There are no recent messages."])
    await writer.drain()


async def recieve_and_send_message(reader, username):
    """
    Infinite loop which recieves a user message, appends a time,
    and sends the message out to everyone in the server.
    """
    while True:
        message = await recv_str(reader)
        time = datetime.datetime.now().time()
        time = time.strftime("%H:%M:%S")
        message = [time, username, message]
        print(message[0] + ":" + message[1] + "~ " + message[2])
        add_message_to_log(message)
        for writer in users.values():
            send_str_list(writer, message)
            await writer.drain()


async def handle_request(reader, writer):
    """
    Handles initial request and starts the username validation process.
    """
    print("Handling request")
    version = await recv_single_value(reader, "<i")
    if version != 1:
        print("Invalid version")
        await writer.drain()
        writer.close()
        return
    await accept_new_user(writer, reader)


async def chat_server(port):
    print("Server started")
    server = await asyncio.start_server(handle_request, '', port)
    async with server:
        await server.serve_forever()


def main():
    parser = argparse.ArgumentParser(description='TCP Client')
    parser.add_argument("-p", "--port", type=int, help="port that you want", default=25565)
    args = parser.parse_args()
    asyncio.run(chat_server(args.port))


if __name__ == "__main__":
    main()