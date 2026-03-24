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

    def __init__(self, horizon_len, setpoint, init_state, bound):
        self.horizon_len = horizon_len  # length of the horizon, decided by user
        self.setpoints = (
            np.zeros(horizon_len) + setpoint
        )  # the setpoint is 0.5 (center of the field of view in normalized coordinates)
        self.state = init_state  # position of the person in the field of view. Might be a float like 0.7
        self.control_inputs = np.zeros(
            horizon_len
        )  # the sequence of control inputs to minimize the cost function given the current state
        self.bound = bound  # bounds for the control inputs. It should be positive. This is to avoid sending large commands to the drone

    def calculate_cost_function(self, control_inputs):
        cost = 0
        current_state = self.state

        for i in range(self.horizon_len):
            current_state = self.compute_next_state(current_state, control_inputs[i])
            cost += (
                self.setpoints[i] - current_state
            ) ** 2  # error between the state and the setpoint after doing i actions (or inputs)

        return cost / self.horizon_len

    def calculate_control_inputs(self):
        results = minimize(
            self.calculate_cost_function, self.control_inputs
        )  # getting the inputs that minimize the cost function
        return results.x

    def compute_next_state(self, current_state, control_input):
        return current_state + control_input

    def update_state_to_real_state(self, real_state):
        self.state = real_state  # update the state based on real measurement of the position of the point in the field of view

    def update_state_model(self, control_input):

        self.state = (
            self.state + control_input
        )  # update the state based on our model, to predict the behaviour of the system

    def solve_mpc(
        self, real_state
    ):  # function to get the action to perform given the current position of the point in the field of view

        self.update_state_to_real_state(real_state)
        self.control_inputs = self.calculate_control_inputs()
        optimal_input = self.control_inputs[0]

        return optimal_input if abs(optimal_input) <= self.bound else self.bound


# def function_movement_target(t, execution_time_interval):
#     """returns the position of the target in normalized coordinates at time t"""

#     return (
#         t * execution_time_interval,
#         (0.5 + 2.5 * np.sin(0.2 * t + 1)) / 5,
#     )  # Target moves between 0.0 and 0.5 in normalized coordinates


# def function_movement_drone(t, drone_state, state, execution_time_interval):
#     """returns the position of the drone in normalized coordinates at time t"""
#     x, y = state
#     x_drone, y_drone = drone_state
#     return (
#         x_drone + x * execution_time_interval,
#         y_drone + y * execution_time_interval,
#     )  # Drone is always at the center of the field of view in normalized coordinates


# def main():
#     mpc_x = MPC(20, 0., 0.0)
#     mpc_y = MPC(60, 0., 0.0)

#     dt = 0.01
#     t = 10

#     state_target = (0,0)
#     state_drone = (0,0)

#     for dummy in range(int(t/dt)):
#         #target moves
#         state_target = function_movement_target(dummy*dt,dt)

#         # states calculation
#         x_drone, y_drone = state_drone
#         x_target, y_target = state_target
#         state_x = x_drone - x_target
#         state_y = y_drone - y_target

#         print(f"-------------Before drone's movement:---------------\n",
#               f"Drone state : {state_drone}, Target State : {state_target}\n",
#               f"System state x: {state_x}\n",
#               f"System state y: {state_y}\n")

#         # computing correction
#         inputs_x = mpc_x.solve_mpc(state_x)
#         inputs_y = mpc_y.solve_mpc(state_y)

#         # drone moves according to correction
#         state_drone = function_movement_drone(t,state_drone, (inputs_x, inputs_y), dt)


#         # new states calculation
#         x_drone, y_drone = state_drone
#         x_target, y_target = state_target
#         state_x = x_drone - x_target
#         state_y = y_drone - y_target

#         # updating the model with the new state of the system (position of the target in the field of view)
#         mpc_x.update_state_model(state_x)
#         mpc_y.update_state_model(state_y)

#         print(f"********After drone's movement:***********\n",
#               f"Drone state : {state_drone}, Target State : {state_target}\n",
#               f"System state x: {state_x},  inputs x: {inputs_x}\n",
#               f"System state y: {state_y}, inputs y: {inputs_y}\n")

#     print(f"Final states:\n",
#           f"System state x: {state_x}\n",
#           f"System state y: {state_y}\n")

# main()
