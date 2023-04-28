"""
    Example main.py
"""
import os
import hub
import time
import uasyncio as asyncio
import sys
os.chdir("/spikecom/")
sys.path.insert(1, "/spikecom/") # Required to get into correct working directory
                                 # cannot find a nice way to auto this

from communicate import CommunicationHandler
from protocol import *
from motor import Motor
from motor_pair import MotorPair
from sensor import Ultrasonic
from gyrosensor import GyroSensor
import log

LEFT_WHEEL = Motor("A")
RIGHT_WHEEL = Motor("B", inverted=True)
WHEEL_PAIR = MotorPair(LEFT_WHEEL, RIGHT_WHEEL)
DISTANCE_SENSOR = Ultrasonic("E")
GYROSENSOR = GyroSensor()
CORRECTION_SYSTEM_ENABLED = False


async def on_ping(handler, data):
    handler.send(Ping())
    log.log("Received ping!")

async def on_get_distance(handler, data):
    log.log("on_get_distance")
    try:
        handler.send(DistanceSend(DISTANCE_SENSOR.get_distance()))
    except Exception as e:
        log.log("get_distance failed, " + str(e))

def do_safe_move(instruction):
    # Get the directional yaw
    directional_yaw = GYROSENSOR.get_yaw()
    # Get current motor rotations
    left_wheel_starting_rotation = LEFT_WHEEL.get_rotation()
    right_wheel_starting_rotation = RIGHT_WHEEL.get_rotation()

    # Start the Motors

    #for i in range(20):
    WHEEL_PAIR.run_for_degrees(
        instruction.left_motor_degrees,
        speed=20
    )
    #   time.sleep(0.1)

    """
    LEFT_WHEEL.run_for_degrees(
        instruction.left_motor_degrees, 
        speed=20
    )
    RIGHT_WHEEL.run_for_degrees(
        instruction.right_motor_degrees, 
        speed=20
    )
    """
    time.sleep(0.1) # Allow time for the motors to start

    # Monitoring
    recorded_yaws = []
    recorded_power = []
    recorded_rotations = []
    tolerance = 2 # Amount of tolerance
    while LEFT_WHEEL.is_running() or RIGHT_WHEEL.is_running():
        current_yaw = GYROSENSOR.get_yaw()
        recorded_yaws.append(current_yaw)
        recorded_power.append((LEFT_WHEEL.get_current_power(), RIGHT_WHEEL.get_current_power()))
        recorded_rotations.append((LEFT_WHEEL.get_rotation(), RIGHT_WHEEL.get_rotation()))

        if CORRECTION_SYSTEM_ENABLED and abs(current_yaw - directional_yaw) > tolerance:
            log.log("Incorrect yaw detected... correcting")
            WHEEL_PAIR.stop()
            hub.display.show("1")

            # Perform rotation until we get to correct yaw
            sign = lambda x: (-1, 1)[x<0]
            while abs(current_yaw - directional_yaw) > 0:
                # Which way are we incorrect?
                dir = sign(current_yaw - directional_yaw)
                # dir=1 means we turn left, dir=-1 means we turn right
                if dir == 1:
                    WHEEL_PAIR.start(1, 0)
                else:
                    WHEEL_PAIR.start(0, 1)
                time.sleep(0.1)
                current_yaw = GYROSENSOR.get_yaw()
            WHEEL_PAIR.stop()
            hub.display.show("2")
            time.sleep(3)


            # Begin instruction again
            left_wheel_moved_by = abs(LEFT_WHEEL.get_rotation() - left_wheel_starting_rotation)
            right_wheel_moved_by = abs(RIGHT_WHEEL.get_rotation() - right_wheel_starting_rotation)


            if left_wheel_moved_by > instruction.left_motor_degrees or right_wheel_moved_by > instruction.right_motor_degrees:
                break

            new_instruction = MoveInstruction(
                left_motor_degrees=instruction.left_motor_degrees - left_wheel_moved_by,
                left_motor_speed=20,
                right_motor_degrees=instruction.right_motor_degrees - right_wheel_moved_by,
                right_motor_speed=20
            )

            for i in range(20):
                WHEEL_PAIR.run_for_degrees(
                    new_instruction.left_motor_degrees,
                    speed=i
                )
                time.sleep(0.1)

            """
            LEFT_WHEEL.run_for_degrees(
                new_instruction.left_motor_degrees, 
                speed=new_instruction.left_motor_speed
            )
            RIGHT_WHEEL.run_for_degrees(
                new_instruction.right_motor_degrees, 
                speed=new_instruction.right_motor_speed
            )
            """
            time.sleep(0.1)
        time.sleep(0.1)

    yaw_differences = [abs(x - directional_yaw) for x in recorded_yaws]
    average_difference = sum(yaw_differences) / len(yaw_differences)

    # Calculating RPMs from rotations
    calculated_rotation_offsets = []
    calculated_rotation_offsets.append((recorded_rotations[0][0] - left_wheel_starting_rotation, recorded_rotations[0][1] - right_wheel_starting_rotation))
    for i in range(1, len(recorded_rotations) - 1):
        calculated_rotation_offsets.append(
            (abs(recorded_rotations[i][0] - recorded_rotations[i-1][0]), 
            abs(recorded_rotations[i][1] - recorded_rotations[i-1][1]))
        )
    # Time between rotation changes is 0.1, we can calculate REAL RPM from this
    calculated_rpm = []
    for offsets in calculated_rotation_offsets:
        calculated_rpm.append(
            ((offsets[0] / 360) * 600, (offsets[1] / 360) * 600))

    log.log("#######SAFE MOVE DIGEST########")
    log.log("Starting Yaw: " + str(directional_yaw))
    log.log("Ending Yaw: " + str(recorded_yaws[-1]))
    log.log("Recorded Yaws: " + str(recorded_yaws))
    log.log("Yaw Differences: " + str(yaw_differences))
    log.log("Average Difference: " + str(average_difference))
    log.log("Power Values: " + str(recorded_power))
    log.log("RPM Values:" + str(calculated_rpm))
    log.log("Move Time:" + str(len(recorded_power) / 10))
    log.log("#######SAFE MOVE DIGEST########")


async def on_new_directions(handler, directions):
    for instruction in directions.instructions:
        hub.sound.beep(1000)
        if isinstance(instruction, MoveInstruction):
            log.log("MoveInstruction")
            try:
                do_safe_move(instruction)
            except Exception as e:
                log.log(str(e))
            log.log("Finished move instruction")
        elif isinstance(instruction, DistanceInstruction):
            log.log("DistanceInstruction")
            await on_get_distance(handler, None)
            log.log("Finished DistanceInstruction")
        time.sleep(5)

async def main():
    # Reset log
    log.reset()
    handler = CommunicationHandler()
    handler.add_listener(Ping, on_ping)
    handler.add_listener(Directions, on_new_directions)
    handler.add_listener(DistanceInstruction, on_get_distance)
    await handler.start()


if __name__ == "__main__":
    asyncio.run(main())