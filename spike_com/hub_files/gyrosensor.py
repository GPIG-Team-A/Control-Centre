"""
    Module for the GyroSensor
"""
import hub

class GyroSensor:
    """
        Represents the GyroSensor on the Hub

        Attributes:
            gyroscope: Unknown
            accelerometer: Values of accelerometer across axis (order unknown)
            yaw_pitch_roll: List of yaw, pitch, roll
            position: Unknown
    """

    def __init__(self):
        """
            Creates an object of the GyroSensor
        """
        pass
    
    def get_yaw(self):
        return hub.motion.yaw_pitch_roll()[0]
    
    def get_pitch(self):
        return hub.motion.yaw_pitch_roll()[1]

    def get_roll(self):
        return hub.motion.yaw_pitch_roll()[2]
