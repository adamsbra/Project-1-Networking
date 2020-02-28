import asyncio
import struct



async def recv_formatted_data(reader, frmt):
    """
    Receives struct-formatted data from the given socket according to the struct format given and
    returns a tuple of values.
    """
    data = struct.unpack(frmt, await reader.read(struct.calcsize(frmt)))
    return data


async def recv_single_value(reader, frmt):
    """
    Receives a single value from the given socket according to the struct format given and returns
    it.
    """
    return (await recv_formatted_data(reader, frmt))[0]


async def recv_str(reader):
    """
    Receives a string using the socket. The string must be prefixed with its length and encoded.
    """
    length = await recv_single_value(reader, "<i")
    data = await reader.read(length)
    string = data.decode()
    return string


async def recv_str_list(reader):
    """
    Receives a list of strings from the socket. The list is prefixed with the length and each string
    is prefixed with recv_str().
    """
    str_list = []
    length = await recv_single_value(reader, "<i")
    for i in range(length):
        str_list.append(await recv_str(reader))
    return str_list


def send_str(writer, string):
    """
    Sends a string using the socket. The string is encoded then prefixed with the length as a 4-byte
    integer.
    """
    string = string.encode()
    data = struct.pack('<i', len(string))
    data += string
    writer.write(data)


def send_str_list(writer, strings):
    """
    Sends a list of strings using the socket. The list is prefixed with its length as a 4-byte
    integer. Each string is send with send_str().
    """
    data = struct.pack('<i', len(strings))
    writer.write(data)
    for string in strings:
        send_str(writer, string)

def send_integer(writer, i):
    writer.write(struct.pack("<i", i))