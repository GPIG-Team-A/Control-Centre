"""
    Main module for running Spike-Com
"""
import subprocess
import os
import time
from threading import Thread
from spike_com.host_files.main import Handler

# CONSTANTS
MAC = "30:E2:83:03:7C:71"
REMOTE_DIRECTORY = "/spikecom"


class SpikeHandler:
    """
        Handles SpikeCom
    """

    def __init__(self):
        self.connected = False
        self.communication_handler = None

    def _bind(self):
        """
            Bind to port
        """
        try:
            if os.name != "nt":
                subprocess.run(["sudo", "rfcomm", "bind", "0", MAC], check=True)
        except subprocess.CalledProcessError as error:
            print("[Spike-Com] Error unable to bind: ", error)
            self.disconnect()

    def run_ampy_cmd(self, cmds, check=False, universal_newlines=False):
        return subprocess.run(self.get_ampy_args(cmds), check=check, universal_newlines=universal_newlines)

    def get_ampy_args(self, cmds):
        if os.name == "nt":
            arguments = ["ampy", "--port", "COM4"]
        else:
            arguments = ["sudo", "ampy", "--port", "/dev/rfcomm0"]

        for cmd in cmds:
            arguments.append(cmd)

        return arguments

    def check_ampy_cmd(self, cmds, universal_newlines=False):
        return subprocess.check_output(self.get_ampy_args(cmds), universal_newlines=universal_newlines)

    def connect(self, callback_function):
        """
            Attempt to connect to the Rover

            :returns boolean: Whether successful
        """

        def _connect():
            self.disconnect()
            # Attempt to make connection here
            self._bind()

            # Try to run the hub file
            try:
                self.run_ampy_cmd(["run", "-n", "spike_com/hub_files/main.py"], check=True)
            except subprocess.CalledProcessError as error:
                print("[Spike-Com] Error unable to bind: ", error)
                self.disconnect()
                callback_function(False)
                return

            time.sleep(5)

            # Now create our communication handler
            try:
                self.communication_handler = Handler()
                self.communication_handler.start()
            except Exception as error:  # pylint: disable=W0718
                print("[Spike-Com] Error unable to start communication: ", error)
                self.disconnect()
                callback_function(False)
                return
            if not self.communication_handler.connected:
                self.disconnect()
            else:
                self.connected = True
            callback_function(self.communication_handler.connected)

        thread = Thread(target=_connect)
        thread.start()

    def send_instructions(self, instructions):
        """
            Send instructions
        """

        def _send_instructions():
            self.communication_handler.send_instructions(instructions)

        thread = Thread(target=_send_instructions)
        thread.start()

    def get_log(self):
        """
            Get the logs off the Rover
        """
        self._bind()
        try:
            log = self.check_ampy_cmd(["get", f"{REMOTE_DIRECTORY}/log.txt"], universal_newlines=True)
        except subprocess.CalledProcessError:
            return False
        self.disconnect()
        return str(log)

    def update_rover_files(self):
        """
            Update the files on the rover
        """
        self._bind()
        # Send all hub files to the hub
        python_files = [x for x in os.listdir("spike_com/hub_files/") if
                        x.endswith(".py") and not x == "main.py"]
        # Create directory
        self.run_ampy_cmd(["mkdir", "--exists-okay", f"{REMOTE_DIRECTORY}"])
        for file in python_files:
            print(f"Uploading {file}")
            self.run_ampy_cmd(["rm", f"{REMOTE_DIRECTORY}/{file}"])
            time.sleep(1)
            self.run_ampy_cmd(["put", f"spike_com/hub_files/{file}", f"{REMOTE_DIRECTORY}/{file}"])
            time.sleep(1)
        print("Update complete")
        self.disconnect()

    def disconnect(self):
        """
            Disconnect from Hub
        """
        try:
            if os.name != "nt":
                subprocess.run(["sudo", "rfcomm", "release", "0"], check=True)
        except subprocess.CalledProcessError as error:
            print("[Spike-Com] Error unable to bind: ", error)
        print("[Spike-Com] Disconnected!")
