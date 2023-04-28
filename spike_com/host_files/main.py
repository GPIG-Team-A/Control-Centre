"""
    Entry-Point of the Spike Host
"""
import json
import time
from protocol import Directions, Ping, DistanceSend
from commands import move, rotate, set_variable
import clrprint
from communicate import CommunicationHandler

MAC = "30:E2:83:03:7C:71"

class Handler:
    """
        Establishes and handles communication with the Rover
    """

    def __init__(self):
        """
            Constuctor
        """
        self.communication_handler = None
        self.connected = False

    def on_ping(self, _):
        """
            Called when ping is received
        """
        print("pong")
        self.connected = True

    def on_distance_received(self, _, distance_send):
        """
            Called when distance is received
        """
        print("Received distance reading:", distance_send.reading)

    def command_line(self, handler):
        """
            Called to create an interactive command line to the rover
        """

        # format: name : [function name, arguments expected]
        commands = {"go": [move, 1],
            "turn": [rotate, 1],
            #"get": [Commands.get, 0],
            "set": [set_variable, 2]
        }

        instructions = Directions()
        while True:
            command = input(">>> ")
            args = command.split(" ")
            cmd = args[0]
            args = args[1:]
            if cmd == "send":
                print("Sending instructions...")
                handler.send(instructions)
                print("Sent!")
                instructions = Directions()
            elif cmd == "ping":
                handler.send(Ping())
            elif cmd == "quit":
                break
            elif cmd in commands:
                comtr = commands[cmd]
                arg_count = comtr[1]
                if len(args) == arg_count:
                    instructions.add_instruction(comtr[0](args))
                    clrprint.clrprint(f"added {cmd} instruction", clr = 'g')

    def start(self):
        """
            Begin connection to the Rover
        """
        self.communication_handler = CommunicationHandler()
        self.communication_handler.add_listener(Ping, self.on_ping)
        self.communication_handler.add_listener(DistanceSend, self.on_distance_received)
        self.communication_handler.start()

        # Ping first to check working
        time.sleep(10)
        print("Checking connection...")

        self.connected = False
        print("ping...")
        self.communication_handler.send(Ping())
        while not self.connected:
            time.sleep(1)
        print("Connection is established.")
        return self.communication_handler

def get_from_json(file_name, verbose, handler):
    """
        Get commands from a JSON file
    """
    commands = {"MOVE": [move, 1],
                "ROTATE": [rotate, 1],
                #"GET": [Commands.get, 0]
                }
    instructions = Directions()
    with open(file_name, encoding="utf-8") as file:
        d = json.load(file)
        for item in d:
            if item["type"] in commands:
                command = commands[item["type"]]
                if command[1] == 1:
                    instructions.add_instruction(command[0]([item["value"]]))
                elif command[1] == 0:
                    instructions.add_instruction(command[0]([]))
                else:
                    clrprint.clrprint(
                        f"unable to add instruction {item['type']} due to unknown or \
                            invalid number of values needed",
                            clr='red')
                if verbose:
                    clrprint.clrprint(f"added instruction {item['type']} with \
                                      value {item['value']}", clr='green')
                    if item["value"] % 1 != 0:
                        clrprint.clrprint("WARNING: value given is a \
                                          decimal value -> accuracy loss likely", clr='y')

    handler.send(instructions)

def main(args):
    """
        Main function called when communication begins
    """
    handler = Handler()
    communication_handler = handler.start()

    get_from_json(file_name=args[0], verbose=True, handler=communication_handler)
