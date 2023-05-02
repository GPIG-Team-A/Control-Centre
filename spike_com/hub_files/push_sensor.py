"""
    A Push Sensor
"""
import hub

class PushSensor:

    def __init__(self, port):
        self.port = port
        self._device = getattr(hub.port, port).device
        self._device.mode([(0, 0), (1, 0), (4, 0)])
    
    def is_pushed(self):
        """
            Return whether the sensor is pushed
        """
        return self._device.get()[1] == 1
    
    