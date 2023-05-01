"""
    Main module for running Spike-Com
"""
import argparse
import sys
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
            subprocess.run(["sudo", "rfcomm", "bind", "0", MAC], check=True)
        except subprocess.CalledProcessError as error:
            print("[Spike-Com] Error unable to bind: ", error)
            self.disconnect()
    
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
                subprocess.run(["sudo", "ampy", "--port", "/dev/rfcomm0", "run", "-n",
                                "spike_com/hub_files/main.py"], check=True)
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
            except Exception as error: # pylint: disable=W0718
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
        try:
            log = subprocess.check_output(["sudo", "ampy", "--port", "/dev/rfcomm0", "get",
                            f"{REMOTE_DIRECTORY}/log.txt"], universal_newlines=True)
        except subprocess.CalledProcessError:
            return False
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
        subprocess.run(["sudo", "ampy", "--port", "/dev/rfcomm0", "mkdir",
                        "--exists-okay", f"{REMOTE_DIRECTORY}"], check=False)
        for file in python_files:
            print(f"Uploading {file}")
            subprocess.run(["sudo", "ampy", "--port", "/dev/rfcomm0", "rm",
                            f"{REMOTE_DIRECTORY}/{file}"], check=False)
            time.sleep(1)
            subprocess.run(["sudo", "ampy", "--port", "/dev/rfcomm0",
                "put", f"spike_com/hub_files/{file}", f"{REMOTE_DIRECTORY}/{file}"],
                check=False)
            time.sleep(1)
        print("Update complete")

    def disconnect(self):
        """
            Disconnect from Hub
        """
        try:
            subprocess.run(["sudo", "rfcomm", "release", "0"], check=True)
        except subprocess.CalledProcessError as error:
            print("[Spike-Com] Error unable to bind: ", error)
        print("[Spike-Com] Disconnected!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        usage = "%(prog)s [OPTION] [COMMAND]",
        description = "Execute a remote spike program"
    )
    parser.add_argument(
        "-v",
        action = "version",
        version = f"{parser.prog} version 1.0"
    )
    parser.add_argument(
        "command",
        choices = ["run", "update", "debug", "log"]
    )

    args, host_args = parser.parse_known_args()

    # Setup connection
    print("Connecting... ", end="")
    try:
        subprocess.run(["sudo", "rfcomm", "bind", "0", MAC], check=True)
    except subprocess.CalledProcessError as e:
        print("Error unable to bind: ", e)
        sys.exit(-1)
    else:
        print("Connected!")

    if args.command == "run":
        # Send file to spike
        print("Running remote program on Spike... ", end="")
        try:
            subprocess.run(["sudo", "ampy", "--port", "/dev/rfcomm0", "run", "-n",
                            "hub_files/main.py"], check=True)
        except subprocess.CalledProcessError as e:
            print("Error unable to bind: ", e)
            sys.exit(-1)
        else:
            print("Finished.")

        time.sleep(5)

        print("Running host file...")
        try:
            sys.path.append("host_files/")
            import main
            main.main(host_args)
        except ImportError as e:
            print(f"Error! {e}")
            sys.exit(-1)
        else:
            print("Done!")
    elif args.command == "debug":
        print("Running remote program on Spike with traceback...")
        try:
            subprocess.run(["sudo", "ampy", "--port", "/dev/rfcomm0", "run",
                            "hub_files/main.py"], check=True)
        except subprocess.CalledProcessError as e:
            print("Error unable to bind: ", e)
            sys.exit(-1)
        else:
            print("Finished.")
    elif args.command == "log":
        print("Retrieving log file...")
        try:
            subprocess.run(["sudo", "ampy", "--port", "/dev/rfcomm0", "get",
                            f"{REMOTE_DIRECTORY}/log.txt"], check=True)
        except subprocess.CalledProcessError as e:
            print("Error unable to bind: ", e)
            sys.exit(-1)
        else:
            print("Finished.")
    elif args.command == "update":
        # Send all hub files to the hub
        python_files = [x for x in os.listdir("hub_files/") if
                        x.endswith(".py") and not x == "main.py"]
        # Create directory
        subprocess.run(["sudo", "ampy", "--port", "/dev/rfcomm0", "mkdir",
                        "--exists-okay", f"{REMOTE_DIRECTORY}"], check=False)
        for file in python_files:
            print(f"Uploading {file}")
            subprocess.run(["sudo", "ampy", "--port", "/dev/rfcomm0", "rm",
                            f"{REMOTE_DIRECTORY}/{file}"], check=False)
            time.sleep(1)
            subprocess.run(["sudo", "ampy", "--port", "/dev/rfcomm0",
                            "put", f"hub_files/{file}", f"{REMOTE_DIRECTORY}/{file}"], check=False)
            time.sleep(1)
        print("Update complete")

    # Disconnect
    print("Disconnecting from Spike... ", end="")
    try:
        subprocess.run(["sudo", "rfcomm", "release", "0"], check=True)
    except subprocess.CalledProcessError as e:
        print("Error unable to bind: ", e)
        sys.exit(-1)
    else:
        print("Disconnected!")
