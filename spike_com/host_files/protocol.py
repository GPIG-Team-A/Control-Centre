"""
    Details key classes for the communication protocol
"""
import struct

class Packet:
    """
        Represents a packet to be sent to the Spike
    """

    def __init__(self, code):
        self.code = code

    def _encapsulate(self, payload):
        return struct.pack("!b", self.code) + payload

    def pack(self):
        """ Requires overwrite """
        return b''

    @staticmethod
    def decapsulate(data):
        """
            Decapsulate the packet into just the payload
        """
        return data[1:]

    @staticmethod
    def get_code(data):
        """
            Get the code of this packet
        """
        code, = struct.unpack("!b", data[:1])
        return code

class Ping(Packet):
    """ A simple Ping packet """
    CODE = 0

    def __init__(self):
        super().__init__(self.CODE)

    def pack(self):
        return self._encapsulate(b'')

    @staticmethod
    def unpack(_):
        """
            Unpack the Ping Packet
        """
        return Ping()

class DistanceInstruction(Packet):
    """
        A distance request instruction to the Spike
    """

    CODE = 2

    def __init__(self):
        super().__init__(self.CODE)

    def pack(self):
        return self._encapsulate(b'')

    @staticmethod
    def unpack(_):
        """
            Unpack the DistanceInstruction Packet
        """
        return DistanceInstruction()

class DistanceSend(Packet):
    """
        A distance response from the Spike
    """

    CODE = 3

    def __init__(self, reading):
        super().__init__(self.CODE)
        self.reading = reading

    def pack(self):
        payload = struct.pack("!H",
                              self.reading)
        return self._encapsulate(payload)

    @staticmethod
    def unpack(data):
        """
            Unpack the DistanceSend Packet
        """
        print(data)
        payload = Packet.decapsulate(data)
        print(len(payload))
        print(payload)
        reading = struct.unpack("!H", payload)
        return DistanceSend(reading)

class MoveInstruction(Packet):
    """
        A movement instruction to the Spike
    """
    CODE = 1

    def __init__(self, left_motor_degrees=360, left_motor_speed=100,
                right_motor_degrees=360, right_motor_speed=100):
        super().__init__(self.CODE)
        self.left_motor_speed = int(left_motor_speed) * (-1 if left_motor_degrees < 0 else 1)
        self.left_motor_degrees = abs(int(left_motor_degrees))
        self.right_motor_speed = int(right_motor_speed) * (-1 if right_motor_degrees < 0 else 1)
        self.right_motor_degrees = abs(int(right_motor_degrees))


    def pack(self):
        payload = struct.pack("!hhhh",
            self.left_motor_degrees,
            self.left_motor_speed,
            self.right_motor_degrees,
            self.right_motor_speed)
        return self._encapsulate(payload)

    @staticmethod
    def unpack(data):
        """
            Unpack the MoveInstruction Packet
        """
        payload = Packet.decapsulate(data)
        left_motor_degrees, left_motor_speed, right_motor_degrees,\
              right_motor_speed = struct.unpack("!hhhh", payload)
        return MoveInstruction(
            left_motor_degrees=left_motor_degrees,
            left_motor_speed=left_motor_speed,
            right_motor_degrees=right_motor_degrees,
            right_motor_speed=right_motor_speed
        )

class RotateInstruction(Packet):
    """
        An instruction to rotate the Rover by a certain number of degrees
    """
    CODE = 5

    def __init__(self, spin_rotation, motor_speed):
        """
        Create spin instruction

        Args:
            spin_rotation (int): angle turn of rover in degrees
            motor_speed (int): speed of motor
        """
        super().__init__(self.CODE)
        self.spin_roation = int(spin_rotation)
        self.motor_speed = motor_speed
    
    def pack(self):
        payload = struct.pack("!hh", self.spin_roation, self.motor_speed)
        return self._encapsulate(payload)

    @staticmethod
    def unpack(data):
        payload = Packet.decapsulate(data)
        spin_rotation, motor_speed = struct.unpack("!hh", payload)
        return RotateInstruction(spin_rotation, motor_speed)


class MiningInstruction(Packet):
    """
        Represents an instruction to mine a rock
    """

    CODE = 4

    def __init__(self, time=5):
        """
            Create an instruction to mine a rock

            :param time: Amount of time to mine rock for
        """
        super().__init__(self.CODE)
        self.time = time
    
    def pack(self):
        """
            Pack the instruction to binary
        """
        payload = struct.pack("!h", self.time)
        return self._encapsulate(payload)

    @staticmethod
    def unpack(data):
        """
            Unpack the instruction
        """
        payload = Packet.decapsulate(data)
        time, = struct.unpack("!h", payload)
        return MiningInstruction(time=time)

    

class SyncInstruction(Packet):
    """
        A sync instruction
    """

    def __init__(self):
        super().__init__("sync")

    @staticmethod
    def unpack(_):
        """
            Unpack the SynInstruction packet
        """
        return SyncInstruction()

class Directions(Packet):
    """
        Represents a Direction list to the Spike
        The intention is that the spike will follow these instructions
    """
    CODE = 100

    def __init__(self, instructions=None, timeout=1000):
        super().__init__(self.CODE)
        if instructions is None:
            self.instructions = []
        else:
            self.instructions = instructions
        self.timeout = timeout

    def add_instruction(self, instruction):
        """
            Add an instruction to the list of instructions
        """
        self.instructions.append(instruction)

    def pack(self):
        """
            Pack and return a dictionary payload for use
                in a BT transmission
        """
        # Pack all of the instructions
        payload = bytearray()
        # Append the number of instructions
        payload += struct.pack("!B", len(self.instructions))
        # Now append all the packed instructions
        for instruction in self.instructions:
            packed_instruction = instruction.pack()
            # Prepend with size of the instruction
            payload += struct.pack("!B", len(packed_instruction))
            # Append the instruction
            payload += packed_instruction
        return self._encapsulate(bytes(payload))

    @staticmethod
    def unpack(data):
        """
            Unpack some given data into a Directions object
        """
        # Get decaspulated payload
        payload = Packet.decapsulate(data)
        # Read the number of instructions this contained
        no_instructions, = struct.unpack("!B", payload[:1])
        # Create a new Directions object
        directions = Directions()
        current_index = 1
        for _ in range(no_instructions):
            # Read the ith instruction
            # Read the size of the instruction
            instruction_size, = struct.unpack("!B", payload[current_index:current_index+1])
            current_index += 1
            # Now read the actual instruction
            packed_instruction, = struct.unpack("!" + str(instruction_size) + "s",
                payload[current_index:current_index + instruction_size])
            current_index += instruction_size
            # Now get the code of this instruction
            code = Packet.get_code(packed_instruction)
            print("Found code " + str(code))
            if code == MoveInstruction.CODE:
                directions.add_instruction(MoveInstruction.unpack(packed_instruction))
            elif code == DistanceInstruction.CODE:
                directions.add_instruction(DistanceInstruction())
            elif code == MiningInstruction.CODE:
                directions.add_instruction(MiningInstruction.unpack(packed_instruction))
            elif code == RotateInstruction.CODE:
                directions.add_instruction(RotateInstruction.unpack(packed_instruction))
        return directions

CODES = {
    0: Ping,
    1: MoveInstruction,
    2: DistanceInstruction,
    3: DistanceSend,
    4: MiningInstruction,
    5: RotateInstruction,
    100: Directions,
}

def class_by_code(code):
    """
        Get class by the code
    """
    return CODES[code]
