"""
    A Light Sensor
"""
import hub

class Colour:
    BLACK = 0
    RED = 9
    WHITE = 10

class LightSensor:

    def __init__(self, port):
        self.port = port
        self._device = getattr(hub.port, port).device
        self._device.mode([(1, 0), (0, 0), (5, 0), (5, 1), (5, 2)])
    
    def get_reflecton(self):
        """
            Get the light reflection
        """
        return self._device.get()[0]
    
    def get_colour(self):
        """
            Get the colour currently recorded
        """
        return self._device.get()[1]