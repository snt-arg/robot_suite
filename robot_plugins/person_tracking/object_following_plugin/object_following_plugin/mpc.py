"""
Model function
Cost function
prediction horizon len
control horizon len
system step
constraints
"""

import numpy as np
from scipy.optimize import minimize


class MPC:
    """Class to implement a MPC controller"""

    def __init__(self, horizon_len, setpoint, init_state):
        self.horizon_len = horizon_len  # length of the horizon, decided by user
        self.setpoints = (
            np.zeros(horizon_len) + setpoint
        )  # the setpoint is 0.5 (center of the firld of view in normalized coordinates)
        self.state = init_state  # position of the person in the field of view. Might be a float like 0.7
        self.control_inputs = np.zeros(
            horizon_len
        )  # the sequence of control inputs to minimize the cost function given the current state

    def calculate_cost_function(self, control_inputs):
        cost = 0
        current_state = self.state
        for i in range(self.horizon_len):
            current_state = self.update_state_model(current_state, control_inputs[i])
            cost += (
                self.setpoints[i] - current_state
            ) ** 2  # error between the state and the setpoint after doing i actions (or inputs)

        return cost / self.horizon_len

    def calculate_control_inputs(self):
        results = minimize(
            self.calculate_cost_function, self.control_inputs
        )  # getting the inputs that minimize the cost function
        return results.x

    def update_state_to_real_state(self, real_state):
        self.state = real_state  # update the state based on real measurement of the position of the point in the field of view

    def update_state_model(self, state, control_input):
        return (
            state + control_input
        )  # update the state based on our model, to predict the behaviour of the system

    def solve_mpc(
        self, real_state
    ):  # function to get the action to perform given the current position of the point in the field of view

        self.update_state_to_real_state(real_state)
        self.control_inputs = self.calculate_control_inputs()
        optimal_input = self.control_inputs[0]
        return optimal_input


# def main():
#    mpc = MPC(20,0.5,0.76)

#    dt = 0.1
#    t = 10
#    L = int(np.round(t/dt))
#    state = 0
#    for l in range(L):
#        inputs = mpc.solve_mpc(state)
#        mpc.state = mpc.update_state_model(mpc.state,inputs)
#        state = mpc.state
#        print(f"Inputs : {inputs}, State : {state}")
