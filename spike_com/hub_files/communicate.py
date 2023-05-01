"""
    Module to handle the raw bluetooth communication
    to a Spike
"""
import hub
import uasyncio as asyncio # Called uasyncio in micropython
from log import log
from protocol import *

class CommunicationHandler:
    """
        Represents a Bluetooth connection to a Spike
    """

    def __init__(self):
        """
            Create a Bluetooth connection handler

            Args:
                use_test_file_pipe (Bool): Whether to use a file pipe instead of BT
                                                for testing purposes (default: False)
        """
        self.listeners = {}

    async def start(self):
        """
            Start the service
        """
        await self._recv_loop()
    
    def send(self, packet):
        """
            Send a command over to the hub with the given data

            Args:
                packet (Packet): Packet to send
        """
        hub.BT_VCP().write(packet.pack())
    
    def add_listener(self, packet_type, function):
        """
            Add a listener for a given packet type with the given function

            Args:
                packet_type (class): The packet type to listen for
                function (func): The function to execute with the data parameter
        """
        self.listeners[packet_type.CODE] = function
    
    def _recv_raw(self):
        """
            Receive bytes over communication link
        """
        try:
            raw = hub.BT_VCP().read()
        except:
            return None
        return raw

    async def _recv_loop(self):
        """
            The receive loop that handles listeners
        """
        while True:
            raw = self._recv_raw()
            if not raw:
                await asyncio.sleep(1)
                continue
            
            # Deal with the Hub killcode
            raw = raw.replace(b"\x7e\x7e",b"\x03")
            
            # Grab the code of this packet
            try:
                code = Packet.get_code(raw)
            except:
                await asyncio.sleep(1)
                continue

            log("Received code: " + str(code))

            if code in self.listeners.keys():
                unpacked = class_by_code(code).unpack(raw)
                asyncio.create_task(self.listeners[code](self, unpacked))
