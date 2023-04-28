import time
import hub
from log import log

class Sensor:
    def __init__(self, port):
        self.port = port
        assert self.port in ['A', 'B', 'C', 'D', 'E', 'F']
        self._sensor = getattr(hub.port, port).device


class Ultrasonic(Sensor):
    def __init__(self, port):
        super().__init__(port)

    def set_leds(self, top_left, top_right, bottom_left, bottom_right):
        self._sensor.mode(5, bytes([top_left, top_right, bottom_left, bottom_right]))

    def get_distance(self):
        distance = self._sensor.get()[0]
        if distance:
            return int(distance)
        else:
            return 9999
