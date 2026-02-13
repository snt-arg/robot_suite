# Plugin Base

The `plugin_base` package serves as a bridge between the `robot_bt` framework and any custom plugins you create. It allows you to develop plugins independently, without requiring direct use of `robot_bt` or the `py-trees` library (which manages the [behavior tree](../Packages/robot_bt.md)).

Essentially, this package provides a ROS 2 node with a pre-configured ROS 2 service, enabling the behavior tree to trigger the execution (or "ticking") of your plugin.

## Getting Started

Using this package is straightforward and requires only two steps:

1. **Inherit from `plugin_base.PluginNode`:** Use this as the base class for your node instead of `rclpy.Node`.
2. **Define the `tick(self)` method:** Implement the `tick()` method in your node class. This method is essential; it will serve as the main loop for your plugin.

!!! danger

    You **must** implement the `tick` function. You can think of it as an infinite while loop. This function should not contain any infinite loop inside!!

!!! example

    ```python
    from plugin_base.plugin_base import PluginNode
    from typing import Optional, Any

    class MyNode(PluginNode):
      def __init__(self, node_name: str):
        super().__init__(node_name)

        # ...

      def tick(self, blackboard: Optional[dict["str", Any]] = None):
        # Implement here the logic
        pass
    ```

## Parameters

The following parameters can be configured in the `plugin_base` package:

| Parameter Name | Default Value | Description                                                                                           |
| -------------- | ------------- | ----------------------------------------------------------------------------------------------------- |
| `tick_rate`    | 30            | When in standalone mode, this parameter sets the rate (in Hz) at which the `tick()` method is called. |
| `standalone`   | false         | If set to `true`, the plugin runs in standalone mode, meaning it operates without the behavior tree.  |

## For developers

We offer a simple plugin tester node, which is targeted for developers to test for example their behavior tree.
The node name is `test_plugin_node` and it can be executed with:

```sh
ros2 run plugin_base test_plugin
```

!!! tip

    In case you want to test your plugin while in development, you can run it in standalone mode.
    In order to use the plugin in standalone mode, you can run the following command:

    ```sh
    ros2 run plugin_server_base test_plugin --ros-args -p standalone:=true -p tick_rate:=30
    ```
