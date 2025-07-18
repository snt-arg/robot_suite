from fastapi import APIRouter
from ..modules.cameraRaw import CameraRaw
import rclpy
import base64

router = APIRouter()
rclpy.init()
camera_node = CameraRaw()


@router.get("/")
def get_latest_image():
    rclpy.spin_once(camera_node, timeout_sec=0.1)
    image_msg = camera_node.get_latest_image()
    if image_msg is None:
        return {"error": "No image received yet."}

    img_bytes = bytes(image_msg.data)
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    return {
        "header": str(image_msg.header),
        "encoding": image_msg.encoding,
        "height": image_msg.height,
        "width": image_msg.width,
        "data": img_b64,
    }
