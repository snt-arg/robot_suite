from setuptools import find_packages, setup
import os
from glob import glob

package_name = "object_following_plugin"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (
            os.path.join("share", package_name, "launch"),
            glob(os.path.join("launch", "*launch.py")),
        ),
        (
            os.path.join("share", package_name, "config"),
            glob("config/*"),
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="maeri",
    maintainer_email="maevachekma@gmail.com",
    description="Package for object following plugin. Responsible for following a person/object and avoiding obstacles.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "collision_avoiding_node = object_following_plugin.collision_avoiding:main",
            "following_commands_node = object_following_plugin.following_commands:main",
            "tracker_node = object_following_plugin.tracker:main",
            "takeoff_node = object_following_plugin.takeoff:main",
            "land_node = object_following_plugin.land:main",
        ],
    },
)
