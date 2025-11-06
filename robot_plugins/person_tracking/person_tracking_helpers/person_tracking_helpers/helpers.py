from person_tracking_msgs.msg import Box, PointMsg, AllBoundingBoxes
from hand_gestures_msgs.msg import Landmarks
import json
import math


def overlapping_area(rect1, rect2, overlapping_method):
    """Function to calculate the overlapping area between two rectangles
    Parameters: rect1 (rectangle given by a Box : Box.top_left.x, Box.top_left.y, Box.bottom_right.x, Box.bottom_right.y)
                rect2 (rectangle given by a Box : Box.top_left.x, Box.top_left.y, Box.bottom_right.x, Box.bottom_right.y)

    """
    if isinstance(rect1, Box) and isinstance(rect2, Box):

        dx = min(rect1.bottom_right.x, rect2.bottom_right.x) - max(
            rect1.top_left.x, rect2.top_left.x
        )
        dy = min(rect1.bottom_right.y, rect2.bottom_right.y) - max(
            rect1.top_left.y, rect2.top_left.y
        )

        area1 = abs(rect1.bottom_right.x - rect1.top_left.x) * abs(
            rect1.bottom_right.y - rect1.top_left.y
        )  # area rectangle 1
        area2 = abs(rect2.bottom_right.x - rect2.top_left.x) * abs(
            rect2.bottom_right.y - rect2.top_left.y
        )  # area rectangle 2

        intersection_area = dx * dy

        if dx < 0 or dy < 0:  # if the rectangles don't overlap
            return -1

        if overlapping_method == "intersection":
            return intersection_area

        elif overlapping_method == "IOU":

            union_area = area1 + area2 - intersection_area

            return intersection_area / union_area

        else:
            raise ValueError(
                "Overlapping method must be either intersection or IOU.\nPlease change configuration to enter a correct overlapping method"
            )
    else:
        raise TypeError("In overlapping area, the rectangles aren't Box objects.")


def assign_objects_to_persons(persons_list, objects_list, overlapping_method):

    possessor_to_objects_dict = dict()

    for object_box in objects_list:

        # list of overlapping areas between the object and each person
        overlapping_area_list = [
            overlapping_area(object_box, person_box, overlapping_method)
            for person_box in persons_list
        ]
        max_overlap = max(overlapping_area_list, default=-1)
        # possessor is the person whose bounding box shares the biggest area with the object's box

        # print(f"\n%%% overlapping list, {object_class} : {overlapping_area_list}\n") #<-- debug

        if (
            max_overlap >= 0
        ):  # the overlapping_area method returns -1 if the rectangles don't overlap. So this condition is to ensure that the object's box overlaps with at least one person, before assigning the object to that person

            possessor_index = overlapping_area_list.index(max_overlap)
            # add mapping in dictionnary
            if possessor_index in possessor_to_objects_dict:
                possessor_to_objects_dict[possessor_index].append(object_box.box_class)
            else:
                possessor_to_objects_dict[possessor_index] = [object_box.box_class]

    return possessor_to_objects_dict


def construct_JSON_string(persons_list, possessor_to_objects_dict):
    """Function to construct a JSON string given the list of persons (persons_list)
    and the dictionnary of possessor index and their objects."""

    # list to contain information for each person.
    # This list will be converted to JSON.
    tojson_list = []

    # For loop to build the list of infos about each person.
    # For each person we save the coordinates of the bounding box, the id assigned by the YOLO model, and the list of objects that the person possesses
    for person_counter in range(len(persons_list)):
        person_box = persons_list[person_counter]

        info_dict = dict()
        info_dict["bottom_right"] = (
            person_box.bottom_right.x,
            person_box.bottom_right.y,
        )
        info_dict["top_left"] = (person_box.top_left.x, person_box.top_left.y)
        info_dict["YOLO_id"] = person_box.box_id
        info_dict["objects"] = possessor_to_objects_dict.get(
            person_counter, []
        )  # ["hat"] if person_counter == 0 else []

        # Additional format needed for communication with LLM package
        person_dict = dict()
        person_dict["action"] = "tracking"
        person_dict["id"] = person_counter
        person_dict["info"] = info_dict

        # append the person to the list to be converted to JSON
        tojson_list.append(person_dict)

    return json.dumps(tojson_list)


def extract_box_msg(box_msg):
    """Given a Box message (defined in person_tracking_msgs),
    this function returns a tuple (top_left_x, top_left_y, bottom_right_x, bottom_right_y)
    This function also works for any object possessing top_left.x, top_left.y, bottom_right.x , bott
    """

    top_left_x = box_msg.top_left.x
    top_left_y = box_msg.top_left.y
    bottom_right_x = box_msg.bottom_right.x
    bottom_right_y = box_msg.bottom_right.y
    box_class = box_msg.box_class
    box_id = box_msg.box_id

    return (top_left_x, top_left_y, bottom_right_x, bottom_right_y, box_class, box_id)


def init_box_msg(
    top_left_x,
    top_left_y,
    bottom_right_x,
    bottom_right_y,
    box_class="person",
    box_id=-1,
):
    """Initializes a box message with the given parameters"""

    box_msg = Box()
    box_msg.top_left.x = top_left_x
    box_msg.top_left.y = top_left_y
    box_msg.bottom_right.x = bottom_right_x
    box_msg.bottom_right.y = bottom_right_y
    box_msg.box_class = box_class
    box_msg.box_id = box_id

    return box_msg


def extract_point_msg(point_msg):
    """Given a Box message (defined in person_tracking_msgs),
    this function returns a tuple (x, y)"""
    if hasattr(point_msg, "x") and hasattr(point_msg, "y"):
        x = point_msg.x
        y = point_msg.y
        return (x, y)
    else:
        raise TypeError("The provided point is not an instance of PointMsg")


def calculate_midpoint_box(box):
    """Function to calculate the midpoint of two points, (x1,y1) and (x2,y2)"""
    top_left_x, top_left_y, bottom_right_x, bottom_right_y, _, _ = extract_box_msg(box)
    midpoint = PointMsg()
    midpoint.x = (top_left_x + bottom_right_x) / 2
    midpoint.y = (top_left_y + bottom_right_y) / 2
    return midpoint


def euclidean_distance_squared(x1, y1, x2, y2):
    """Calculates the eucliedean distance between two points (x1,y1) and (x2,y2)"""
    return (x2 - x1) ** 2 + (y2 - y1) ** 2


def calculate_box_size(box):
    """Calculates the size of a box. The size is the length of the diagonal.
    This function takes a custom Box message"""
    top_left_x, top_left_y, bottom_right_x, bottom_right_y, _, _ = extract_box_msg(box)

    return math.sqrt(
        (top_left_x - bottom_right_x) ** 2 + (top_left_y - bottom_right_y) ** 2
    )


def person_lost(empty_midpoint_count, max_empty_midpoint_before_lost):
    """Function to call when someone is lost.
    Returns true when the person is lost and False else."""
    if empty_midpoint_count >= max_empty_midpoint_before_lost:
        return True
    else:
        return False


def equal_point_msg(p1, p2) -> bool:
    """function to compare to point messages (PointMsg).
    Returns True if they have the same coordinates, and False else"""
    if isinstance(p1, PointMsg) and isinstance(p2, PointMsg):
        return p1.x == p2.x and p1.y == p2.y
    else:
        raise TypeError(
            "Error in function equal_point_msg, tried to compare two objects that are not of type PointMsg"
        )


def equal_box_msg(b1, b2, consider_class=False, consider_id=False) -> bool:
    """function to compare two box messages"""
    if isinstance(b1, Box) and isinstance(b2, Box):
        equal_coordinates = True
        equal_class = True
        equal_id = True

        equal_coordinates = equal_point_msg(
            b1.top_left, b2.top_left
        ) and equal_point_msg(b1.bottom_right, b2.bottom_right)

        if consider_class:
            equal_class = b1.box_class == b2.box_class

        if consider_id:
            equal_id = b1.box_id == b2.box_id

        return equal_coordinates and equal_class and equal_id

    else:
        raise TypeError(
            "Error in function equal_box_msg, tried to compare two objects that are not of type Box"
        )


def convert_landmarks_to_box(left_hand_coordinates, right_hand_coordinates):
    """Function to convert a landmarks message into a box. If the message represents two hands,
    The bounding box will be the box around both hands"""

    all_hand_coordinates = left_hand_coordinates + right_hand_coordinates

    all_x_coordinates = [pt[0] for pt in all_hand_coordinates]
    all_y_coordinates = [pt[1] for pt in all_hand_coordinates]

    smallest_x = min(all_x_coordinates)
    smallest_y = min(all_y_coordinates)
    biggest_x = max(all_x_coordinates)
    biggest_y = max(all_y_coordinates)

    return init_box_msg(smallest_x, smallest_y, biggest_x, biggest_y, "hand")


def convert_Landmarks_to_dict(ldmrks: Landmarks):
    infodict = dict()
    right_hand_dict = dict()
    left_hand_dict = dict()

    right_hand_dict["score"] = ldmrks.right_hand.score
    right_hand_dict["gesture"] = ldmrks.right_hand.gesture
    right_hand_dict["handedness"] = ldmrks.right_hand.handedness
    right_hand_dict["normalized_landmarks"] = [
        (n_ldmrk.x, n_ldmrk.y) for n_ldmrk in ldmrks.right_hand.normalized_landmarks
    ]
    right_hand_dict["world_landmarks"] = [
        (w_ldmrk.x, w_ldmrk.y) for w_ldmrk in ldmrks.right_hand.world_landmarks
    ]

    left_hand_dict["score"] = ldmrks.left_hand.score
    left_hand_dict["gesture"] = ldmrks.left_hand.gesture
    left_hand_dict["handedness"] = ldmrks.left_hand.handedness
    left_hand_dict["normalized_landmarks"] = [
        (n_ldmrk.x, n_ldmrk.y) for n_ldmrk in ldmrks.left_hand.normalized_landmarks
    ]
    left_hand_dict["world_landmarks"] = [
        (w_ldmrk.x, w_ldmrk.y) for w_ldmrk in ldmrks.left_hand.world_landmarks
    ]

    infodict["right_hand"] = right_hand_dict
    infodict["left_hand"] = left_hand_dict

    return infodict


def equal_allBoundingBoxes_msg(msg1: AllBoundingBoxes, msg2: AllBoundingBoxes):
    """Compares two messages of type AllBoundingBoxes. Return True if the two messages are equal, and False else."""
    if isinstance(msg1, AllBoundingBoxes) and isinstance(msg2, AllBoundingBoxes):
        if len(msg1.bounding_boxes) == len(msg2.bounding_boxes):
            for i in range(len(msg1.bounding_boxes)):
                if not equal_box_msg(
                    msg1.bounding_boxes[i], msg2.bounding_boxes[i], True, True
                ):
                    return False
            return True
        else:
            return False
    else:
        raise TypeError(
            "Error in function equal_AllBoundingBoxes_msg, tried to compare two objects that are not of type AllBoundingBoxes",
            "Type of msg1:",
            type(msg1),
            "Type of msg2:",
            type(msg2),
        )
