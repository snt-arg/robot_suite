from fastapi import FastAPI
from .api.rawApi import router as camera_router

app = FastAPI()

app.include_router(camera_router, prefix="/api/camera")


@app.on_event("shutdown")
def shutdown_event():
    from .api.rawApi import camera_node

    camera_node.destroy_node()
    import rclpy

    rclpy.shutdown()
