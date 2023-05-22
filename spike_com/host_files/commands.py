"""
    Commands
"""
import math
import clrprint
from spike_com.host_files.protocol import MoveInstruction, RotateInstruction, MiningInstruction

static = {"WHEEL_RADIUS": 4.3, "R": 11/8.7}#6.25/4.3}
var = {"speed": 35}

def move(distance):
    """
    
    :param distance: 
    """
    if isinstance(distance, list):
        distance = distance[0]
    rot = math.degrees(distance / static["WHEEL_RADIUS"])
    return MoveInstruction(
        left_motor_degrees=rot,
        left_motor_speed=var["speed"],
        right_motor_degrees=rot,
        right_motor_speed=var["speed"]
    )

def rotate(deg_clockwise):
    """

    :param deg_clockwise: 
    """
    if isinstance(deg_clockwise, list):
        deg_clockwise = deg_clockwise[0]

    return RotateInstruction(
        deg_clockwise, 20, static["R"]
    )

def mine():
    """
        Mine command
    """
    return MiningInstruction(time=0)

def set_variable(args):
    """
    
    :param args: 
    """
    try:
        var[args[0]] = args[1]
    except IndexError:
        clrprint.clrprint(f"unable to set variable {args[0]} to value {args[1]}", clr='r')
