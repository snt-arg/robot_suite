from setuptools import find_packages, setup
import os
from glob import glob

package_name = "object_detection_plugin"

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
    description="Plugin to detect defined classes of objects and publish the bounding boxes on a topic",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "object_detection_node = object_detection_plugin.object_detection_node:main",
            "associator_node = object_detection_plugin.person_object_association:main",
        ],
    },
)
