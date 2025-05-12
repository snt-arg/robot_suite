from setuptools import find_packages, setup
import os
from glob import glob

package_name = "robot_bt"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*launch.py")),
        (os.path.join("share", package_name, "config"), glob("config/*")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="snt-arg",
    maintainer_email="snt-arg@github.com",
    description="A behavior tree for the robot suite",
    license="GPL-3.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": ["bt_server = robot_bt.bt_server_node:main"],
    },
)
