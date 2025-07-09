"""Simple PID controller to keep the person tracked within the camera's field"""


class PID:
    def __init__(self, setpoint, parameters, boundary):
        self.setpoint = setpoint  # (x,y)
        self.prev_error = 0
        self.integral_error = 0
        self.derivative_error = 0
        self.error = 0

        # self.kp = 1
        # self.ki = 0.01 #0 is the best
        # self.kd = 0

        self.kp, self.ki, self.kd = parameters
        self.time_step = 1  # frame

        self.min_boundary, self.max_boundary = boundary

    def compute(self, pos) -> float:
        """Funtion to compute the output of the PID controller, given the current
        position 'pos'. In our case pos represent the current coordinates of the middlepoint of tracked person
        """
        # if self.integral_error_x > 3 :
        #    self.integral_error_x = 0
        # if self.integral_error_y > 3:
        #    self.integral_error_y = 0
        setpoint = self.setpoint

        self.error = setpoint - pos
        self.error = setpoint - pos

        self.integral_error = self.integral_error + self.error * self.time_step
        self.derivative_error = (self.error - self.prev_error) * self.time_step
        self.prev_error = self.error

        correction = max(
            self.min_boundary,
            min(
                self.max_boundary,
                self.kp * self.error
                + self.ki * self.integral_error
                + self.kd * self.derivative_error,
            ),
        )
        return correction
