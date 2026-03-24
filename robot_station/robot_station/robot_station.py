import uvicorn
from robot_station.backend.app import app


def main():
    uvicorn.run(app, host="0.0.0.0", port=9000, reload=False)


if __name__ == "__main__":
    main()
