import asyncio
import struct
import datetime
from file_utils import recv_str_list, recv_str, recv_single_value, send_str, send_str_list, send_integer

users = {}
message_log = []

'''
Addition of messages onto message log
'''
async def add_message_to_log(message):
    #get rid of oldest message, replace with newest
    if len(message_log) >= 10:
        message_log.pop(0)
    message_log.append(message)



async def accept_new_user(writer, reader):
    send_str(writer, "Enter a username:")
    await writer.drain()
    print("Sent string")
    username = await recv_str(reader)
    if username in users:
        send_str(writer, "Username is already taken.")
        writer.close()
        return
    writer.write(struct.pack("<i", 2))
    print("sending 2")
    await writer.drain()
    users[username] = writer

    await writer.drain()
    if len(message_log) > 0:
        send_integer(writer, len(message_log))
        for message in message_log:
            send_str_list(writer, message)
    else:
        send_integer(writer, 1)
        send_str_list(writer, ["00:00", "SERVER", "There are no recent messages."])
    await writer.drain()

async def recieve_and_send_message(writer, reader):
    username, message = await recv_str_list(reader)
    time = datetime.datetime.now().time()
    time = time.strftime("%H:%M:%S")
    message = [time, username, message]
    print(message[0] + ":" + message[1] + "~ " + message[2])
    await add_message_to_log(message)
    for name in list(users):
        try:
            print(name)
            send_str_list(users[name], message)
            await users[name].drain()
        except Exception:
            del users[name]

            
async def handle_request(reader, writer):
    print("Handling request")
    version = await recv_single_value(reader, "<i")
    if version != 1:
        print("Invalid version")
        writer.close()
    writer.write(struct.pack("<i", 1))
    await writer.drain()
    while True:
        action = await recv_single_value(reader, "<i")
        if action == 2:
            await accept_new_user(writer, reader)
        elif action == 3:
            await recieve_and_send_message(writer, reader)
            

async def chat_server():
    print("Server started")
    server = await asyncio.start_server(handle_request, '', 25565)
    async with server:
        await server.serve_forever()


asyncio.run(chat_server())