"""Simple P controller to keep the person tracked within the camera's field and at a constant distance from the robot"""


class P:
    def __init__(self, setpoint, parameters, boundary):
        self.setpoint = setpoint
        self.error = 0

        self.kp = parameters

        self.min_boundary, self.max_boundary = boundary

    def compute(self, pos) -> float:
        """Funtion to compute the output of the P controller, given the current
        position 'pos'. In our case pos represent the current coordinates of the middlepoint of tracked person
        """
        setpoint = self.setpoint

        self.error = setpoint - pos

        correction = max(
            self.min_boundary, min(self.max_boundary, self.kp * self.error)
        )
        return correction
