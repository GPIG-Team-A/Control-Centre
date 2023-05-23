"""
"""

class MotorPair:

    def __init__(self, A, B):
        self.A = A
        self.B = B
        self.pair = A._motor.pair(B._motor)
    
    def start(self, a_speed=100, b_speed=100):
        if self.A.inverted:
            a_speed = -a_speed
        if self.B.inverted:
            b_speed = -b_speed
        self.pair.run_at_speed(a_speed, b_speed)
    
    def run_for_degrees(self, degrees, speed=100):
        if isinstance(speed, tuple):
            a_speed = speed[0]
            b_speed = speed[1]
        else:
            a_speed = speed
            b_speed = speed
        if self.A.inverted:
            a_speed *= -1
        if self.B.inverted:
            b_speed *= -1
        self.pair.run_for_degrees(degrees, a_speed, b_speed)
    
    def stop(self):
        self.pair.brake()