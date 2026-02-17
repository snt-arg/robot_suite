# Person Tracking Plugin

This plugin allows the robot to follow a specific person.
It uses deep learning based object detection and tracking to identify objects and follow them throughout video frames.
We now use the information given by the deep learning object tracking model to send appropriate commands that will make the robot follow the target in real life.

---

## Plugin structure

![Structure of the person tracking plugin](../assets/person_tracking_structure.png)

**Object detection**

As the name indicates, this part of the plugin handles real time object detection. Given real time video frames coming form the robot's driver, this nodes performs object detection on the frames, and publishes the list of bounding boxes on a new topic. It also publishes image frames on which the bounding boxes around objects are outlined, for visualization purposes.

**Object following**

This is the part responsible for actually tracking a specific person.

1. The `tracker node` is responsible for selecting the target person to follow, and updating its current position (relative to the robot's camera).
   Based on the list of bounding boxes sent by the `object detection node`, and depending on the target selection mode, the `tracker node` chooses the person that the robot should follow, updates his/her position as she/he moves and sends the latest position to the `object following node` to compute tracking commands.  
   At the moment, there are two selection modes possible:
    - Via hand gestures  
      In this mode, the person to follow is selected via hand gestures. The recognition of gestures relies on the [hand gestures plugin](../Plugins/hand_gestures.md). And there is an additional node, the `sign filter` which purpose is to to send a tracking signal to the `Tracker node` when someone does a specific gesture (requesting for tracking).
    - Via the robot agent  
      It is possible to ask the [robot agent](../Packages/robot_agent.md) to track a specific person (based on an object they hold). In this case, the `robot agent` will use a tool to find a person matching the description of the user. If such a person is found, the `robot_agent` will send a tracking signal to the `Tracker node`, specifying the position of the person to follow.

1. The `Object following node` is responsible for computing appropriate commands that will allow the robot to follow the target in the real world.

**Helper nodes**

1. Sign filter
1. Person object associator
1. Drawing node

---

## ROS2

### ROS2 custom messages

### Object detection node

**Topics and services**

**Parameters**

### Person object association

**Topics and services**

**Parameters**

### Tracker node

**Topics and services**

**Parameters**

### Following node

**Topics and services**

**Parameters**

### Sign filter node

**Topics and services**

**Parameters**

### Drawer node

**Topics and services**

**Parameters**

---

## Launching in standalone mode
