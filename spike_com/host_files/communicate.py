"""
    Module to handle the raw bluetooth communication
    to a Spike
"""
import os
import socket
import time
import threading
import serial
from spike_com.host_files.protocol import Packet, class_by_code

class CommunicationHandler:
    """
        Represents a Bluetooth connection to a Spike
    """

    def __init__(self):
        """
            Create a Bluetooth connection handler
        """
        self.listeners = {}

        if os.name == "nt":
            self.socket = serial.Serial("COM4", timeout=1)
        else:
            self.socket = serial.Serial("/dev/rfcomm0", timeout=1)

        self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self.lock = threading.Lock()

    def start(self):
        """
            Start the service
        """
        self.socket.flush()
        self.recv_thread.start()

    def send(self, packet):
        """
            Send a command over to the hub with the given data

            Args:
                packet (Packet): Data to send
        """
        assert isinstance(packet, Packet)

        with self.lock:
            payload = packet.pack()
            payload = payload.replace(b"\x03", b"\x7e\x7e")

            try:
                self.socket.write(payload)
            except BufferError as error:
                print(f"Error occured whilst sending: {error}")

            print(f"Sent {len(payload)} bytes of data")

    def add_listener(self, packet_type, function):
        """
            Add a listener for a given packet type with the given function

            Args:
                packet_type (class): The packet type to listen for
                function (func): The function to execute with the data parameter
        """
        self.listeners[packet_type.CODE] = function

    def _recv_raw(self):
        with self.lock:
            try:
                raw = self.socket.read_until()
            except serial.SerialException:
                raw = None
        return raw

    def _recv_loop(self):
        """
            The receive loop that handles listeners
        """
        while True:
            raw = self._recv_raw()
            if raw:
                code = Packet.get_code(raw)
                if code in self.listeners:
                    unpacked = class_by_code(code).unpack(raw)
                    self.listeners[code](self, unpacked)

            time.sleep(1)
