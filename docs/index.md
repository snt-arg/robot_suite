!!! danger "Important"

    - This project is still a work in progress, so expect some bugs! If you encounter any, please open an issue or submit a PR with a fix.
    - This suite has been ported from the `tello_suite` project, so some names may not have been fully updated to reflect the new `robot_...` naming convention.

Robot Suite is a collection of ROS2 packages designed to enhance the capabilities of robots,
making them smarter and more versatile. The suite utilizes a series of plugins—ROS2 packages with
specialized features—to extend the robot's functionality. While each plugin can operate independently,
the primary goal of the suite is to integrate with the robot_bt package, which enables complex
behaviors by orchestrating the execution of multiple plugins.

A key principle of this project is robot agnosticism. This means that the combination
of these plugin packages is designed to work across any robot platform, including both
ground and aerial robots. As such, there is no robot-specific package, such as a dedicated robot driver.
Instead, we leverage ROS' standard interfaces, using middleware and configuration files to ensure compatibility.
For instance, these configuration files allow plugins to subscribe to the appropriate topics for the robot in use.

The suite also includes a Dockerfile for easy setup, eliminating the need to install dependencies
on your computer and simplifying the process of switching between different robot platforms.
For more information, refer to the Docker page.
