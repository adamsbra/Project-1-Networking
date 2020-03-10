import asyncio
import socket
import datetime

PORT = 25555


def get_ip():
    """Gets the local IP of the current machine."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            # random IP address, doesn't have to be reachable
            s.connect(('10.255.255.255', 1))
            # get the outgoing IP address on the machine
            return s.getsockname()[0]
        except Exception:
            return '127.0.0.1'


class ChatProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        """
        Constructor for Datagram Protocol, added message log and username for utility purposes.
        """
        self.message_log = []
        self.username = ""
        self.on_con_lost = asyncio.get_running_loop().create_future()

    def format_message(self, op_code, message):
        """
        Encodes a message with an operation code appended to the front.
        """
        full_message = str(op_code) + message
        full_message = full_message.encode()
        return full_message

    def unpack_message(self, full_message):
        """
        Decodes the string and returns a tuple of operation code and message.
        """
        full_message = full_message.decode()
        op_code = int(full_message[0])
        message = full_message[1:]
        return (op_code, message)

    def instantiate_message_log(self, message):
        """
        Only accepts the first message_log to be recieved,
        instantiates the message log and prints the messages
        in it for the first time.
        """
        if len(self.message_log) == 0:
            self.message_log = message.split("`")
            print(self.message_log)
            # This may cause the program to print out multiple logs when there
            # are multiple people sending messages.
            for msg in self.message_log:
                print(msg)

    def prepare_message_log(self):
        """
        Prepares the string needed to send the message log
        to a client
        """
        message_log_string = "2"
        # Using an increment here to prevent us from adding a character to the
        # end of the string, causing an empty string to be produced when we
        # split later on.
        i = 0
        print(self.message_log)
        for msg in self.message_log:
            if i != len(self.message_log) - 1:
                message_log_string += msg + "`"
            else:
                message_log_string += msg
            i += 1
        return message_log_string

    def recieve_message(self, message):
        time = datetime.datetime.now().time()
        time = time.strftime("%H:%M:%S")
        full_message = time + " ~ " + message
        if len(self.message_log) >= 10:
            self.message_log.pop(0)
        self.message_log.append(full_message)
        print(time + " ~ " + message)

    def connection_made(self, transport):
        """
        Method called when the connection is initially made.
        """
        self.transport = transport
        # Starts getting messages as a task in the asyncio loop
        asyncio.create_task(self.get_messages())

    def connection_lost(self, exc):
        """
        Method called whenever the transport is closed.
        """
        self.on_con_lost.set_result(True)

    async def get_messages(self):
        """
        Loop forever getting new inputs from the user and then broadcasting
        them. If the input is the empty string (i.e. just an enter)
        then it stops the program.
        """
        loop = asyncio.get_running_loop()
        print("Enter a name: ")
        name = await loop.run_in_executor(None, input)
        # Prefixed with a 1 to indicate that we are confirming a username.
        message = ("1" + name).encode()
        self.transport.sendto(message, ('255.255.255.255', PORT))
        # Attempt to set it no matter what, if username is invalid we will be
        # sent a 9 and disconnect.
        self.username = name
        while True:
            # Get the message from the user
            message = await loop.run_in_executor(None, input)
            if not message:
                self.transport.close()
                break
            # Broadcast the message by prefixing the string with a 3 and
            # sending the username along with the message.
            full_message = ("3" + self.username + "~" + message).encode()
            self.transport.sendto(full_message, ('255.255.255.255', PORT))

    def datagram_received(self, data, addr):
        """
        Method called whenever a datagram is recieved.
        """
        # Decode recieved data into op code and message.
        op_code, message = self.unpack_message(data)
        # Check to see if the recieved data is from the client itself
        if addr[0] != get_ip():
            # Close the connection
            if op_code == 9:
                self.transport.abort()
                self.transport.close()
            # First Connection
            if op_code == 1:
                if self.username == message:
                    self.transport.sendto(("9" + "quit").encode(), addr)
                else:
                    self.transport.sendto(self.prepare_message_log().encode(), addr)
            # Recieving the message log.
            elif op_code == 2:
                self.instantiate_message_log(message)
            # Recieving a message.
            elif op_code == 3:
                self.recieve_message(message)
        # Adding the client's own message to the output and log.
        elif addr[0] == get_ip() and op_code == 3:
            self.recieve_message(message)

    def error_received(self, exc):
        """
        Method called whenever there is an error
        with the underlying communication.
        """
        print('Error received:', exc)


async def main():
    # Setup the socket we will be using - enable broadcase and recieve message
    # on the given port. Normally, this wouldn't be necessary, but with
    # broadcasting it is needed.
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
    sock.bind(('', PORT))
    
    # Create the transport and protocol with our pre-made socket
    # If not provided, you would instead use local_addr=(...) and/or
    # remote_addr=(...)
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(ChatProtocol, sock=sock)

    # Wait for the connection to be closed/lost
    try:
        await protocol.on_con_lost
    finally:
        transport.close()

print("Your IP is", get_ip())
asyncio.run(main())
